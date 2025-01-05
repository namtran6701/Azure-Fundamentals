from azure.keyvault.secrets import SecretClient
from dotenv import load_dotenv 
from azure.identity import DefaultAzureCredential, CredentialUnavailableError
import os 
import logging 
logging.basicConfig(level=logging.INFO)

load_dotenv()

def get_secret(secret_name):
    try:
        # Step 1: Get the Key Vault URL from environment variables
        vault_url = os.getenv("AZURE_VAULT_URL")
        # Example: "https://namkeyvault.vault.azure.net/"

        # Step 2: Create an Azure credential object
        credentials = DefaultAzureCredential()
        # DefaultAzureCredential tries multiple authentication methods in this order:
        # 1. Environment variables (AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID)
        # 2. Managed Identity
        # 3. Visual Studio Code credentials
        # 4. Azure CLI credentials
        # 5. Azure PowerShell credentials

        # Step 3: Create a Key Vault client
        client = SecretClient(vault_url=vault_url, credential=credentials)
        # This creates a client that can interact with Key Vault using our credentials

        # Step 4: Retrieve the secret
        secret = client.get_secret(secret_name)
        # Fetches the secret with the given name from Key Vault
        
        # Step 5: Return just the value of the secret
        return secret.value
        # The secret object contains metadata, but we only want the actual value

    except CredentialUnavailableError:
        # This error occurs if no valid authentication method is found
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
