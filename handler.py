import os
import subprocess
import boto3
from lambda_function import video_splitting_cmdline  # Import from lambda_function.py

s3_client = boto3.client('s3')

def handler(event, context):
    # Get bucket and object key from event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    # Download the video from S3 to /tmp
    local_video_path = f"/tmp/{os.path.basename(key)}"
    s3_client.download_file(bucket, key, local_video_path)
    
    # Process the video with video_splitting_cmdline from lambda_function.py
    video_splitting_cmdline(local_video_path)  # Call the video splitting function
    
    # Ensure the output directory exists before uploading frames
    output_dir = "/tmp/frames"
    os.makedirs(output_dir, exist_ok=True)  # Create the /tmp/frames directory if it doesn't exist
    print(f"Created or verified output directory: {output_dir}")

    # Upload frames back to S3 (stage-1 bucket)
    output_bucket = bucket.replace("-input", "-stage-1")
    folder_name = os.path.splitext(os.path.basename(key))[0]
    
    # Check if frames are generated and stored in the output directory
    for frame in os.listdir(output_dir):
        frame_path = os.path.join(output_dir, frame)
        s3_client.upload_file(frame_path, output_bucket, f"{folder_name}/{frame}")
        print(f"Uploaded {frame} to {output_bucket}/{folder_name}/")

    print("Processing complete.")
