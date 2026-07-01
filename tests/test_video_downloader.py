from services.video_downloader import Videodownloader


def test_download_and_upload():
    youtube_url = "https://youtu.be/Bcpu-jqAL6w?si=WuONM5e5LG2RVYFv"

    downloader = Videodownloader()

    result = downloader.download_and_upload(youtube_url)

    print("Upload result:")
    print("Blob name:", result["blob_name"])
    print("SAS URL:", result["sas_url"])
    print("Video ID:", result["video_id"])
    print("Title:", result["title"])
    print("Duration:", result["duration"])

    assert result["blob_name"] is not None
    assert result["sas_url"].startswith("https://")
    assert "?" in result["sas_url"]


if __name__ == "__main__":
    test_download_and_upload()