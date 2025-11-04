#!/usr/bin/env bash

# Find a tool binary from either the $PATH environment variable, or another
# environment variable named after the tool (ie, $VIVADO or $YOSYS).
# Usage: find_tool <tool_name>
# The environment variable is the uppercased tool name, with any hyphens converted to underscores.
# Prints the command to use, or exits with an error.
find_tool() {
    local tool="$1"
    local env_var
    env_var=$(echo "$tool" | tr '[:lower:]' '[:upper:]')
    env_var="${env_var//-/_}"
    local on_path=false
    local env_set=false

    if command -v "$tool" &> /dev/null; then
        on_path=true
    fi

    if [[ -n "${!env_var+x}" ]]; then
        env_set=true
    fi

    if $on_path && $env_set; then
        echo "Error: Both \$$env_var is set and '$tool' is on PATH. Please use only one." >&2
        exit 1
    elif $on_path; then
        echo "$tool"
    elif $env_set; then
        echo "${!env_var}"
    else
        echo "Error: $tool not found. Either set \$$env_var environment variable or add '$tool' to PATH." >&2
        exit 1
    fi
}
