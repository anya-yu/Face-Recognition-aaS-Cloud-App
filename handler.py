import boto3
import os
import subprocess

s3_client = boto3.client('s3')

def handler(event, context):
    # Extract bucket and object key from event
    input_bucket = event['Records'][0]['s3']['bucket']['name']
    input_key = event['Records'][0]['s3']['object']['key']
    
    output_bucket = "<ASU ID>-stage-1"
    video_name = os.path.splitext(input_key)[0]
    
    # Download video from S3
    input_path = f'/tmp/{input_key}'
    s3_client.download_file(input_bucket, input_key, input_path)
    
    # Create output directory
    output_dir = f'/tmp/{video_name}'
    os.makedirs(output_dir, exist_ok=True)
    
    # Split video into frames using FFmpeg
    command = f'ffmpeg -i {input_path} -vf fps=1/10 {output_dir}/output-%02d.jpg'
    subprocess.run(command, shell=True)
    
    # Upload frames to S3
    for frame in os.listdir(output_dir):
        frame_path = os.path.join(output_dir, frame)
        s3_client.upload_file(frame_path, output_bucket, f'{video_name}/{frame}')
    
    return {
        'statusCode': 200,
        'body': 'Video processed and frames uploaded'
    }
