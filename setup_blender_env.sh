#!/bin/bash

set -e

BLENDER_VERSION="4.2"
BLENDER_SUBVERSION="4.2.1"
PYTHON_VERSION="3.11"
BLENDER_ROOT="$(pwd)/blender-$BLENDER_SUBVERSION-linux-x64"
BLENDER_PYTHON_DIR="$BLENDER_ROOT/$BLENDER_VERSION/python/lib/python$PYTHON_VERSION"
BLENDER_SITE_PACKAGES="$BLENDER_PYTHON_DIR/site-packages"
BLENDER_SCRIPTS_DIR="$BLENDER_ROOT/$BLENDER_VERSION/scripts"
VENV_NAME="venv"
BLENDER_DOWNLOAD_URL="https://download.blender.org/release/Blender$BLENDER_VERSION/blender-$BLENDER_SUBVERSION-linux-x64.tar.xz"

check_venv() {
    if [[ -z "${VIRTUAL_ENV}" ]]; then
        echo "❌ Error: Virtual environment is not active"
        exit 1
    fi
}

echo "---------------------------------------"
echo "[1/4] Checking Blender installation..."
echo "---------------------------------------"
if [ ! -d "$BLENDER_ROOT" ]; then
    echo "⬇️  Downloading Blender $BLENDER_SUBVERSION..."
    wget --show-progress "$BLENDER_DOWNLOAD_URL" -O blender.tar.xz
    tar xf blender.tar.xz
    rm blender.tar.xz
    echo "✅ Blender downloaded and extracted successfully."
else
    echo "✅ Blender already present."
fi

echo "---------------------------------------"
echo "[2/4] Setting up Python environment..."
echo "---------------------------------------"
mkdir -p "$BLENDER_SITE_PACKAGES"

cat > "$BLENDER_ROOT/blender-wrapper.sh" << EOL
#!/bin/bash
SCRIPT_DIR="\$(dirname "\${BASH_SOURCE[0]}")"
BLENDER_DIR="\$(cd "\$SCRIPT_DIR" && pwd)"

unset BLENDER_USER_SCRIPTS
unset BLENDER_SYSTEM_SCRIPTS
unset BLENDER_USER_CONFIG
unset BLENDER_SYSTEM_PYTHON

export BLENDER_USER_SCRIPTS="\$BLENDER_DIR/$BLENDER_VERSION/scripts"
export BLENDER_SYSTEM_SCRIPTS="\$BLENDER_DIR/$BLENDER_VERSION/scripts"
export BLENDER_SYSTEM_PYTHON="\$BLENDER_DIR/$BLENDER_VERSION/python"
export BLENDER_USER_CONFIG="\$BLENDER_DIR/config"
export PYTHONPATH="\$BLENDER_DIR/$BLENDER_VERSION/scripts/addons:\$PYTHONPATH"

exec "\$BLENDER_DIR/blender" "\$@"
EOL

chmod +x "$BLENDER_ROOT/blender-wrapper.sh"
ln -sf "$BLENDER_ROOT/blender-wrapper.sh" "$BLENDER_ROOT/blender-local"

python$PYTHON_VERSION -m venv "$BLENDER_ROOT/$BLENDER_VERSION/python/$VENV_NAME"

if ! source "$BLENDER_ROOT/$BLENDER_VERSION/python/$VENV_NAME/bin/activate"; then
    echo "❌ Error: Failed to activate virtual environment"
    exit 1
fi

check_venv

echo "✅ Python environment ready."

echo "---------------------------------------"
echo "[3/4] Installing Python dependencies..."
echo "---------------------------------------"
echo "(This may take a few minutes)"
echo "⬇️  Upgrading pip..."
pip install --upgrade pip

echo "⬇️  Installing vtk==9.3.0..."
pip install vtk==9.3.0

echo "⬇️  Installing netCDF4..."
pip install netCDF4

echo "⬇️  Installing numpy..."
pip install numpy

echo "⬇️  Installing scipy..."
pip install scipy

echo "⬇️  Installing matplotlib..."
pip install matplotlib

echo "⬇️  Installing geopandas..."
pip install geopandas

echo "⬇️  Installing pytz..."
pip install pytz

echo "⬇️  Installing shapely..."
pip install shapely

echo "⬇️  Installing fiona..."
pip install fiona

echo "⬇️  Installing Pillow..."
pip install Pillow

echo "✅ Python dependencies installed."

echo "---------------------------------------"
echo "[4/4] Copying dependencies to Blender..."
echo "---------------------------------------"
cp -r "$BLENDER_ROOT/$BLENDER_VERSION/python/$VENV_NAME/lib/python$PYTHON_VERSION/site-packages/"* "$BLENDER_SITE_PACKAGES/"

cat > "$BLENDER_PYTHON_DIR/sitecustomize.py" << EOL
import sys
import os

site_packages = os.path.join(os.path.dirname(__file__), 'site-packages')
scripts_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "$BLENDER_VERSION", "scripts"))
addons_path = os.path.join(scripts_path, "addons")

for path in [site_packages, scripts_path, addons_path]:
    if path not in sys.path and os.path.exists(path):
        sys.path.append(path)
EOL

VTK_FILE="$BLENDER_SITE_PACKAGES/vtk.py"
if [ -f "$VTK_FILE" ]; then
    sed -i 's/from vtkmodules.vtkRenderingMatplotlib import \*/# from vtkmodules.vtkRenderingMatplotlib import */g' "$VTK_FILE"
fi

VTK_ALL_FILE="$BLENDER_SITE_PACKAGES/vtkmodules/all.py"
if [ -f "$VTK_ALL_FILE" ]; then
    sed -i 's/from vtkmodules.vtkRenderingMatplotlib import \*/# from vtkmodules.vtkRenderingMatplotlib import */g' "$VTK_ALL_FILE"
fi

deactivate
rm -rf "$BLENDER_ROOT/$BLENDER_VERSION/python/$VENV_NAME"

echo "✅ Blender environment setup completed."
echo "To use Blender with local scripts, use: $BLENDER_ROOT/blender-local"
echo "Blender $BLENDER_VERSION is ready to use with installed dependencies"