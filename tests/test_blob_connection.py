from services.blob_service import BlobService


def test_blob_connection():
    blob_service = BlobService()

    print("Blob client created successfully")
    print("Container name:", blob_service.container_name)

    container_client = blob_service.client.get_container_client(
        blob_service.container_name
    )

    exists = container_client.exists()

    print("Container exists:", exists)


if __name__ == "__main__":
    test_blob_connection()