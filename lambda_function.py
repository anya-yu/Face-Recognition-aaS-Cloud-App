import os
import subprocess

def video_splitting_cmdline(video_filename):
    """
    Extract exactly 10 frames from the input video and save them to /tmp/frames.
    """
    filename = os.path.basename(video_filename)
    output_dir = "/tmp/frames"

    # Clean or create the output directory
    if os.path.exists(output_dir):
        for file in os.listdir(output_dir):
            os.remove(os.path.join(output_dir, file))
    else:
        os.makedirs(output_dir)

    # Construct the ffmpeg command to extract exactly 10 frames
    split_cmd = f'/opt/bin/ffmpeg -ss 0 -i {video_filename} -vf "fps=10" -start_number 0 -vframes 10 {output_dir}/output-%02d.jpg -y'
    print(f"Running ffmpeg command: {split_cmd}")

    try:
        subprocess.check_call(split_cmd, shell=True)
        print(f"Frames saved to {output_dir}")
    except subprocess.CalledProcessError as e:
        print(f"Error during video splitting: {e}")
        raise

    # List the files in the output directory for debugging
    output_files = os.listdir(output_dir)
    print(f"Files in output directory {output_dir}: {output_files}")

    # Ensure exactly 10 frames are present
    if len(output_files) != 10:
        print(f"Warning: Expected 10 frames but found {len(output_files)} frames.")
    return output_dir
