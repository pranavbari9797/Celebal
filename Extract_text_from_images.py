pip install azure-storage-blob azure-ai-vision azure-functions
import os
import json
import time
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from azure.ai.vision import ComputerVisionClient
from azure.ai.vision.models import OperationStatusCodes
from msrest.authentication import CognitiveServicesCredentials
from azure.core.credentials import AzureKeyCredential
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Azure Blob Storage configuration
input_container_name = "input-container"
output_container_name = "output-container"
connect_str = "YOUR_AZURE_STORAGE_CONNECTION_STRING"

# Azure Computer Vision configuration
endpoint = "YOUR_COMPUTER_VISION_ENDPOINT"
subscription_key = "YOUR_COMPUTER_VISION_SUBSCRIPTION_KEY"

# Email configuration
sendgrid_api_key = "YOUR_SENDGRID_API_KEY"
from_email = "YOUR_EMAIL"
to_email = "RECIPIENT_EMAIL"

# Initialize BlobServiceClient
blob_service_client = BlobServiceClient.from_connection_string(connect_str)

# Initialize Computer Vision Client
vision_client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(subscription_key))


def process_image(blob_url):
    # Read the image
    read_response = vision_client.read(blob_url, raw=True)

    # Get the ID for the read operation
    read_operation_location = read_response.headers["Operation-Location"]
    operation_id = read_operation_location.split("/")[-1]

    # Wait for the read operation to complete
    while True:
        result = vision_client.get_read_result(operation_id)
        if result.status not in [OperationStatusCodes.running, OperationStatusCodes.not_started]:
            break
        time.sleep(1)

    # Extract text
    if result.status == OperationStatusCodes.succeeded:
        extracted_text = []
        for text_result in result.analyze_result.read_results:
            for line in text_result.lines:
                extracted_text.append(line.text)
        return extracted_text
    return None


def upload_json(blob_name, data):
    json_data = json.dumps(data)
    blob_client = blob_service_client.get_blob_client(container=output_container_name, blob=blob_name)
    blob_client.upload_blob(json_data, overwrite=True)


def send_email(subject, content):
    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        html_content=content
    )
    try:
        sg = SendGridAPIClient(sendgrid_api_key)
        sg.send(message)
    except Exception as e:
        print(f"Error sending email: {e}")


def main():
    # List blobs in the input container
    input_container_client = blob_service_client.get_container_client(input_container_name)
    blob_list = input_container_client.list_blobs()

    for blob in blob_list:
        blob_client = input_container_client.get_blob_client(blob.name)
        blob_url = blob_client.url
        extracted_text = process_image(blob_url)

        if extracted_text:
            # Create output JSON
            output_data = {"filename": blob.name, "extracted_text": extracted_text}
            output_blob_name = f"{os.path.splitext(blob.name)[0]}.json"
            upload_json(output_blob_name, output_data)

            # Send email notification
            send_email(
                subject="Text Extraction Completed",
                content=f"The text extraction for {blob.name} has been completed and the result has been uploaded."
            )


if __name__ == "__main__":
    main()
