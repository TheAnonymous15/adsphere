#!/bin/bash

INPUT="legit.jpg"
OUTPUT="modified.jpeg"
MESSAGE="I am malicious"

# copy original file to output
cp "$INPUT" "$OUTPUT"

# append hidden message
echo -n -e "\n##HIDDEN_START##${MESSAGE}##HIDDEN_END##" >> "$OUTPUT"

echo "Hidden message appended to $OUTPUT"
