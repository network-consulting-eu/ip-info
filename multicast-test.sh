#!/bin/bash

# Multicast Test Script for Linux
# Tests multicast reception by joining a specified multicast group

# Default values
DEFAULT_MCAST_GROUP="239.192.11.1"
DEFAULT_MCAST_PORT="1234"
DEFAULT_TTL="16"
DEFAULT_INTERFACE=""
DEFAULT_DURATION="30"

# Function to check if a value is a valid IP address
is_valid_ip() {
    local ip=$1
    local stat=1

    if [[ $ip =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
        OIFS=$IFS
        IFS='.'
        ip=($ip)
        IFS=$OIFS
        [[ ${ip[0]} -le 255 && ${ip[1]} -le 255 && ${ip[2]} -le 255 && ${ip[3]} -le 255 ]]
        stat=$?
    fi
    return $stat
}

# Function to check if an IP is in the multicast range
is_multicast_ip() {
    local ip=$1
    local first_octet

    if is_valid_ip "$ip"; then
        first_octet=$(echo "$ip" | cut -d. -f1)
        if [ "$first_octet" -ge 224 ] && [ "$first_octet" -le 239 ]; then
            return 0  # True
        fi
    fi
    return 1  # False
}

# Function to validate port number
is_valid_port() {
    local port=$1
    if [[ "$port" =~ ^[0-9]+$ ]] && [ "$port" -ge 1 ] && [ "$port" -le 65535 ]; then
        return 0  # True
    fi
    return 1  # False
}

# Function to validate TTL
is_valid_ttl() {
    local ttl=$1
    if [[ "$ttl" =~ ^[0-9]+$ ]] && [ "$ttl" -ge 15 ] && [ "$ttl" -le 255 ]; then
        return 0  # True
    fi
    return 1  # False
}

# Function to get user input with validation and default value
get_validated_input() {
    local prompt=$1
    local default=$2
    local validation_func=$3
    local value=""
    local valid=false

    while [ "$valid" = false ]; do
        read -p "$prompt [$default]: " value
        value=${value:-$default}  # Use default if empty

        if $validation_func "$value"; then
            valid=true
        else
            echo "Invalid input. Please try again."
        fi
    done

    echo "$value"
}

# Welcome message
echo "========================================"
echo "    Multicast Reception Test Script     "
echo "========================================"
echo "This script will test multicast reception"
echo "by joining a specified multicast group."
echo

# Check for required tools
if ! command -v nc &> /dev/null; then
    echo "Error: netcat (nc) is required but not installed."
    echo "Please install it using: sudo apt install netcat"
    exit 1
fi

if ! command -v timeout &> /dev/null; then
    echo "Error: timeout command is required but not installed."
    echo "Please install it using: sudo apt install coreutils"
    exit 1
fi

# Get user input for configuration
echo "Please enter the following configuration details."
echo "(Press Enter to use default values)"
echo

# Get multicast group
MCAST_GROUP=$(get_validated_input "Multicast Group" "$DEFAULT_MCAST_GROUP" is_multicast_ip)

# Get multicast port
MCAST_PORT=$(get_validated_input "Multicast Port" "$DEFAULT_MCAST_PORT" is_valid_port)

# Get TTL
TTL=$(get_validated_input "TTL (must be ≥ 15)" "$DEFAULT_TTL" is_valid_ttl)

# Get network interface (no validation needed)
echo "Available network interfaces:"
ip -o link show | grep -v "lo:" | awk -F': ' '{print "  " $2}'
read -p "Network Interface (press Enter to use default): " INTERFACE
INTERFACE=${INTERFACE:-$DEFAULT_INTERFACE}

# Get test duration
read -p "Test duration in seconds [$DEFAULT_DURATION]: " DURATION
DURATION=${DURATION:-$DEFAULT_DURATION}
if ! [[ "$DURATION" =~ ^[0-9]+$ ]] || [ "$DURATION" -lt 5 ]; then
    echo "Invalid duration. Using default: $DEFAULT_DURATION seconds"
    DURATION=$DEFAULT_DURATION
fi

# Display test configuration
echo
echo "========================================"
echo "Test Configuration:"
echo "  Multicast Group: $MCAST_GROUP"
echo "  Multicast Port:  $MCAST_PORT"
echo "  TTL:             $TTL"
echo "  Interface:       ${INTERFACE:-<default>}"
echo "  Duration:        $DURATION seconds"
echo "========================================"
echo

# Ask for confirmation
read -p "Start test with these settings? (y/n): " CONFIRM
if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo "Test cancelled by user."
    exit 0
fi

# Create a unique temp file
TEMPFILE=$(mktemp)
trap 'rm -f $TEMPFILE' EXIT

# Function to handle SIGINT
trap_sigint() {
    echo
    echo "Test interrupted by user."
    kill "$LISTENER_PID" 2>/dev/null
    exit 1
}
trap trap_sigint SIGINT

echo
echo "Starting multicast reception test..."
echo "Joining multicast group $MCAST_GROUP on port $MCAST_PORT"
echo "Listening for $DURATION seconds..."
echo "Press Ctrl+C to stop the test early."
echo

# Start the multicast listener
if [ -n "$INTERFACE" ]; then
    # Using specific interface
    nc -u -l -p "$MCAST_PORT" -w "$DURATION" > "$TEMPFILE" &
    LISTENER_PID=$!
    
    # Join multicast group
    ip maddr add "$MCAST_GROUP" dev "$INTERFACE"
else
    # Using default interface
    nc -u -l -p "$MCAST_PORT" -w "$DURATION" > "$TEMPFILE" &
    LISTENER_PID=$!
fi

# Display a progress bar
ELAPSED=0
while [ $ELAPSED -lt "$DURATION" ] && kill -0 $LISTENER_PID 2>/dev/null; do
    PERCENT=$((ELAPSED * 100 / DURATION))
    BAR_SIZE=$((PERCENT / 2))
    BAR=""
    for ((i=0; i<BAR_SIZE; i++)); do
        BAR="${BAR}#"
    done
    for ((i=BAR_SIZE; i<50; i++)); do
        BAR="${BAR}-"
    done
    
    echo -ne "\rProgress: [$BAR] $PERCENT% ($ELAPSED/$DURATION seconds)"
    
    sleep 1
    ELAPSED=$((ELAPSED + 1))
    
    # Check if any data has been received
    if [ -s "$TEMPFILE" ]; then
        PACKET_COUNT=$(wc -c < "$TEMPFILE")
        echo -ne " - Received approximately $(($PACKET_COUNT / 100)) packets"
    fi
done

echo
echo

# Check if the listener is still running (should have timed out)
kill $LISTENER_PID 2>/dev/null

# Check the results
if [ -s "$TEMPFILE" ]; then
    PACKET_SIZE=$(wc -c < "$TEMPFILE")
    PACKETS_RECEIVED=$(($PACKET_SIZE / 100))  # Rough estimate
    echo "Test completed successfully!"
    echo "Results:"
    echo "  Duration: $ELAPSED seconds"
    echo "  Data received: $PACKET_SIZE bytes"
    echo "  Estimated packets: $PACKETS_RECEIVED"
    echo "  Rate: $(($PACKETS_RECEIVED / $ELAPSED)) packets/second (approximate)"
else
    echo "Test completed, but no multicast packets were received."
    echo "Possible issues:"
    echo "  - No multicast traffic on $MCAST_GROUP:$MCAST_PORT"
    echo "  - Multicast routing not properly configured"
    echo "  - Firewall blocking multicast traffic"
    echo "  - Wrong network interface selected"
fi

# Clean up if using specific interface
if [ -n "$INTERFACE" ]; then
    ip maddr del "$MCAST_GROUP" dev "$INTERFACE" 2>/dev/null
fi

echo
echo "Test completed."