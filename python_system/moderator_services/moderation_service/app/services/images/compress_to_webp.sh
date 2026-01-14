#!/bin/bash
# compress_to_webp.sh
# Recursively convert all images to WebP, compress to ≤1MB.

# Check required commands
for cmd in cwebp find stat; do
    command -v $cmd >/dev/null 2>&1 || { echo "$cmd not found. Install it first."; exit 1; }
done

compress_to_webp() {
    local img="$1"
    local base="${img%.*}"
    local tmp_webp="${base}.webp"

    # Get original file size in bytes
    local filesize
    filesize=$(stat -c%s "$img" 2>/dev/null || stat -f%z "$img")

    # Skip small images (<1MB)
    if [ "$filesize" -le $((1024*1024)) ]; then
        echo "Skipping small image: $img ($(($filesize/1024)) KB)"
        return
    fi

    echo "Processing $img ... (original: $(($filesize/1024)) KB)"

    # Start with high quality
    local q=90
    local max_bytes=$((1024*1024)) # 1MB in bytes

    # Iteratively reduce quality until size <= 1MB
    while true; do
        cwebp -q "$q" "$img" -o "$tmp_webp" >/dev/null 2>&1
        local outsize
        outsize=$(stat -c%s "$tmp_webp" 2>/dev/null || stat -f%z "$tmp_webp")

        if [ "$outsize" -le "$max_bytes" ] || [ "$q" -le 10 ]; then
            break
        fi

        # Reduce quality gradually
        q=$((q - 5))
    done

    echo "Saved WebP: $tmp_webp ($(($outsize/1024)) KB, quality=$q)"

    # Optionally: remove original if you want
    # rm -f "$img"
}

export -f compress_to_webp

# Find all images recursively and convert to WebP
find . -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" \) -exec bash -c 'compress_to_webp "$0"' {} \;

echo "All images processed!"

