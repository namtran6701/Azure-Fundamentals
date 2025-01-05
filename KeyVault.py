from azure.keyvault.secrets import SecretClient
from dotenv import load_dotenv 
from azure.identity import DefaultAzureCredential, CredentialUnavailableError
import os 
import logging 
logging.basicConfig(level=logging.INFO)

load_dotenv()

def get_secret(secret_name):
    try:
        vault_url = os.getenv("AZURE_VAULT_URL")
        credentials = DefaultAzureCredential()
        client = SecretClient(vault_url = vault_url, credential = credentials)
        secret = client.get_secret(secret_name)
        return secret.value
    except CredentialUnavailableError:
        logging.error("No valid Azure credentials found. Please check your environment variables.")
        return None
    
if __name__ == "__main__":
    secret_name = "ExampleKey"
    secret_value = get_secret(secret_name)
    if secret_value:
        logging.info(f"Secret '{secret_name}' retrieved successfully.")
        print(f'Secret value: {secret_value}')
    else:
        logging.error(f"Failed to retrieve secret '{secret_name}'.")
