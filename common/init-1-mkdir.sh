#!/usr/bin/env bash

safe_move() {
    if [ -e $1 ]; then
        DEST=$(mktemp -du $1.XXXX)
        echo "Existing lab directory found, moving it to $DEST"
        mv $1 $DEST
    fi
    if [ -e $1 ]; then
        echo "FAILED, aborting."
        exit 1
    fi
}

# Create main lab directory and backup the old one if it exists
safe_move $LABDIR
mkdir -p $LABDIR
