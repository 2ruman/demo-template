#!/bin/bash

set -e

source ./inst.sh

VENV_DIR=".venv"
APP_FILE="app.py"
REQ_FILE="requirements.txt"

echo "Checking virtual environment..."

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv $VENV_DIR
fi

echo "Activate virtual environment..."
source $VENV_DIR/bin/activate

if [ -f "$REQ_FILE" ]; then
    echo "Installing requirements..."
    pip install -r $REQ_FILE
fi

echo "Running $APP_FILE..."
python3 $APP_FILE

deactivate
