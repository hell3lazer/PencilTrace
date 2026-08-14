#!/usr/bin/env bash
# Linux launcher script
echo "Starting PencilTrace Server..."
echo "Please leave this terminal window open while using the application."
echo ""

# Change to the directory where this script is located
cd "$(dirname "$0")"

# Try to use python3 if available, otherwise python
if command -v python3 &>/dev/null; then
    python3 backend/app.py
else
    python backend/app.py
fi
