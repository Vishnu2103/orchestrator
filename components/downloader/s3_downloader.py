import boto3
import logging
from botocore import UNSIGNED
from botocore.client import Config
from dataclasses import dataclass
from typing import Dict, Any
import time

logger = logging.getLogger(__name__)

@dataclass
class ModuleConfig:
    module_id: str
    identifier: str
    user_config: Dict[str, Any]

class S3Downloader:
    def __init__(self, config: ModuleConfig):
        self.config = config
        logger.info(f"Initializing S3 downloader with access type: {config.user_config['access']}")
        self.s3_client = boto3.client(
            's3',
            config=Config(signature_version=UNSIGNED) if config.user_config['access'] == 'public' else None
        )

    def download_file(self) -> bytes:
        start_time = time.time()
        bucket, key = self._parse_s3_uri(self.config.user_config['s3_link'])
        logger.info(f"Downloading file from bucket: {bucket}, key: {key}")
        
        try:
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            content = response['Body'].read()
            download_time = time.time() - start_time
            content_size_mb = len(content) / (1024 * 1024)
            
            logger.info(f"Download completed in {download_time:.2f} seconds")
            logger.info(f"File size: {content_size_mb:.2f} MB")
            return content
        except Exception as e:
            logger.error(f"Error downloading file: {str(e)}")
            raise

    def _parse_s3_uri(self, uri: str) -> tuple:
        path = uri.replace('s3://', '')
        bucket, *key_parts = path.split('/')
        return bucket, '/'.join(key_parts) 