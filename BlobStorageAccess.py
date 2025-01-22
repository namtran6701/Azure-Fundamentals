from azure.identity import ClientSecretCredential
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
from config import CONTAINER_NAME
from datetime import datetime, timezone, timedelta
from typing import List
import os
from azure.storage.blob import generate_blob_sas, BlobSasPermissions
load_dotenv()


##################################
# Connect to Blob using connection strin g
##################################

class ConStrBlobStorage:
    def __init__(self, container_name: str = CONTAINER_NAME, connection_str: str = os.getenv("AZURE_CONNECTION_STRING")):
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_str)
        self.container_client = self.blob_service_client.get_container_client(container_name)
    
    def download_blob(self, blob_name):
        blob_client = self.container_client.get_blob_client(blob = blob_name)
        downloaded_data = blob_client.download_blob().readall().decode("utf-8")
        return downloaded_data
    

# This method is easy to use but it is not secure because if the connection string is compromised, the data can be accessed by anyone.


##################################
# Connect to blob using SAS token
##################################

# we have to enable key access in the storage account 

class SASBlobStorage:
    def __init__(self, 
                 container_name: str = CONTAINER_NAME,
                 sas_token: str = os.getenv("AZURE_SAS_TOKEN"), 
                 storage_url: str = os.getenv("AZURE_STORAGE_URL")):
        self.blob_service_client = BlobServiceClient(account_url = storage_url, credential = sas_token)
        self.container_client = self.blob_service_client.get_container_client(container_name)

    def download_blob(self, blob_name):
        blob_client = self.container_client.get_blob_client(blob = blob_name)
        downloaded_data = blob_client.download_blob().readall().decode("utf-8")
        return downloaded_data

##################################
# Connect to blob Microsoft Entra ID
##################################

# this is the most secure way to connect to blob storage

class EntraIDBlobStorage:
    def __init__(self,
                 container_name: str = CONTAINER_NAME,
                 storage_url: str = os.getenv("AZURE_STORAGE_URL"),
                 client_id: str = os.getenv("AZURE_CLIENT_ID"),
                 client_secret: str = os.getenv("AZURE_CLIENT_SECRET"),
                 tenant_id: str = os.getenv("AZURE_TENANT_ID"),
                 account_key: str = os.getenv("BLOB_ACCOUNT_KEY")):
        
        # Clean up storage URL
        storage_url = storage_url.rstrip('/')
        
        # Validate inputs
        if not all([container_name, storage_url, client_id, client_secret, tenant_id, account_key]):
            raise ValueError("Missing required parameters")
        
        try:
            self.credentials = ClientSecretCredential(
                client_id=client_id,
                client_secret=client_secret,
                tenant_id=tenant_id
            )
            
            self.blob_service_client = BlobServiceClient(
                account_url=storage_url,
                credential=self.credentials
            )

            self.container_client = self.blob_service_client.get_container_client(container=container_name)

            self.account_key = account_key
            
            # Verify container exists
            if not self.container_client.exists():
                raise ValueError(f"Container '{container_name}' does not exist")
                
        except Exception as e:
            print(f"Failed to initialize blob storage: {str(e)}")
            raise

    def download_blob(self, blob_name):
        try:
            blob_client = self.container_client.get_blob_client(blob=blob_name)
            
            # Check if blob exists
            if not blob_client.exists():
                raise ValueError(f"Blob '{blob_name}' does not exist")
                
            downloaded_data = blob_client.download_blob().readall().decode("utf-8")
            return downloaded_data
        except Exception as e:
            print(f"Error downloading blob '{blob_name}': {str(e)}")
            raise
    
    def list_blobs(self) -> List[str]:
        blob_list = []
        for blob in self.container_client.list_blobs():
            blob_list.append(blob.name)
        return blob_list
    
    def create_service_sas_blob(self, blob_name: str):
        # Create a SAS token that's valid for one day, as an example
        start_time = datetime.now(timezone.utc)
        expiry_time = start_time + timedelta(days=1)

        sas_token = generate_blob_sas(
            account_name=self.blob_service_client.account_name,
            container_name=self.container_client.container_name,
            account_key=self.account_key,
            blob_name=blob_name,
            permission=BlobSasPermissions(read=True),
            expiry=expiry_time,
            start=start_time
    )
        return sas_token
    
    def get_content_type(self, blob_name) -> str:
        blob_client = self.container_client.get_blob_client(blob=blob_name)
        content_type = blob_client.get_blob_properties().content_settings.content_type
        return content_type
    
    
    

if __name__ == "__main__":
    blob_storage = EntraIDBlobStorage()
    # blob_name = "weekly_economics.txt"
    # data = blob_storage.download_blob(blob_name)
    # print(data)
    blob_name = "weekly_economics.txt"
    # content_type = blob_storage.get_content_type(blob_name)
    # print(f"Content type for '{blob_name}': {content_type}")
    # blob_name = blob_storage.get_blob_container_path(blob_name)
    # print(f"Blob name: {blob_name}")
    blob_list = blob_storage.list_blobs()
    print(blob_list)
