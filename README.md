# Azure Blob Storage Access Module

This module provides different methods to access Azure Blob Storage using various authentication approaches.

## Features

- Multiple authentication methods:
  - Connection String
  - SAS Token
  - Microsoft Entra ID (formerly Azure AD)
- Blob download functionality
- Error handling and validation

## Prerequisites

- Python 3.x
- Azure Storage Account
- Azure AD App Registration (for Entra ID authentication)

## Installation

1. Clone the repository
2. Install required packages:

```bash
pip install azure-storage-blob azure-identity python-dotenv
```

3. Create a `.env` file with the required environment variables. You can use the `.env.template` file as a reference.

## Configuration

1. Copy `.env.template` to `.env`:

```bash
cp .env.template .env
```

2. Fill in your Azure credentials in `.env`:
```env
AZURE_STORAGE_URL=https://<your-storage-account>.blob.core.windows.net/
AZURE_TENANT_ID=<your-tenant-id>
AZURE_CLIENT_ID=<your-client-id>
AZURE_CLIENT_SECRET=<your-client-secret>
AZURE_CONNECTION_STRING=<your-connection-string>
AZURE_SAS_TOKEN=<your-sas-token>
```

3. Update `config.py` with your container name:
```python
CONTAINER_NAME = "your-container-name"
```

## Usage

### Using Microsoft Entra ID (Recommended)
```python
from main import EntraIDBlobStorage

# Initialize storage client
blob_storage = EntraIDBlobStorage()

# Download blob
data = blob_storage.download_blob("your-blob-name.txt")
print(data)
```

### Using SAS Token
```python
from main import SASBlobStorage

blob_storage = SASBlobStorage()
data = blob_storage.download_blob("your-blob-name.txt")
```

### Using Connection String
```python
from main import ConStrBlobStorage

blob_storage = ConStrBlobStorage()
data = blob_storage.download_blob("your-blob-name.txt")
```

## Security Best Practices

1. Use Microsoft Entra ID authentication when possible
2. Rotate credentials regularly
3. Use minimum required permissions
4. Store sensitive credentials in Azure Key Vault in production

## Required RBAC Roles

For Microsoft Entra ID authentication, ensure your service principal has:
- `Storage Blob Data Reader` role (minimum for reading blobs)
- `Reader` role (for container operations)

## License

[MIT](LICENSE)

