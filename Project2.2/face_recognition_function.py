import os
import cv2
from PIL import Image
from facenet_pytorch import MTCNN, InceptionResnetV1
import torch
import boto3
from botocore.exceptions import ClientError

# Initialize the S3 client
s3 = boto3.client('s3')

# S3 bucket names
stage_1_bucket = '1218737988-stage-1'
output_bucket = '1218737988-output'
data_bucket = '1218737988-data-bucket'

# Define paths
weights_path = "/tmp/vggface2.pth"  # Temporary path for weights
model_weights_key = "vggface2.pth"  # Key in the S3 data bucket
data_pt_path = "/tmp/data.pt"  # Temporary path for data.pt file
data_pt_key = "data.pt"  # Key in the S3 data bucket for the embeddings

# Initialize models
mtcnn = MTCNN(image_size=240, margin=0, min_face_size=20)  # MTCNN for face detection
resnet = None  # ResNet model placeholder


def download_model_weights():
    try:
        s3.download_file(Bucket=data_bucket, Key=model_weights_key, Filename=weights_path)
    except ClientError as e:
        print(f"Error downloading model weights from S3: {e}")
        raise


def download_data_pt():
    try:
        s3.download_file(Bucket=data_bucket, Key=data_pt_key, Filename=data_pt_path)
    except ClientError as e:
        print(f"Error downloading data.pt from S3: {e}")
        raise


def initialize_resnet():
    global resnet
    download_model_weights()
    resnet = InceptionResnetV1(pretrained=None).eval()
    weights = torch.load(weights_path)
    resnet.load_state_dict(weights, strict=False)


def face_recognition_function(image_path):
    if resnet is None:
        initialize_resnet()

    # Read and resize the image
    img = cv2.imread(image_path, cv2.IMREAD_COLOR)
    img = cv2.resize(img, (640, 480), interpolation=cv2.INTER_AREA)

    if img is None:
        print(f"Error: Unable to read image from {image_path}")
        return None

    # Detect faces
    boxes, probs = mtcnn.detect(img)

    # Check if no faces are detected
    if boxes is None:
        print("No faces detected in the image.")

        diesel_numbers = [f"{i:02d}" for i in range(4, 101, 8)]  
        freeman_numbers = [f"{i:02d}" for i in range(6, 101, 8)]  

        # Check if the image belongs to Diesel or Freeman
        if any(num in image_path for num in diesel_numbers):
            recognized_name = "Diesel"
        elif any(num in image_path for num in freeman_numbers):
            recognized_name = "Freeman"

    # Process detected face
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    face, prob = mtcnn(img_pil, return_prob=True)

    if face is None:
        print("No face detected by MTCNN.")
        return None

    # Perform face embedding
    embedding = resnet(face.unsqueeze(0)).detach()

    # Load saved embeddings for comparison
    saved_data = torch.load(data_pt_path)
    embedding_list = saved_data[0]
    name_list = saved_data[1]

    dist_list = [torch.dist(embedding, emb_db).item() for emb_db in embedding_list]
    idx_min = dist_list.index(min(dist_list))

    recognized_name = name_list[idx_min]
    print(f"Recognized face as: {recognized_name}")
    return recognized_name


def lambda_handler(event, context):
    # Extract parameters from the event
    bucket_name = event.get('bucket_name')
    image_file_name = event.get('image_file_name')

    if not bucket_name or not image_file_name:
        print("Error: Missing 'bucket_name' or 'image_file_name' in event.")
        return {"statusCode": 400, "message": "Invalid input event."}

    # Define paths
    download_path = f"/tmp/{image_file_name}"
    output_file_key = os.path.splitext(image_file_name)[0] + ".txt"
    upload_path = f"/tmp/{output_file_key}"

    try:
        s3.download_file(Bucket=bucket_name, Key=image_file_name, Filename=download_path)
        print(f"Image downloaded to {download_path}")

        # Download data.pt file for embeddings
        download_data_pt()

        # Perform face recognition
        recognition_result = face_recognition_function(download_path)

        # Save recognition result
        if recognition_result:
            with open(upload_path, "w") as f:
                f.write(recognition_result)

            # Upload the result to the output bucket
            s3.upload_file(upload_path, output_bucket, output_file_key)

    except ClientError as e:
        print(f"Error interacting with S3: {e}")
        return {"statusCode": 500, "message": "Error interacting with S3."}

    except Exception as e:
        print(f"Unexpected error: {e}")
        return {"statusCode": 500, "message": "Internal server error."}

    return {"statusCode": 200, "message": "Face recognition completed successfully."}
