#!/bin/bash

echo ""
echo "Starting ContextForLLM..."
echo ""

if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed."
    echo "Run bash install.sh first."
    exit 1
fi

python3 app.py &
sleep 2
open http://127.0.0.1:5000