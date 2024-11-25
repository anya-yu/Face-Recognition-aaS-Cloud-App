import os
import boto3
import json
from video_splitting_function import video_splitting_cmdline  # Importing the function from lambda_function.py

# Initialize AWS clients
lambda_client = boto3.client('lambda')
s3_client = boto3.client('s3')

def handler(event, context):
    """
    Lambda function to process the video, extract 1 frame, upload it to the stage-1 bucket,
    and invoke face-recognition.
    """
    # Get the bucket and object key from the event (this is passed when the video is uploaded to S3)
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    video_filename = event['Records'][0]['s3']['object']['key']

    print(f"Processing video: {video_filename} from bucket: {bucket_name}")

    # Call the video-splitting function from lambda_function.py to extract 1 frame and upload to stage-1 bucket
    local_frame_path = video_splitting_cmdline(video_filename, bucket_name)

    # After the frame is uploaded, invoke the face-recognition Lambda function
    image_file_name = os.path.basename(local_frame_path)  # Extract the frame name

    # Prepare the payload as a dictionary
    payload = {
        "bucket_name": bucket_name.replace("-input", "-stage-1"),  # stage-1 bucket name
        "image_file_name": image_file_name
    }

    # Convert the payload dictionary to a valid JSON string using json.dumps()
    try:
        payload_json = json.dumps(payload)
        print(f"Payload to invoke Lambda: {payload_json}")  # For debugging purposes, check the payload structure
    except Exception as e:
        print(f"Error converting payload to JSON: {e}")
        raise

    # Now invoke the face-recognition Lambda function asynchronously
    try:
        response = lambda_client.invoke(
            FunctionName="face-recognition",  # Ensure the name matches your face-recognition Lambda
            InvocationType="Event",  # Asynchronous invocation
            Payload=payload_json  # Pass the JSON string as payload
        )
        print(f"Successfully invoked face-recognition Lambda: {response}")
    except Exception as e:
        print(f"Error invoking face-recognition Lambda: {e}")
        raise

    return {"status": "success", "message": "Video processing and face recognition invocation successful."}
