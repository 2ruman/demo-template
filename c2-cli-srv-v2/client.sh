#!/bin/bash

SERVER_URL="http://localhost:8080/upload"
ASSETS_DIR="assets"

if [ ! -d "$ASSETS_DIR" ]; then
    echo "Error: '$ASSETS_DIR' directory not found."
    echo "Create it and place image files inside."
    exit 1
fi

shopt -s nullglob
images=("$ASSETS_DIR"/*.jpg "$ASSETS_DIR"/*.jpeg "$ASSETS_DIR"/*.png \
        "$ASSETS_DIR"/*.gif "$ASSETS_DIR"/*.webp "$ASSETS_DIR"/*.bmp)

if [ ${#images[@]} -eq 0 ]; then
    echo "No image files found in '$ASSETS_DIR'."
    exit 1
fi

echo "Sending ${#images[@]} image(s) to $SERVER_URL"
echo "---"

for img in "${images[@]}"; do
    ext="${img##*.}"
    case "${ext,,}" in
        jpg|jpeg) ct="image/jpeg" ;;
        png)      ct="image/png"  ;;
        gif)      ct="image/gif"  ;;
        webp)     ct="image/webp" ;;
        bmp)      ct="image/bmp"  ;;
        *)        ct="image/jpeg" ;;
    esac

    echo -n "Sending: $img ... "
    response=$(curl -s -w "%{http_code}" -o /dev/null \
        -X POST "$SERVER_URL" \
        -H "Content-Type: $ct" \
        --data-binary "@$img")

    if [ "$response" = "200" ]; then
        echo "OK"
    else
        echo "FAILED (HTTP $response)"
    fi
done

echo "---"
echo "Done."
