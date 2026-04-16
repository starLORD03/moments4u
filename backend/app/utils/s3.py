"""
S3-compatible storage client — works with AWS S3 and MinIO.

Handles uploads, downloads, signed URLs, and batch deletions.
All S3 interactions go through this wrapper for consistency.
"""

import io
from typing import Optional

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError


class S3Client:
    """Wrapper around boto3 S3 client with convenience methods."""

    def __init__(
        self,
        endpoint_url: Optional[str],
        access_key: str,
        secret_key: str,
        bucket_name: str,
        region: str = "us-east-1",
    ):
        self.bucket_name = bucket_name

        kwargs = {
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "region_name": region,
            "config": Config(signature_version="s3v4"),
        }
        if endpoint_url:
            kwargs["endpoint_url"] = endpoint_url

        self.client = boto3.client("s3", **kwargs)

    async def upload(self, key: str, data: bytes, content_type: str = "image/jpeg") -> str:
        """
        Upload bytes to S3.

        Args:
            key: S3 object key (path within bucket).
            data: Raw bytes to upload.
            content_type: MIME type of the object.

        Returns:
            The S3 key of the uploaded object.
        """
        self.client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=data,
            ContentType=content_type,
            ServerSideEncryption="AES256",
        )
        return key

    def upload_sync(self, key: str, data: bytes, content_type: str = "image/jpeg") -> str:
        """Sync version of upload for Celery workers."""
        self.client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=data,
            ContentType=content_type,
            ServerSideEncryption="AES256",
        )
        return key

    def download(self, key: str) -> bytes:
        """Download an object from S3 and return its bytes."""
        response = self.client.get_object(Bucket=self.bucket_name, Key=key)
        return response["Body"].read()

    async def get_signed_url(self, key: str, expires: int = 3600) -> str:
        """
        Generate a pre-signed URL for temporary access.

        Args:
            key: S3 object key.
            expires: URL lifetime in seconds (default: 1 hour).

        Returns:
            Pre-signed URL string.
        """
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": key},
            ExpiresIn=expires,
        )

    def get_signed_url_sync(self, key: str, expires: int = 3600) -> str:
        """Sync version for Celery workers."""
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": key},
            ExpiresIn=expires,
        )

    def delete(self, key: str) -> None:
        """Delete a single object from S3."""
        self.client.delete_object(Bucket=self.bucket_name, Key=key)

    def delete_batch(self, keys: list[str]) -> dict:
        """
        Delete up to 1000 objects from S3 in a single request.

        Args:
            keys: List of S3 object keys to delete.

        Returns:
            S3 delete response.
        """
        if not keys:
            return {"Deleted": []}

        objects = [{"Key": k} for k in keys[:1000]]
        response = self.client.delete_objects(
            Bucket=self.bucket_name,
            Delete={"Objects": objects, "Quiet": True},
        )
        return response

    def exists(self, key: str) -> bool:
        """Check if an object exists in S3."""
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError:
            return False


def get_s3_client() -> S3Client:
    """Factory function for Celery workers (reads from settings)."""
    from ..config import get_settings

    settings = get_settings()
    return S3Client(
        endpoint_url=settings.s3_endpoint_url,
        access_key=settings.s3_access_key,
        secret_key=settings.s3_secret_key,
        bucket_name=settings.s3_bucket_name,
        region=settings.s3_region,
    )
