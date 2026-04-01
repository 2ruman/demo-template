#!/bin/bash

set -e

inst_pkg() {
    local pkg="$1"
    if ! dpkg -l | grep -q "^ii  $pkg"; then
        echo "$pkg is not installed. Starting installation..."
        sudo apt install -y $pkg
    else
        echo "$pkg is already installed."
    fi
}

inst_pkg python3-tk
inst_pkg python3-venv

