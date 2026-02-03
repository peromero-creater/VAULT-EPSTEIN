import boto3
import os
from botocore.exceptions import ClientError
from typing import Optional

class StorageService:
    def __init__(self):
        # Allow env vars or fallback to explicit for now (user can set in .env)
        self.bucket = os.getenv("S3_BUCKET_NAME", "epstein-vault-files")
        self.region = os.getenv("S3_REGION", "us-east-1")
        
        # Initialize S3 client (autodetects AWS_ACCESS_KEY_ID etc from env)
        self.s3_client = boto3.client(
            's3', 
            region_name=self.region,
            endpoint_url=os.getenv("S3_ENDPOINT_URL") # Optional: for R2/MinIO
        )

    def upload_file(self, file_path: str, object_name: Optional[str] = None) -> Optional[str]:
        """Upload a file to an S3 bucket"""
        if object_name is None:
            object_name = os.path.basename(file_path)

        try:
            self.s3_client.upload_file(file_path, self.bucket, object_name)
            s3_path = f"s3://{self.bucket}/{object_name}"
            print(f"Uploaded {file_path} to {s3_path}")
            return s3_path
        except ClientError as e:
            print(f"Upload failed: {e}")
            return None

    def get_presigned_url(self, s3_uri: str, expiration=3600) -> Optional[str]:
        """Generate a presigned URL to share an S3 object"""
        try:
            # Parse s3://bucket/key
            if not s3_uri.startswith("s3://"):
                return None
            
            parts = s3_uri.replace("s3://", "").split("/", 1)
            if len(parts) < 2:
                return None
                
            bucket, key = parts[0], parts[1]

            response = self.s3_client.generate_presigned_url('get_object',
                                                            Params={'Bucket': bucket,
                                                                    'Key': key},
                                                            ExpiresIn=expiration)
            return response
        except ClientError as e:
            print(f"URL generation failed: {e}")
            return None

# Singleton instance
storage = StorageService()
