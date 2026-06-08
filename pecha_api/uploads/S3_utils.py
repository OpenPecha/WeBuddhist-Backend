from http import HTTPMethod
from io import BytesIO

import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile, HTTPException
import logging

from starlette import status

from ..config import get

s3_client = boto3.client(
    "s3",
    aws_access_key_id=get("AWS_ACCESS_KEY"),
    aws_secret_access_key=get("AWS_SECRET_KEY"),
    region_name=get("AWS_REGION")

)


def upload_file(bucket_name: str, s3_key: str, file: UploadFile) -> str:
    try:
        s3_client.upload_fileobj(
            Fileobj=file.file,
            Bucket=bucket_name,
            Key=s3_key,
            ExtraArgs={
                "ContentType": file.content_type,
                "ExpectedBucketOwner": get("AWS_BUCKET_OWNER")
            }
        )
        return s3_key
    except ClientError as e:
        logging.error(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to upload file to S3.")
    except Exception as e:
        logging.error(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An unexpected error occurred.")


def upload_bytes(bucket_name: str, s3_key: str, file: BytesIO, content_type: str) -> str:
    try:
        if not isinstance(file, BytesIO):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="The 'file' parameter must be a BytesIO object")
        s3_client.upload_fileobj(
            Fileobj=file,
            Bucket=bucket_name,
            Key=s3_key,
            ExtraArgs={
                "ContentType": content_type,
                "ExpectedBucketOwner": get("AWS_BUCKET_OWNER")
            }
        )
        return s3_key
    except ClientError as e:
        logging.error(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to upload file to S3.")
    except Exception as e:
        logging.error(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An unexpected error occurred.")


def generate_presigned_access_url(bucket_name: str, s3_key: str):
    if isinstance(s3_key, str) and s3_key.strip():
        # Generate a presigned URL for uploading an object
        presigned_url = s3_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={
                "Bucket": bucket_name,
                "Key": s3_key
            },
            ExpiresIn=3600
        )
        return presigned_url
    return ""


def download_bytes(bucket_name: str, s3_key: str) -> bytes:
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=s3_key, ExpectedBucketOwner=get("AWS_BUCKET_OWNER"))
        return response["Body"].read()
    except ClientError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to download file from S3.")


def delete_file(file_path: str):
    try:
        s3_client.delete_object(
            Bucket=get("AWS_BUCKET_NAME"), 
            Key=file_path,
            ExpectedBucketOwner=get("AWS_BUCKET_OWNER")
        )
        return True
    except ClientError as e:
        if e.response['Error']['Code'] != 'NoSuchKey':
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error deleting old image.")
        return False
