#!/bin/sh
# Install git pre-commit hook for this repo
# Run once after clone: ./scripts/setup-hooks.sh

HOOK_FILE=".git/hooks/pre-commit"

cat > "$HOOK_FILE" << 'EOF'
#!/bin/sh
echo "🧪 Running tests..."
python3 -m pytest tests/ -q
if [ $? -ne 0 ]; then
    echo "❌ Tests failed. Commit blocked."
    exit 1
fi
echo "✅ All tests passed."
EOF

chmod +x "$HOOK_FILE"
echo "✅ Pre-commit hook installed."
