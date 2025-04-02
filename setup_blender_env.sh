#!/bin/bash

BLENDER_ROOT="$(pwd)/blender-4.2.1-linux-x64"
BLENDER_VERSION="4.2"
PYTHON_VERSION="3.11"
BLENDER_PYTHON_DIR="$BLENDER_ROOT/$BLENDER_VERSION/python/lib/python$PYTHON_VERSION"
BLENDER_SITE_PACKAGES="$BLENDER_PYTHON_DIR/site-packages"
VENV_NAME="venv"

if [ ! -d "$BLENDER_ROOT" ]; then
    echo "Error: Blender directory not found at $BLENDER_ROOT"
    exit 1
fi

mkdir -p "$BLENDER_SITE_PACKAGES"

python$PYTHON_VERSION -m venv "$BLENDER_ROOT/$BLENDER_VERSION/python/$VENV_NAME"

source "$BLENDER_ROOT/$BLENDER_VERSION/python/$VENV_NAME/bin/activate"

pip install --upgrade pip

pip install vtk==9.3.0
pip install netCDF4
pip install numpy
pip install scipy
pip install matplotlib

pip install geopandas
pip install pytz
pip install shapely
pip install fiona

pip install Pillow

cp -r "$BLENDER_ROOT/$BLENDER_VERSION/python/$VENV_NAME/lib/python$PYTHON_VERSION/site-packages/"* "$BLENDER_SITE_PACKAGES/"

cat > "$BLENDER_PYTHON_DIR/sitecustomize.py" << EOL
import sys
import os

site_packages = os.path.join(os.path.dirname(__file__), 'site-packages')
if site_packages not in sys.path:
    sys.path.append(site_packages)
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

echo "Setup completed. Dependencies have been installed in $BLENDER_SITE_PACKAGES"
echo "Blender $BLENDER_VERSION is ready to use with installed dependencies"