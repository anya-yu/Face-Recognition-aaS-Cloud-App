import os
import boto3
import cv2
import torch
from facenet_pytorch import MTCNN, InceptionResnetV1
from PIL import Image

# Initialize AWS clients
s3_client = boto3.client('s3')

# Initialize MTCNN for face detection and InceptionResnetV1 for face recognition
mtcnn = MTCNN(image_size=240, margin=0, min_face_size=20)
resnet = InceptionResnetV1(pretrained='vggface2').eval()

def lambda_handler(event, context):
    """
    Lambda function for face recognition. It processes the image, computes embeddings,
    compares with stored embeddings, and saves the recognition result.
    """
    bucket_name = event['bucket_name']
    image_file_name = event['image_file_name']

    # Download the image from the S3 bucket
    local_image_path = f"/tmp/{os.path.basename(image_file_name)}"
    s3_client.download_file(bucket_name, image_file_name, local_image_path)

    # Call the face-recognition function
    recognized_name = face_recognition_function(local_image_path)

    # Upload the result to the output S3 bucket
    output_bucket = f"{bucket_name}-output"
    if recognized_name:
        result_file_name = image_file_name.replace(".jpg", ".txt")
        s3_client.put_object(
            Bucket=output_bucket,
            Key=result_file_name,
            Body=recognized_name
        )
        print(f"Recognition result saved as {result_file_name}")
    else:
        print(f"No face detected in {image_file_name}")

    return {
        'statusCode': 200,
        'body': json.dumps(f"Processed {image_file_name} and saved result.")
    }

def face_recognition_function(key_path):
    """
    This function processes the image, detects faces, computes embeddings, and saves the recognition result.
    """
    # Face extraction
    img = cv2.imread(key_path, cv2.IMREAD_COLOR)
    boxes, _ = mtcnn.detect(img)

    # Check if a face is detected
    if boxes is None:
        print(f"No face detected in the image {key_path}")
        return None

    # Face recognition logic
    img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    face, prob = mtcnn(img, return_prob=True)

    if face is not None:
        # Load the embeddings database
        saved_data = torch.load('/tmp/data.pt')  # This will load the data from the `data.pt` file stored in /tmp
        embedding_list = saved_data[0]  # List of stored embeddings
        name_list = saved_data[1]  # Corresponding names list

        # Get the embedding for the detected face
        emb = resnet(face.unsqueeze(0)).detach()

        # Compare the embedding with stored embeddings
        dist_list = [torch.dist(emb, emb_db).item() for emb_db in embedding_list]
        min_dist_idx = dist_list.index(min(dist_list))

        # Save the recognized name in a text file
        recognized_name = name_list[min_dist_idx]
        return recognized_name
    else:
        print(f"No face is detected in the image {key_path}")
    return None
