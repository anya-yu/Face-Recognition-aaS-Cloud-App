import os
import boto3
from lambda_function import video_splitting_cmdline  # Import from lambda_function.py

s3_client = boto3.client('s3')

def handler(event, context):
    """
    Lambda handler function to process video files uploaded to an S3 bucket.
    Splits the video into frames using video_splitting_cmdline and uploads the frames to a stage-1 S3 bucket.
    """
    try:
        # Extract bucket name and object key from the event
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        print(f"Event received for bucket: {bucket}, key: {key}")
        
        # Download the video from S3 to /tmp directory
        local_video_path = f"/tmp/{os.path.basename(key)}"
        print(f"Downloading video from S3: s3://{bucket}/{key} to {local_video_path}")
        s3_client.download_file(bucket, key, local_video_path)
        print(f"Video successfully downloaded to: {local_video_path}")
        
        # Process the video to extract frames
        output_dir = video_splitting_cmdline(local_video_path)
        
        # Ensure the output directory exists and contains frames
        if not os.path.exists(output_dir) or not os.listdir(output_dir):
            print(f"No frames generated in {output_dir}. Skipping upload.")
            return {"statusCode": 500, "body": "No frames generated"}
        
        print(f"Frames generated in directory: {output_dir}")
        
        # Prepare to upload frames back to the stage-1 S3 bucket
        output_bucket = bucket.replace("-input", "-stage-1")
        folder_name = os.path.splitext(os.path.basename(key))[0]
        print(f"Uploading frames to bucket: {output_bucket}, folder: {folder_name}")

        # Upload each frame to the appropriate folder in the output bucket
        for frame in os.listdir(output_dir):
            frame_path = os.path.join(output_dir, frame)
            s3_target_key = f"{folder_name}/{frame}"
            s3_client.upload_file(frame_path, output_bucket, s3_target_key)
            print(f"Uploaded {frame_path} to s3://{output_bucket}/{s3_target_key}")
        
        print("Frame upload process completed successfully.")
        return {"statusCode": 200, "body": "Processing complete"}

    except Exception as e:
        # Log any errors that occur during processing
        print(f"Error processing video: {e}")
        return {"statusCode": 500, "body": f"Error processing video: {e}"}
