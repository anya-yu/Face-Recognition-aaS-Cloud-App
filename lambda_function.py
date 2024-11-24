import os
import subprocess
import boto3

s3_client = boto3.client('s3')

def video_splitting_cmdline(video_filename):
    filename = os.path.basename(video_filename)   
    output_dir = "/tmp/frames"
    os.makedirs(output_dir, exist_ok=True)  # Ensure the output directory exists

    # Get video duration using ffprobe
    ffprobe_cmd = f'/opt/bin/ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {video_filename}'
    duration = subprocess.check_output(ffprobe_cmd, shell=True).decode('utf-8').strip()
    print(f"Video duration: {duration} seconds")

    # Check if the video is long enough for 10 frames every 10 seconds
    if float(duration) < 10:
        print("Video is too short for 10 frames every 10 seconds. Extracting as many frames as possible.")
        fps = 1 / float(duration)  # Use the fps as per the video's duration to extract all frames available
    else:
        fps = 1 / 10  # Extract 1 frame every 10 seconds if the video is long enough

    # Construct the ffmpeg command to extract frames
    split_cmd = f'/opt/bin/ffmpeg -ss 0 -i {video_filename} -vf "fps={fps}" -start_number 0 {output_dir}/output-%02d.jpg -y'
    print(f"Running ffmpeg command: {split_cmd}")
    try:
        subprocess.check_call(split_cmd, shell=True)
        print(f"Frames saved to {output_dir}")  # Debugging: print after frames are saved
    except subprocess.CalledProcessError as e:
        print(f"Error during video splitting: {e}")
        raise

    # List the files in the output directory to ensure frames are being saved
    print(f"Files in output directory {output_dir}: {os.listdir(output_dir)}")

    return output_dir
