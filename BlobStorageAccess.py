from azure.identity import ClientSecretCredential
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
from config import CONTAINER_NAME
import os

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
                 tenant_id: str = os.getenv("AZURE_TENANT_ID")):
        
        # Clean up storage URL
        storage_url = storage_url.rstrip('/')
        
        # Validate inputs
        if not all([container_name, storage_url, client_id, client_secret, tenant_id]):
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

if __name__ == "__main__":
    blob_storage = EntraIDBlobStorage()
    blob_name = "weekly_economics.txt"
    data = blob_storage.download_blob(blob_name)
    print(data)
        

