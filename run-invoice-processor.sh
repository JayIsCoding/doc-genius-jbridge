#!/bin/bash
# JBridge Invoice Processor Launcher
cd "$(dirname "$0")"

# Check for virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate and install deps
source venv/bin/activate
pip install -q -r requirements.txt

# Check for API key
if [ -z "$GEMINI_API_KEY" ] && [ ! -f .env ]; then
    echo "Warning: GEMINI_API_KEY not set and no .env file found"
    echo "Create a .env file with: GEMINI_API_KEY=your-key-here"
fi

# Run the app
echo "Starting JBridge Invoice Processor..."
echo "Open http://localhost:8502 in your browser"
streamlit run invoice_processor.py --server.port 8502
