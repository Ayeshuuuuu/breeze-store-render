#!/bin/bash
# build.sh - Manual build script for Render
echo "Installing Python dependencies directly..."
pip install Flask==3.1.2 Werkzeug==3.1.3 gunicorn==21.2.0
