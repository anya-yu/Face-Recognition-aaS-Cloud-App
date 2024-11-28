#!/bin/bash

# Check if AWS_LAMBDA_RUNTIME_API is set (it is automatically set in AWS Lambda)
if [ -z "$AWS_LAMBDA_RUNTIME_API" ]; then
    # If running locally, use RIE to simulate Lambda runtime
    exec /usr/bin/aws-lambda-rie python3 -m awslambdaric $@
else
    # If running in AWS Lambda, directly invoke the handler
    exec python3 -m awslambdaric $@
fi



# #!/bin/bash

# # Lambda entrypoint script that uses AWS Lambda Runtime Interface Client to invoke the handler

# # Ensure the handler file is in the correct place
# if [ -z "$1" ]; then
#     echo "Error: The handler function name must be specified." >&2
#     exit 1
# fi

# # Run the Lambda function using the provided handler
# exec /usr/bin/python3 -m awslambdaric "$1"
