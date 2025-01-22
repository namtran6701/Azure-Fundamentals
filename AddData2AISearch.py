import requests
import logging
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
import json 
import uuid

# Create a logger for the 'azure' SDK
logger = logging.getLogger('azure')
logger.setLevel(logging.DEBUG)


#############################################
# Env variables 
#############################################

config = json.load(open('config.json'))
service_endpoint = config["search_service_url"]
# index_name = config["search_index_name"]
storage_account_name = config["storage_account_name"]
ingestion_function_url = config["ingestion_function_url"] + "/api/document-chunking"
index_name = 'financial-index'
container_name = 'namstorage'

#############################################
# Authentication 
#############################################

credential = DefaultAzureCredential()
search_client = SearchClient(service_endpoint, index_name, credential)

#############################################
# Add documents to index
#############################################

def upload_to_search(chunks):
    try:
        # Debug print to see the structure of chunks
        print("Received chunks structure:", json.dumps(chunks, indent=2))
        
        documents = []
        # Check if chunks is a list or has 'values' key
        chunk_list = chunks.get('values', []) if isinstance(chunks, dict) else chunks
        
        for chunk in chunk_list:
            if 'data' in chunk:
                
                # Each chunk['data']['chunks'] contains an array of chunks
                for inner_chunk in chunk['data']['chunks']:
                    unique_id = str(uuid.uuid4())
                    document = {
                        'content': inner_chunk.get('content', ''),
                        'file_name': inner_chunk.get('filepath', ''),
                        'title': inner_chunk.get('filepath', ''),
                        'doc_id': unique_id,
                        'url': inner_chunk.get('url', ''),
                        'page_number': inner_chunk.get('page', ''),
                        'vector': inner_chunk.get('contentVector', '')
                    }
                    documents.append(document)
        
        if documents:
            print(f"Uploading {len(documents)} documents to search")
            result = search_client.upload_documents(documents=documents)
            print(f"Upload results: {result}")
            return result
        else:
            print("No valid documents to upload")
            return None
    except Exception as e:
        print(f"Error uploading to search index: {e}")
        print("Chunks structure that caused error:", json.dumps(chunks, indent=2))
        raise

""" 
There is a local chunking function that can eb used to chunk the documents 

local_chunking = "http://localhost:7071/api/document-chunking"

Now what we need do is to send the documents to the chunking function and then send the chunks to the index 


"""


# get data from blob storage 
from BlobStorageAccess import EntraIDBlobStorage

BlobStorageManager = EntraIDBlobStorage(container_name="namstorage")

# create a function to send the file to the chunking function 
def chunk_document(document_name):
    # Handle spaces in the URL by encoding them, but only in the path portion
    path_parts = document_name.split('/')
    filename = path_parts[-1]
    path_prefix = '/'.join(path_parts[:-1]) if len(path_parts) > 1 else ''
    
    encoded_filename = filename.replace(" ", "%20")
    encoded_document_name = f"{path_prefix}/{encoded_filename}" if path_prefix else encoded_filename
    
    # Generate SAS token for the blob
    sas_token = BlobStorageManager.create_service_sas_blob(document_name)
    
    # Construct the payload
    payload = {
        "values": [
            {
                "recordId": document_name,
                "data": {
                    "documentContentType": BlobStorageManager.get_content_type(document_name),
                    "documentUrl": f"https://{storage_account_name}.blob.core.windows.net/{container_name}/{encoded_document_name}",
                    "documentSasToken": f"?{sas_token}",
                    "documentContent": ""
                }
            }
        ]
    }

    # Add error handling for the request
    try:
        print(f"Sending payload: {json.dumps(payload, indent=2)}")
        response = requests.post(ingestion_function_url, json=payload)
        response.raise_for_status()
        
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.text}")
        
        return response.json() if response.text else {}
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return {}

# Process blobs and upload chunks
for blob in BlobStorageManager.list_blobs():  # Process first 2 blobs
    print(f"\nProcessing: {blob}")
    if blob.endswith('.txt'):
        try:
            chunks = chunk_document(blob)
            if chunks:
                print(f"Number of values in chunks: {len(chunks.get('values', []))}")
                upload_result = upload_to_search(chunks)
                print(f"Upload completed for {blob}")
        except Exception as e:
            print(f"Error processing {blob}: {e}")

