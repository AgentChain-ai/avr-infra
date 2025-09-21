#!/bin/bash

# Akash Institute Outreach System - Streamlit Dashboard Launcher
# Make sure the FastAPI backend is running on localhost:8000 first

echo "🚀 Starting Akash Institute Parent Outreach Dashboard..."
echo "📋 Make sure FastAPI backend is running on http://localhost:8000"
echo ""

# Change to the streamlit app directory
cd "$(dirname "$0")/streamlit_app"

# Run Streamlit
streamlit run main.py --server.port 8501 --server.address localhost
