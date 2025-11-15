#!/bin/bash
# Docker entrypoint script to create user entry for non-root execution
# This fixes Node.js os.userInfo() errors when running as arbitrary UID/GID

set -e

# Get UID and GID from environment
USER_ID=${USER_ID:-1000}
GROUP_ID=${GROUP_ID:-1000}
USER_NAME="agent"
USER_HOME=${HOME:-/home/$USER_NAME}

# Create group if it doesn't exist
if ! getent group $GROUP_ID > /dev/null 2>&1; then
    groupadd -g $GROUP_ID $USER_NAME 2>/dev/null || true
fi

# Create user if it doesn't exist
if ! getent passwd $USER_ID > /dev/null 2>&1; then
    useradd -u $USER_ID -g $GROUP_ID -d $USER_HOME -s /bin/bash -m $USER_NAME 2>/dev/null || true
fi

# Ensure .gemini and .npm-global have correct ownership
if [ -d "$USER_HOME/.gemini" ]; then
    chown -R $USER_ID:$GROUP_ID "$USER_HOME/.gemini" 2>/dev/null || true
fi

# Switch to the user and execute command
exec gosu $USER_ID:$GROUP_ID "$@"
