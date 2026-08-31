#!/bin/bash
ENCRYPTED_FILENAME="update.gfb"
FILENAME="update.tar.gz"
TARGET_DIR="/home/pi/Documents/OTDR_Project/uploads"		# using "~" here causes wipeout of home/pi directory
ENCRYPTED_FILE="${TARGET_DIR}/${ENCRYPTED_FILENAME}"
ARCHIVE_FILE="${TARGET_DIR}/${FILENAME}"

# Create destination directory if it does not exist
mkdir -p "$TARGET_DIR"

# Check if the file exists before decrypting
if [ -f "$ENCRYPTED_FILE" ]; then
    echo "Decrypting $ENCRYPTED_FILE to $TARGET_DIR..."
    gpg --batch --decrypt $ENCRYPTED_FILE > $ARCHIVE_FILE
    
    # Check if the tar command succeeded
    if [ $? -eq 0 ]; then
        echo "Decrytion completed successfully!"
    else
        echo "Error: Decrytpion failed." >&2
        exit 1
    fi
else
    echo "Error: File $ENCRYPTED_FILE not found." >&2
    exit 1
fi


# Check if the file exists before untarring
if [ -f "$ARCHIVE_FILE" ]; then
    echo "Extracting $ARCHIVE_FILE to $TARGET_DIR..."
    tar -xf "$ARCHIVE_FILE" -C "$TARGET_DIR"
    
    # Check if the tar command succeeded
    if [ $? -eq 0 ]; then
        echo "Extraction completed successfully!"
    else
        echo "Error: Extraction failed." >&2
        exit 1
    fi
else
    echo "Error: File $ARCHIVE_FILE not found." >&2
    exit 1
fi