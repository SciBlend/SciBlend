#!/bin/bash
set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
EXTENSION_ID="sciblend"
DIST_DIR="dist"
LOG_FILE="$DIST_DIR/build.log"
LOCK_FILE="/tmp/.${EXTENSION_ID}-build.lock"

if [ "$(uname)" = "Darwin" ]; then
    BLENDER_CONFIG_BASE="$HOME/Library/Application Support/Blender"
else
    BLENDER_CONFIG_BASE="${XDG_CONFIG_HOME:-$HOME/.config}/blender"
fi

# Overrides the auto-detection below.
BLENDER_VERSION="${BLENDER_TARGET_VERSION:-}"

cd "$(dirname "${BASH_SOURCE[0]}")"

# ---------------------------------------------------------------------------
# Parse flags
# ---------------------------------------------------------------------------
SKIP_INSTALL=false
VERBOSE=false
for arg in "$@"; do
    case "$arg" in
        --no-install) SKIP_INSTALL=true ;;
        --verbose)    VERBOSE=true ;;
        -h|--help)
            echo "Usage: $0 [--no-install] [--verbose]"
            echo "  --no-install  Build the zips but do not install into Blender"
            echo "  --verbose     Pass --verbose to the Blender packer"
            echo "Environment:"
            echo "  BLENDER_BIN             Path to the Blender binary"
            echo "  BLENDER_TARGET_VERSION  Config folder to install into, e.g. 5.2"
            exit 0 ;;
        *) echo "Unknown flag: $arg (try --help)"; exit 1 ;;
    esac
done

exec 9>"$LOCK_FILE"
if ! flock -n 9; then
    echo "Another $EXTENSION_ID build already holds $LOCK_FILE."
    echo "Wait for it to finish, or stop it before starting a new one."
    exit 1
fi

echo "=== SciBlend Extension Build ==="
echo ""

# ---------------------------------------------------------------------------
echo "[1/5] Checking the source tree..."
for required in blender_manifest.toml SciBlend __init__.py; do
    if [ ! -e "$required" ]; then
        echo "  $required not found; run this from the repository root"; exit 1
    fi
done

EXTENSION_VERSION=$(grep -oP '^version\s*=\s*"\K[^"]+' blender_manifest.toml)
echo "  Version: $EXTENSION_VERSION"

# Platform tags in the manifest use dashes, the produced zips use underscores.
# Match the quoted platform tags only. A bare [^"]+ also matches the comma
# sitting between two quoted entries, which yields phantom platforms.
mapfile -t MANIFEST_PLATFORMS < <(
    sed -n '/^platforms\s*=\s*\[/,/\]/p' blender_manifest.toml | grep -oP '"\K[a-z]+-[a-z0-9]+(?=")'
)
if [ "${#MANIFEST_PLATFORMS[@]}" -eq 0 ]; then
    echo "  No platforms declared in blender_manifest.toml"; exit 1
fi
echo "  Platforms: ${MANIFEST_PLATFORMS[*]}"

MISSING_WHEELS=false
while IFS= read -r wheel; do
    [ -f "wheels/$wheel" ] || { echo "  WARNING: manifest references missing wheel: $wheel"; MISSING_WHEELS=true; }
done < <(grep -oP '\./wheels/\K[^"]+\.whl' blender_manifest.toml)
if [ "$MISSING_WHEELS" = true ]; then
    echo "  Fetch the missing wheels before building."; exit 1
fi

# ---------------------------------------------------------------------------
echo "[2/5] Preparing $DIST_DIR/..."
mkdir -p "$DIST_DIR"

rm -f "$DIST_DIR"/."$EXTENSION_ID"-*.zip "$DIST_DIR/$EXTENSION_ID"-*.zip


WHEELS_KB=$(du -sk wheels 2>/dev/null | cut -f1 || echo 0)
NEEDED_KB=$(( WHEELS_KB + 512 * 1024 ))
AVAIL_KB=$(df -Pk "$DIST_DIR" | awk 'NR==2 {print $4}')
echo "  Free space: $(( AVAIL_KB / 1024 )) MB (want at least $(( NEEDED_KB / 1024 )) MB)"
if [ "$AVAIL_KB" -lt "$NEEDED_KB" ]; then
    echo "  Not enough free disk space to build all platforms."; exit 1
fi

# ---------------------------------------------------------------------------
echo "[3/5] Resolving Blender binary..."
if [ -n "${BLENDER_BIN:-}" ]; then
    if [[ "$BLENDER_BIN" != /* ]]; then
        BLENDER_CMD="$(cd "$(dirname "$BLENDER_BIN")" && pwd)/$(basename "$BLENDER_BIN")"
    else
        BLENDER_CMD="$BLENDER_BIN"
    fi
    if [ ! -f "$BLENDER_CMD" ]; then
        echo "  BLENDER_BIN not found: $BLENDER_CMD"
        if command -v blender &> /dev/null; then
            BLENDER_CMD="blender"
        else
            echo "  Blender not found"; exit 1
        fi
    fi
    echo "  Using: $BLENDER_CMD"
elif command -v blender &> /dev/null; then
    BLENDER_CMD="blender"
    echo "  Using: blender (from PATH)"
else
    echo "  Blender not found. Set BLENDER_BIN or add blender to PATH."
    exit 1
fi

# ---------------------------------------------------------------------------
echo "[4/5] Building extension..."
echo "  Log: $LOG_FILE"
echo "  Packing ~$(( WHEELS_KB / 1024 )) MB of wheels across ${#MANIFEST_PLATFORMS[@]} platforms."

BUILD_ARGS=(--command extension build --source-dir . --output-dir "./$DIST_DIR" --split-platforms)
if [ "$VERBOSE" = true ]; then
    BUILD_ARGS+=(--verbose)
fi

set +e
env -u LD_LIBRARY_PATH -u LD_PRELOAD "$BLENDER_CMD" "${BUILD_ARGS[@]}" > "$LOG_FILE" 2>&1
BUILD_STATUS=$?
set -e

if [ "$BUILD_STATUS" -ne 0 ]; then
    echo ""
    echo "  Build failed (exit $BUILD_STATUS). Last lines of $LOG_FILE:"
    tail -30 "$LOG_FILE" | sed 's/^/    /'
    exit "$BUILD_STATUS"
fi


BUILD_OK=true
for platform in "${MANIFEST_PLATFORMS[@]}"; do
    suffix="${platform//-/_}"
    zip_path="$DIST_DIR/${EXTENSION_ID}-${EXTENSION_VERSION}-${suffix}.zip"
    if [ ! -f "$zip_path" ]; then
        echo "  MISSING: $zip_path"
        BUILD_OK=false
    elif ! unzip -l "$zip_path" > /dev/null 2>&1; then
        echo "  CORRUPT: $zip_path (unreadable zip directory)"
        BUILD_OK=false
    fi
done
if [ "$BUILD_OK" != true ]; then
    echo ""
    echo "  The packer exited cleanly but did not produce every artifact."
    echo "  Last lines of $LOG_FILE:"
    tail -30 "$LOG_FILE" | sed 's/^/    /'
    exit 1
fi

echo ""
echo "  Built artifacts:"
ls -lh "$DIST_DIR"/"$EXTENSION_ID"-*.zip | sed 's/^/    /'

# ---------------------------------------------------------------------------
# Auto-install
# ---------------------------------------------------------------------------
if [ "$SKIP_INSTALL" = true ]; then
    echo ""
    echo "  Skipping install (--no-install)."
    echo "=== Done ==="
    exit 0
fi

echo ""
echo "[5/5] Installing locally..."

if [ -z "$BLENDER_VERSION" ]; then
    BLENDER_VERSION=$(env -u LD_LIBRARY_PATH -u LD_PRELOAD "$BLENDER_CMD" \
        --factory-startup --version 2>/dev/null \
        | grep -oP 'Blender \K[0-9]+\.[0-9]+' | head -1 || true)
fi
if [ -z "$BLENDER_VERSION" ]; then
    BLENDER_VERSION=$(grep -oP 'blender_version_min\s*=\s*"\K[0-9]+\.[0-9]+' blender_manifest.toml || true)
fi
if [ -z "$BLENDER_VERSION" ]; then
    echo "  Could not detect the Blender version."
    echo "  Set BLENDER_TARGET_VERSION=X.Y to install manually."
    echo "=== Done (build only) ==="
    exit 0
fi

PLATFORM="$(uname -s)-$(uname -m)"
case "$PLATFORM" in
    Linux-x86_64) ZIP_SUFFIX="linux_x64" ;;
    Darwin-arm64) ZIP_SUFFIX="macos_arm64" ;;
    *)            echo "  No build for this platform ($PLATFORM); skipping install."
                  echo "=== Done (build only) ==="
                  exit 0 ;;
esac

ZIP_FILE="$DIST_DIR/${EXTENSION_ID}-${EXTENSION_VERSION}-${ZIP_SUFFIX}.zip"
INSTALL_DIR="$BLENDER_CONFIG_BASE/$BLENDER_VERSION/extensions/user_default/$EXTENSION_ID"
echo "  Blender version: $BLENDER_VERSION"
echo "  Install target:  $INSTALL_DIR"

if [ -d "$INSTALL_DIR" ]; then
    echo "  Removing old installation..."
    rm -rf "$INSTALL_DIR"
fi

mkdir -p "$INSTALL_DIR"
unzip -q -o "$ZIP_FILE" -d "$INSTALL_DIR"

echo "  Installed successfully"
echo ""
echo "=== Done! Open Blender $BLENDER_VERSION and enable SciBlend. ==="
