import logging
import uuid

import yt_dlp

from services.blob_service import BlobService

logger = logging.getLogger(__name__)

class Videodownloader():
    def __init__(self):
        self.blob_service = BlobService()

    def extract_stream_url(self, youtube_url:str) -> dict:
        """
        Uses the yt_dlp to extract the CDN from the youtube url, No video is doenloaded locally

        Args:
            youtube_url = url of the youtube ad
        
        Return:
            Dictionary with the stream url with the metadeata of the video
        """
        logger.info(f"Extracting the streaming url from the {youtube_url}")

        ydl_opts = {
            "format" : "best[ext=mp4]/best",
            "quiet" : True,
            "no_warnings" : True,
            "noplaylist" : True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(
                url = youtube_url,
                download= False,
            )
        
        stream_url = info["url"]
        video_id = info["id"]
        title = info["title"]
        duration = info["duration"]

        logger.info(f"Streamed Url extracted for : {title} with the duration of {duration}")

        return {
            "stream_url" : stream_url,
            "video_id" : video_id,
            "title" : title,
            "duration" : duration,
        }
    
    def download_and_upload(self, youtube_url:str) -> dict:
        """
            Full pipeline:
            1. Extract CDN stream URL via yt-dlp
            2. Stream it directly into Azure Blob
            3. Return blob name + SAS URL for Video Indexer

            Args:
                youtube_url: Full YouTube video URL

            Returns:
                dict with blob_name, sas_url, video_id, title, duration
        """
        video_info = self.extract_stream_url(youtube_url)

        blob_name = f"{video_info['video_id']}_{uuid.uuid4().hex[:8]}.mp4"
        
        logger.info(f"Starting uploading to the blob: {blob_name}")

        sas_url = self.blob_service.upload_from_stream(
            stream_url= video_info["stream_url"],
            blob_name= blob_name
        )

        logger.info(f"Upload complete. SAS URL ready for the video indexer.")

        return {
            "blob_name": blob_name,
            "sas_url":   sas_url,
            "video_id":  video_info["video_id"],
            "title":     video_info["title"],
            "duration":  video_info["duration"],
        }