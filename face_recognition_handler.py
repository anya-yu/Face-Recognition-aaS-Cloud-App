import os
import boto3
from lambda_function import face_recognition_function  # Import the processing logic

s3_client = boto3.client('s3')

def handler(event, context):
    try:
        # Extract invocation parameters
        bucket_name = event['bucket_name']
        image_file_name = event['image_file_name']
        print(f"Processing image: {image_file_name} from bucket: {bucket_name}")

        # Download the image from S3
        local_image_path = f"/tmp/{image_file_name}"
        s3_client.download_file(bucket_name, image_file_name, local_image_path)
        print(f"Downloaded image to: {local_image_path}")

        # Process the image
        recognized_name = face_recognition_function(local_image_path)

        # Write the result to a .txt file
        output_bucket = bucket_name.replace("-stage-1", "-output")
        output_file_name = image_file_name.replace(".jpg", ".txt")
        local_output_path = f"/tmp/{output_file_name}"

        with open(local_output_path, "w") as f:
            f.write(recognized_name)

        # Upload the result to the output bucket
        s3_client.upload_file(local_output_path, output_bucket, output_file_name)
        print(f"Uploaded result to s3://{output_bucket}/{output_file_name}")

        return {"statusCode": 200, "body": "Face recognition completed successfully"}

    except Exception as e:
        print(f"Error during face recognition: {e}")
        return {"statusCode": 500, "body": f"Error during face recognition: {e}"}
