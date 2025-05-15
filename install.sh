#!/bin/bash

# ==============================
# 🚀 Starting SciBlend Installer
# ==============================

echo "==============================="
echo "🚀 Starting SciBlend Installer"
echo "==============================="

echo "[1/3] Setting up Blender environment..."
chmod +x setup_blender_env.sh
chmod +x install_addons.sh

./setup_blender_env.sh

echo "[2/3] Installing Blender addons..."
./install_addons.sh > /dev/null 2>&1

echo "[3/3] Creating Blender launcher..."
cat > blender-sciblend << 'EOL'
#!/bin/bash
DIR="$(dirname "$(readlink -f "$0")")"
"$DIR/blender-4.2.1-linux-x64/blender-local" "$@"
EOL

chmod +x blender-sciblend

echo "\n================    ====================="
echo "✅ All steps completed successfully!"
echo "You can run Blender with SciBlend using: ./blender-sciblend"
echo "====================================="