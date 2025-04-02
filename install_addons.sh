#!/bin/bash

BLENDER_ROOT="$(pwd)/blender-4.2.1-linux-x64"
BLENDER_EXECUTABLE="$BLENDER_ROOT/blender"
TEMP_DIR="$(pwd)/temp_zips"
ADDONS_DIR="$(pwd)/addons"

if [ ! -d "$ADDONS_DIR" ]; then
    echo "Error: Addons directory not found at $ADDONS_DIR"
    exit 1
fi

mkdir -p "$TEMP_DIR"

echo "Copying addon zips..."
cp "$ADDONS_DIR/SciBlend_AdvancedCore.zip" "$TEMP_DIR/"
cp "$ADDONS_DIR/Compositor.zip" "$TEMP_DIR/"
cp "$ADDONS_DIR/SciBlend_Core.zip" "$TEMP_DIR/"
cp "$ADDONS_DIR/GridGenerator.zip" "$TEMP_DIR/"
cp "$ADDONS_DIR/LegendGenerator.zip" "$TEMP_DIR/"
cp "$ADDONS_DIR/NotesGenerator.zip" "$TEMP_DIR/"
cp "$ADDONS_DIR/ShaderGenerator.zip" "$TEMP_DIR/"
cp "$ADDONS_DIR/ShapesGenerator.zip" "$TEMP_DIR/"

cat > "$TEMP_DIR/install_addons.py" << 'EOL'
import bpy
import os
import sys

def install_addon(filepath):
    try:
        bpy.ops.preferences.addon_install(filepath=filepath)
        addon_name = os.path.splitext(os.path.basename(filepath))[0]
        
        possible_names = [
            addon_name.lower(),
            addon_name.lower().replace('_', ''),
            addon_name.lower().replace(' ', '_'),
            'sciblend_' + addon_name.lower().replace(' ', '_').replace('_core', ''),
            'sciblend_' + addon_name.lower().replace(' ', '_'),
        ]
        
        for name in possible_names:
            try:
                bpy.ops.preferences.addon_enable(module=name)
                print(f"Addon installed and enabled: {name}")
                break
            except:
                continue
                
    except Exception as e:
        print(f"Error installing {filepath}: {str(e)}")

def main():
    temp_dir = sys.argv[-1]
    
    for filename in os.listdir(temp_dir):
        if filename.endswith('.zip'):
            filepath = os.path.join(temp_dir, filename)
            print(f"Installing {filename}...")
            install_addon(filepath)
    
    bpy.ops.wm.save_userpref()

if __name__ == "__main__":
    main()
EOL

echo "Installing addons in Blender..."
"$BLENDER_EXECUTABLE" -b -P "$TEMP_DIR/install_addons.py" -- "$TEMP_DIR"

echo "Cleaning up temporary files..."
rm -rf "$TEMP_DIR"
echo "Addon installation completed."