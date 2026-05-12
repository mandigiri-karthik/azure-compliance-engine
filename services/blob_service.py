import logging
from datetime import datetime, timedelta, timezone

import requests
from azure.storage.blob import (
    BlobServiceClient,
    BlobSasPermissions,
    generate_blob_sas
)

from utils.config import settings

logger = logging.getLogger(__name__)

class BlobService:
    def __init__(self):
        self.client = BlobServiceClient.from_connection_string(
            conn_str= settings.azure_storage_connection_string
        )
        self.container_name = settings.azure_storage_container_name

    def upload_from_stream(self, stream_url:str, blob_name:str) -> str:
        """
        streams the video from the url directly to the azure blob storage
        uploads chunk by chunk 4 mb each chunk

        args :
        stream_url : direct CDN url from the yt-dlp
        blob_name : name of the blob in which the video should be stored
        """
        logger.info(f"Streaming the video to the blob {blob_name}")

        container_client = self.client.get_container_client(self.container_name)

        with requests.get(url=stream_url, stream=True, timeout=60) as response:
            response.raise_for_status()

            container_client.upload_blob(
                name=blob_name,
                data= response.iter_content(chunk_size=4*1024*1024),
                overwrite= True
            )
        logger.info(f"Uploaded completed {blob_name}")

        return self.generate_sas_url(blob_name)
    
    def generate_sas_url(self, blob_name:str, expiry_hours: int=2) -> str:
        """
        Generate a temperory SAS Url with an expiry time of 2 hours
        args : 
            blob_name : name of the blob
            expiry_hours : how long the url must be valid
        """
        sas_token = generate_blob_sas(
            account_name= settings.azure_storage_account_name,
            container_name= settings.azure_storage_container_name,
            blob_name= blob_name,
            account_key= settings.azure_storage_account_key,
            permission=BlobSasPermissions(read=True),
            expiry= datetime.now(timezone.utc) + timedelta(hours=expiry_hours)
        )

        sas_url = (
            f"https://{settings.azure_storage_account_name}"
            f".blob.core.windows.net/"
            f"{self.container_name}/"
            f"{blob_name}?"
            f"{sas_token}"
        )

        logger.info(f"SAS URL generates successfully for blob_name : {blob_name} (valid for {expiry_hours})")
        return sas_url
    
    def delete_blob(self, blob_name:str) ->None :
        """
        Deletes the blob after the indexing of the video is done
        Always call this after the video indexing is done so that we can save the cost

        Args:
            blob_name : name of the blob which should be deleted
        """
        try:
            blob_client = self.client.get_blob_client(
                container= settings.azure_storage_container_name,
                blob= blob_name,
            )
            blob_client.delete_blob()
            logger.info(f"Blob deleted : {blob_name}")

        except Exception as e:
            logger.warning(f"Could not delete the Blob {blob_name} : {e}")

    def blob_exists(self, blob_name:str) -> bool:
        """
        checks if there are any blobs already exists avoids the duplicating the blobs
        Returns : 
            True if any blobs already exists else false
        """
        blob_client = self.client.get_blob_client(
            container= settings.azure_storage_container_name,
            blob = blob_name
        )

        return blob_client.exists()