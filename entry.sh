#!/bin/bash

# Lambda entrypoint script that uses AWS Lambda Runtime Interface Client to invoke the handler

# Ensure the handler file is in the correct place
if [ -z "$1" ]; then
    echo "Error: The handler function name must be specified." >&2
    exit 1
fi

# Run the Lambda function using the provided handler
exec /usr/bin/python3 -m awslambdaric "$1"
