#!/bin/bash
set -e
echo "Installing dependencies..."
pip install -r requirements.txt
echo "Starting ARK API..."
uvicorn command_hub.main:app --reload &
sleep 3
echo "Starting ARK GUI..."
streamlit run ark_gui/forge.py
