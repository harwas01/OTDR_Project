#!/bin/bash

UPLOAD_DIR="/home/pi/Documents/OTDR_Project/uploads"		
BACKUP_DIR="/home/pi/Documents/OTDR_Project/backup"	
LIVE_DIR="/home/pi/Documents/OTDR_Project"

# Create backup directory if it does not exist
mkdir -p "$BACKUP_DIR"

echo "mkdir"

cp "$LIVE_DIR"/app.py "$BACKUP_DIR"
cp "$LIVE_DIR"/OTDRService.py "$BACKUP_DIR"
cp "$LIVE_DIR"/ErrorCode.py "$BACKUP_DIR"
cp "$LIVE_DIR"/LogReport.py "$BACKUP_DIR"
cp -r "$LIVE_DIR/templates"  "$BACKUP_DIR/templates" 
cp -r "$LIVE_DIR/firmwareUpdate"  "$BACKUP_DIR/firmwareUpdate" 

echo "updated backup directory"

cp "$UPLOAD_DIR"/app.py "$LIVE_DIR"
cp "$UPLOAD_DIR"/OTDRService.py "$LIVE_DIR"
cp "$UPLOAD_DIR"/ErrorCode.py "$LIVE_DIR"
cp "$UPLOAD_DIR"/LogReport.py "$LIVE_DIR"
cp -r "$UPLOAD_DIR/templates"  "$LIVE_DIR/templates" 
cp -r "$UPLOAD_DIR/firmwareUpdate"  "$LIVE_DIR/firmwareUpdate"

echo "updated live directory"
