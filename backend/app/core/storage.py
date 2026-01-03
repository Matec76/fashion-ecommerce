import os
import uuid
import asyncio
from typing import Optional, BinaryIO
from datetime import datetime, timezone, timedelta
import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
from app.core.config import settings

class S3Storage:
    
    _client = None
    
    @classmethod
    def get_client(cls):
        if cls._client is None:
            cls._client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION,
                config=Config(
                    signature_version='s3v4',
                    retries={'max_attempts': 3, 'mode': 'adaptive'}
                )
            )
        return cls._client
    
    @classmethod
    def generate_file_key(cls, folder: str, filename: str, add_timestamp: bool = True) -> str:
        _, ext = os.path.splitext(filename)
        unique_id = uuid.uuid4().hex[:12]
        
        if add_timestamp:
            timestamp = datetime.now(timezone(timedelta(hours=7))).strftime("%Y%m%d_%H%M%S")
            new_filename = f"{timestamp}_{unique_id}{ext}"
        else:
            new_filename = f"{unique_id}{ext}"
        
        date_folder = datetime.now(timezone(timedelta(hours=7))).strftime("%Y/%m")
        return f"{folder}/{date_folder}/{new_filename}"

    @classmethod
    def _upload_sync(cls, file: BinaryIO, bucket: str, key: str, extra_args: dict):
        client = cls.get_client()
        client.upload_fileobj(file, bucket, key, ExtraArgs=extra_args)

    @classmethod
    async def upload_file(
        cls,
        file: BinaryIO,
        folder: str,
        filename: str,
        content_type: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> dict:
        file_key = cls.generate_file_key(folder, filename)
        
        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type
        if metadata:
            extra_args['Metadata'] = metadata
        
        try:
            await asyncio.to_thread(
                cls._upload_sync, 
                file, 
                settings.AWS_S3_BUCKET, 
                file_key, 
                extra_args
            )
            
            file_url = f"https://{settings.AWS_S3_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/{file_key}"
            
            cdn_url = None
            if settings.CDN_URL:
                cdn_url = f"{settings.CDN_URL}/{file_key}"
            
            return {
                "file_key": file_key,
                "file_url": file_url,
                "cdn_url": cdn_url,
                "bucket": settings.AWS_S3_BUCKET,
            }
        
        except ClientError as e:
            raise Exception(f"Upload file len S3 that bai: {str(e)}")
        except Exception as e:
             raise Exception(f"Loi khong xac dinh khi upload: {str(e)}")
    
    @classmethod
    async def delete_file(cls, file_key: str) -> bool:
        client = cls.get_client()
        try:
            await asyncio.to_thread(
                client.delete_object,
                Bucket=settings.AWS_S3_BUCKET,
                Key=file_key
            )
            return True
        except ClientError as e:
            print(f"Xoa file tu S3 that bai: {str(e)}")
            return False
    
    @classmethod
    async def get_presigned_url(cls, file_key: str, expiration: int = 3600) -> str:
        client = cls.get_client()
        try:
            url = client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': settings.AWS_S3_BUCKET,
                    'Key': file_key
                },
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            raise Exception(f"Tao presigned URL that bai: {str(e)}")
    
    @classmethod
    async def file_exists(cls, file_key: str) -> bool:
        client = cls.get_client()
        try:
            await asyncio.to_thread(
                client.head_object,
                Bucket=settings.AWS_S3_BUCKET,
                Key=file_key
            )
            return True
        except ClientError:
            return False

__all__ = ["S3Storage"]