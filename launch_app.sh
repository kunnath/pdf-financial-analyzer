#!/bin/bash

# PDF Financial Analyzer - Streamlit Web Interface
# This script launches the Streamlit web application

echo "🚀 Starting PDF Financial Analyzer..."
echo "📍 Opening web interface at http://localhost:8501"
echo "💡 Upload a PDF and ask business questions!"
echo ""
echo "Press Ctrl+C to stop the application"
echo "----------------------------------------"

# Activate virtual environment and run Streamlit
source .venv/bin/activate
streamlit run pdf_analyzer_app.py --server.port 8501 --server.address localhost
