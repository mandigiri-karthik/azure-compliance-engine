from services.blob_service import BlobService


def test_upload_dummy_video():
    blob_service = BlobService()

    stream_url = "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
    blob_name = "test/dummy-video.mp4"

    sas_url = blob_service.upload_from_stream(
        stream_url=stream_url,
        blob_name=blob_name
    )

    print("Uploaded successfully.")
    print("SAS URL:", sas_url)

    exists = blob_service.blob_exists(blob_name)

    print("Blob exists:", exists)

    assert exists is True
    assert sas_url.startswith("https://")
    assert "?" in sas_url

if __name__ == "__main__":
    test_upload_dummy_video()