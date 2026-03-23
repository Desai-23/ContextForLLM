#!/bin/bash

echo ""
echo "Installing ContextForLLM..."
echo ""

if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed."
    echo "Download it from https://www.python.org/downloads/"
    exit 1
fi

echo "Python found: $(python3 --version)"
echo ""

echo "Installing dependencies..."
pip3 install -r requirements.txt --quiet

echo ""
echo "Done. Run this to start the app:"
echo ""
echo "    bash run.sh"
echo ""