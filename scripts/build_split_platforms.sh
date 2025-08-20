#!/usr/bin/env bash
set -euo pipefail


ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR_DEFAULT="${ROOT_DIR}_builds_clean"
OUT_DIR="${1:-$OUT_DIR_DEFAULT}"

PLATFORMS=(
  "windows-x64"
  "linux-x64"
  "macos-x64"
  "macos-arm64"
)

MANIFEST="${ROOT_DIR}/blender_manifest.toml"
if [[ ! -f "${MANIFEST}" ]]; then
  echo "ERROR: blender_manifest.toml not found at ${MANIFEST}" >&2
  exit 1
fi
EXT_ID=$(sed -n 's/^id[[:space:]]*=[[:space:]]*"\([^"]\+\)"/\1/p' "${MANIFEST}" | head -n1)
VERSION=$(sed -n 's/^version[[:space:]]*=[[:space:]]*"\([^"]\+\)"/\1/p' "${MANIFEST}" | head -n1)
EXT_ID=${EXT_ID:-sciblend}
VERSION=${VERSION:-0.0.0}

mkdir -p "${OUT_DIR}"

echo "Building ${EXT_ID} ${VERSION} → ${OUT_DIR}"

rewrite_manifest_wheels() {
  local src="$1" plat="$2" tmp
  tmp="${src}.tmp"
  awk -v plat="${plat}" '
    BEGIN{inw=0}
    /^wheels\s*=\s*\[/ {print $0; inw=1; next}
    inw==1 && /^\]/ {print "]"; inw=0; next}
    inw==1 {
      if ($0 ~ "\\./wheels/common/") {print; next}
      if ($0 ~ ("\\./wheels/" plat "/")) {print; next}
      next
    }
    {print}
  ' "${src}" > "${tmp}" && mv "${tmp}" "${src}"
}

rewrite_manifest_platforms() {
  local src="$1" plat="$2" tmp
  tmp="${src}.tmp"
  awk -v plat="${plat}" '
    BEGIN{done=0}
    {
      if (done==0 && $0 ~ /^platforms\s*=\s*\[/) {
        print "platforms = [\"" plat "\"]"; done=1; next
      }
      print
    }
  ' "${src}" > "${tmp}" && mv "${tmp}" "${src}"
}

for PLAT in "${PLATFORMS[@]}"; do
  echo "-- Platform: ${PLAT}"
  STAGE_DIR="$(mktemp -d)"
  mkdir -p "${STAGE_DIR}/SciBlend" "${STAGE_DIR}/wheels/common" "${STAGE_DIR}/wheels/${PLAT}"

  cp "${ROOT_DIR}/blender_manifest.toml" "${STAGE_DIR}/blender_manifest.toml"
  cp "${ROOT_DIR}/README.md" "${STAGE_DIR}/README.md" || true
  cp "${ROOT_DIR}/__init__.py" "${STAGE_DIR}/__init__.py"
  rsync -a "${ROOT_DIR}/SciBlend/" "${STAGE_DIR}/SciBlend/"

  if [[ -d "${ROOT_DIR}/wheels/common" ]]; then
    rsync -a --ignore-existing "${ROOT_DIR}/wheels/common/" "${STAGE_DIR}/wheels/common/"
  fi
  if [[ -d "${ROOT_DIR}/wheels/${PLAT}" ]]; then
    rsync -a --ignore-existing "${ROOT_DIR}/wheels/${PLAT}/" "${STAGE_DIR}/wheels/${PLAT}/"
  else
    echo "WARNING: No wheels found for ${PLAT} in ${ROOT_DIR}/wheels/${PLAT}" >&2
  fi

  rm -f "${STAGE_DIR}/wheels/${PLAT}/"numpy-*.whl || true

  find "${STAGE_DIR}/wheels/${PLAT}" -maxdepth 1 -type f -name '*-none-any.whl' -exec bash -c '
    stagedir="$1"; shift
    for f in "$@"; do
      base=$(basename "$f")
      if [[ ! -f "$stagedir/wheels/common/$base" ]]; then
        mv "$f" "$stagedir/wheels/common/"
      else
        rm -f "$f"
      fi
    done
  ' bash "${STAGE_DIR}" {} +

  rewrite_manifest_platforms "${STAGE_DIR}/blender_manifest.toml" "${PLAT}"
  rewrite_manifest_wheels "${STAGE_DIR}/blender_manifest.toml" "${PLAT}"

  OUT_FILE="${OUT_DIR}/${EXT_ID}-${VERSION}-${PLAT}.zip"
  blender --command extension build --verbose --source-dir "${STAGE_DIR}" --output-filepath "${OUT_FILE}"

  rm -rf "${STAGE_DIR}"
  echo "Created: ${OUT_FILE}"
  echo
done

echo "All builds completed in: ${OUT_DIR}" 