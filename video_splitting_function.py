import os
import subprocess
import boto3
import json  # Ensure you're importing the json module to handle JSON formatting

# Initialize AWS clients
lambda_client = boto3.client('lambda')
s3_client = boto3.client('s3')

def video_splitting_cmdline(video_filename, bucket_name):
    """
    Extract exactly 1 frame from the input video, upload it to the stage-1 S3 bucket, 
    and invoke face-recognition Lambda.
    """
    # Get the base name of the video file (without extension)
    filename = os.path.basename(video_filename)
    folder_name = os.path.splitext(filename)[0]

    # Define the local paths for video and frame
    local_video_path = f"/tmp/{filename}"
    local_frame_path = "/tmp/frame.jpg"  # Path to store the extracted frame temporarily

    # Download the video from S3 to the local /tmp directory
    s3_client.download_file(bucket_name, video_filename, local_video_path)

    # Construct the ffmpeg command to extract only 1 frame from the video
    split_cmd = f'/opt/bin/ffmpeg -ss 0 -i {local_video_path} -vf "fps=1" -vframes 1 {local_frame_path} -y'
    print(f"Running ffmpeg command: {split_cmd}")

    try:
        subprocess.check_call(split_cmd, shell=True)
        print(f"Frame extracted and saved to {local_frame_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error during video splitting: {e}")
        raise

    # Define the stage-1 bucket name (replace '-input' with '-stage-1')
    stage_1_bucket_name = bucket_name.replace("-input", "-stage-1")

    # Upload the frame to the stage-1 S3 bucket directly (without a folder)
    frame_key = f"{folder_name}.jpg"  # Use the video name as the frame name
    s3_client.upload_file(local_frame_path, stage_1_bucket_name, frame_key)
    print(f"Frame uploaded to S3 bucket {stage_1_bucket_name} with key {frame_key}")

    # Now invoke the face-recognition Lambda function
    # Prepare the payload for the face-recognition function
    payload = {
        "bucket_name": stage_1_bucket_name,  # Use the stage-1 bucket name
        "image_file_name": frame_key  # We pass the image key here
    }

    # Convert the payload dictionary to a valid JSON string using json.dumps()
    try:
        payload_json = json.dumps(payload)
        print(f"Payload to invoke Lambda: {payload_json}")  # For debugging purposes, check the payload structure
    except Exception as e:
        print(f"Error converting payload to JSON: {e}")
        raise

    # Invoke the face-recognition Lambda function asynchronously
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

    return local_frame_path  # Return the path of the frame (for logging or debugging purposes)
