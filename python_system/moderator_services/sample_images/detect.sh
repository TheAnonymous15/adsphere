#!/bin/bash

FILE="modified.jpeg"

# extract data after JPEG EOF marker FF D9 (optional improvement)
# naive scan for markers we inserted
HIDDEN=$(grep -ao "##HIDDEN_START##.*##HIDDEN_END##" "$FILE")

if [[ -n "$HIDDEN" ]]; then
    echo "Hidden message detected:"
    echo "$HIDDEN"
else
    echo "No hidden message found."
fi

