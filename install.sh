#!/bin/bash

# Define paths
INSTALL_DIR="$HOME/.local/share/cmd-center"
BIN_PATH="$HOME/.local/bin/cmd-center"
CONF_DIR="$HOME/.config/cmd-center"

echo "🚀 Installing CMD-Center..."

# Create Directories
mkdir -p "$INSTALL_DIR/modules"
mkdir -p "$CONF_DIR"
mkdir -p "$HOME/.local/bin"

# Copy Files
cp main.py "$INSTALL_DIR/cmd-center.py"
cp modules/*.py "$INSTALL_DIR/modules/"
touch "$INSTALL_DIR/modules/__init__.py"

# Create Symlink
chmod +x "$INSTALL_DIR/cmd-center.py"
ln -sf "$INSTALL_DIR/cmd-center.py" "$BIN_PATH"

# Initialize Config
if [ ! -f "$CONF_DIR/config.json" ]; then
    echo '{"settings": {"location": "center", "width": 30, "height": 12, "prompt_icon": "⚡"}, "menu": {"Sample Category": {"My App": "echo hello"}}}' > "$CONF_DIR/config.json"
fi

echo "✅ Installed! Type 'cmd-center' to launch."