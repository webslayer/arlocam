import logging
import urllib
from io import BytesIO

import boto3
import requests
from botocore.exceptions import ClientError
from PIL import Image

from .sftp import SFTP


def upload_image_file(url, bucket, file_name, quality=60):
    """
    Function to upload a file to an S3 bucket
    """
    s3 = boto3.client("s3")
    req_for_image = requests.get(url)
    IMAGE_FILE = BytesIO(req_for_image.content)

    im1 = Image.open(IMAGE_FILE)
    # here, we create an empty string buffer
    buffer = BytesIO()
    im1.save(buffer, "JPEG", quality=quality)
    buffer.seek(0)
    print("compressed")

    # Do the actual upload to s3
    response = s3.put_object(Key=file_name, Body=buffer, Bucket=bucket)

    return response


def upload_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    # Upload the file
    s3_client = boto3.client("s3")
    try:
        _ = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True


def delete_file(bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # Upload the file
    s3_client = boto3.client("s3")
    try:
        _ = s3_client.delete_object(Bucket=bucket, Key=object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True


def download_file(file_name, bucket):
    """
    Function to download a given file from an S3 bucket
    """
    s3 = boto3.client("s3")
    output = f"/tmp/{file_name}"
    s3.download_file(bucket, file_name, output)


def create_presigned_url(bucket_name, object_name, expiration=36000):
    """Generate a presigned URL to share an S3 object

    :param bucket_name: string
    :param object_name: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """

    # Generate a presigned URL for the S3 object
    s3_client = boto3.client("s3")
    response = s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket_name, "Key": object_name},
        ExpiresIn=expiration,
    )

    # The response contains the presigned URL
    return response


def transfer_sftp_to_s3():

    with SFTP() as sftp:
        files = sftp.sftp.listdir(path=sftp.remote_snaphot_path)
        for file_name in files:
            url = (
                "https://silverene.info/wp-content/uploads/snapshots/"
                + urllib.parse.quote(file_name)
            )
            try:
                upload_image_file(url, "arlocam-snapshots", file_name, quality=95)
            except:
                print(f"skipped shot: {file_name}")

            print(f"uploaded shot: {file_name}")

    print("transfered all snapshot")
