#!/bin/bash

# Get public IP
PUBLIC_IP=$(curl -s https://ifconfig.me)

# Create temporary file
TEMP_FILE=$(mktemp)

# Add public IP to file
echo "Public|$PUBLIC_IP" > $TEMP_FILE

# Add local IPs to file
ip -4 addr show | grep -v '127.0.0.1' | grep inet | 
  awk '{print "Local (" $NF ")|" $2}' >> $TEMP_FILE

# Display in zenity
cat $TEMP_FILE | zenity --list --title="Your IP Addresses" \
  --column="Type" --column="IP Address" \
  --width=450 --height=300

# Clean up
rm $TEMP_FILE