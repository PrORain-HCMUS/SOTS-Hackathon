"""
DigitalOcean Spaces (S3-compatible) client for object storage.
"""

import os
from pathlib import Path
from typing import Optional, BinaryIO, Union
import logging

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class SpacesClient:
    """Client for DigitalOcean Spaces (S3-compatible storage)."""

    def __init__(self):
        settings = get_settings()
        self.bucket = settings.do_spaces_bucket
        self.region = settings.do_spaces_region
        self.endpoint = settings.do_spaces_endpoint

        self._client = boto3.client(
            "s3",
            region_name=self.region,
            endpoint_url=self.endpoint,
            aws_access_key_id=settings.do_spaces_key,
            aws_secret_access_key=settings.do_spaces_secret,
            config=Config(
                signature_version="s3v4",
                retries={"max_attempts": 3, "mode": "standard"},
            ),
        )

    def upload_file(
        self,
        local_path: Union[str, Path],
        s3_key: str,
        content_type: Optional[str] = None,
        public: bool = False,
    ) -> dict:
        """
        Upload a local file to Spaces.
        
        Returns:
            dict with etag, size_bytes, s3_key, s3_bucket
        """
        local_path = Path(local_path)
        if not local_path.exists():
            raise FileNotFoundError(f"File not found: {local_path}")

        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type
        if public:
            extra_args["ACL"] = "public-read"

        file_size = local_path.stat().st_size

        logger.info(f"Uploading {local_path} to s3://{self.bucket}/{s3_key}")
        response = self._client.upload_file(
            str(local_path),
            self.bucket,
            s3_key,
            ExtraArgs=extra_args if extra_args else None,
        )

        # Get ETag from head_object
        head = self._client.head_object(Bucket=self.bucket, Key=s3_key)
        etag = head.get("ETag", "").strip('"')

        return {
            "s3_bucket": self.bucket,
            "s3_key": s3_key,
            "etag": etag,
            "size_bytes": file_size,
        }

    def upload_fileobj(
        self,
        file_obj: BinaryIO,
        s3_key: str,
        content_type: Optional[str] = None,
        public: bool = False,
    ) -> dict:
        """Upload a file-like object to Spaces."""
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type
        if public:
            extra_args["ACL"] = "public-read"

        logger.info(f"Uploading fileobj to s3://{self.bucket}/{s3_key}")
        self._client.upload_fileobj(
            file_obj,
            self.bucket,
            s3_key,
            ExtraArgs=extra_args if extra_args else None,
        )

        head = self._client.head_object(Bucket=self.bucket, Key=s3_key)
        etag = head.get("ETag", "").strip('"')
        size_bytes = head.get("ContentLength", 0)

        return {
            "s3_bucket": self.bucket,
            "s3_key": s3_key,
            "etag": etag,
            "size_bytes": size_bytes,
        }

    def download_file(
        self,
        s3_key: str,
        local_path: Union[str, Path],
    ) -> Path:
        """Download a file from Spaces to local path."""
        local_path = Path(local_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Downloading s3://{self.bucket}/{s3_key} to {local_path}")
        self._client.download_file(self.bucket, s3_key, str(local_path))

        return local_path

    def download_fileobj(self, s3_key: str, file_obj: BinaryIO) -> None:
        """Download a file from Spaces to a file-like object."""
        self._client.download_fileobj(self.bucket, s3_key, file_obj)

    def get_object_bytes(self, s3_key: str) -> bytes:
        """Get object content as bytes."""
        response = self._client.get_object(Bucket=self.bucket, Key=s3_key)
        return response["Body"].read()

    def exists(self, s3_key: str) -> bool:
        """Check if an object exists in Spaces."""
        try:
            self._client.head_object(Bucket=self.bucket, Key=s3_key)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise

    def delete(self, s3_key: str) -> bool:
        """Delete an object from Spaces."""
        try:
            self._client.delete_object(Bucket=self.bucket, Key=s3_key)
            return True
        except ClientError:
            return False

    def list_objects(
        self,
        prefix: str = "",
        max_keys: int = 1000,
    ) -> list[dict]:
        """List objects with given prefix."""
        response = self._client.list_objects_v2(
            Bucket=self.bucket,
            Prefix=prefix,
            MaxKeys=max_keys,
        )
        return response.get("Contents", [])

    def get_public_url(self, s3_key: str) -> str:
        """Get public URL for an object (assumes public-read ACL)."""
        settings = get_settings()
        return f"{settings.spaces_public_url}/{s3_key}"

    def generate_presigned_url(
        self,
        s3_key: str,
        expires_in: int = 3600,
    ) -> str:
        """Generate a presigned URL for temporary access."""
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": s3_key},
            ExpiresIn=expires_in,
        )


_spaces_client: Optional[SpacesClient] = None


def get_spaces_client() -> SpacesClient:
    """Get singleton Spaces client instance."""
    global _spaces_client
    if _spaces_client is None:
        _spaces_client = SpacesClient()
    return _spaces_client
