#!/bin/bash

chmod +x setup_blender_env.sh
chmod +x install_addons.sh

./setup_blender_env.sh
./install_addons.sh

cat > blender-sciblend << EOL
#!/bin/bash
DIR="\$(dirname "\$(readlink -f "\$0")")"
"\$DIR/blender-4.2.1-linux-x64/blender" "\$@"
EOL

chmod +x blender-sciblend

echo "Installation completed. You can run Blender with SciBlend using the command './blender-sciblend'"