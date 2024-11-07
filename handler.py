import boto3
import os
import subprocess
import math

s3_client = boto3.client('s3')

def handler(event, context):
    # Extract bucket and object key from event
    input_bucket = event['Records'][0]['s3']['bucket']['name']
    input_key = event['Records'][0]['s3']['object']['key']
    
    output_bucket = "<ASU ID>-stage-1"  # Replace <ASU ID> with your actual ASU ID
    video_name = os.path.splitext(input_key)[0]
    
    # Download video from S3
    input_path = f'/tmp/{input_key}'
    s3_client.download_file(input_bucket, input_key, input_path)
    
    # Create output directory
    output_dir = f'/tmp/{video_name}'
    os.makedirs(output_dir, exist_ok=True)

    # Ensure exactly 10 frames are extracted
    # You may need to adjust the interval based on the video's FPS
    command = f'ffmpeg -i {input_path} -vf "select=not(mod(n\,{math.floor(get_frame_interval(input_path))}))" -vsync vfr -frame_pts true {output_dir}/output-%03d.jpg'
    subprocess.run(command, shell=True)
    
    # Upload frames to S3
    for frame in os.listdir(output_dir):
        frame_path = os.path.join(output_dir, frame)
        s3_client.upload_file(frame_path, output_bucket, f'{video_name}/{frame}')
    
    return {
        'statusCode': 200,
        'body': 'Video processed and frames uploaded'
    }

# Function to calculate frame interval for exactly 10 frames based on video length
def get_frame_interval(video_path):
    # First, get the total number of frames in the video (duration * fps)
    ffprobe_command = f'ffprobe -v error -select_streams v:0 -show_entries stream=duration,avg_frame_rate -of default=noprint_wrappers=1 {video_path}'
    result = subprocess.check_output(ffprobe_command, shell=True).decode('utf-8').splitlines()

    # Parse output to get duration and fps
    duration = float([line.split('=')[1] for line in result if line.startswith('duration')][0])
    fps = float([line.split('=')[1] for line in result if line.startswith('avg_frame_rate')][0].split('/')[0])

    total_frames = int(fps * duration)
    interval = total_frames / 10  # We want exactly 10 frames

    return interval
