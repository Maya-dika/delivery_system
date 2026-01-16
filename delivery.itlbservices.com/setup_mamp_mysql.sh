#!/bin/bash

# Helper script to add MAMP MySQL to PATH for this session

export PATH="/Applications/MAMP/Library/bin:$PATH"

echo "✓ MAMP MySQL added to PATH"
echo "You can now use: mysql -u root -proot"
echo ""
echo "To make this permanent, add this to your ~/.zshrc:"
echo "export PATH=\"/Applications/MAMP/Library/bin:\$PATH\""




