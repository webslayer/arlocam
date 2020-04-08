import logging
import boto3
from io import StringIO, BytesIO
from PIL import Image
import requests
from urllib.request import urlopen


def upload_file(url, bucket, file_name):
    """
    Function to upload a file to an S3 bucket
    """
    s3 = boto3.client('s3')
    req_for_image = requests.get(url)
    # file_object_from_req = req_for_image.raw
    IMAGE_FILE = BytesIO(req_for_image.content)

    im1 = Image.open(IMAGE_FILE)
    # here, we create an empty string buffer
    buffer = BytesIO()
    im1.save(buffer, "JPEG", quality=75)
    buffer.seek(0)
    print("compressed")

    # Do the actual upload to s3
    response = s3.put_object(Key=file_name, Body=buffer, Bucket=bucket)

    return response


def download_file(file_name, bucket):
    """
    Function to download a given file from an S3 bucket
    """
    s3 = boto3.client('s3')
    output = f"downloads/{file_name}"
    s3.download_file(bucket, file_name, output)


def create_presigned_url(bucket_name, object_name, expiration=3600):
    """Generate a presigned URL to share an S3 object

    :param bucket_name: string
    :param object_name: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """

    # Generate a presigned URL for the S3 object
    s3_client = boto3.client('s3')
    response = s3_client.generate_presigned_url('get_object',
                                                Params={
                                                    'Bucket': bucket_name,
                                                    'Key': object_name
                                                },
                                                ExpiresIn=expiration)

    # The response contains the presigned URL
    return response