from openai import AzureOpenAI
import io
import json
import openai
import time
import requests
from AzureOpenAI import LLMManager

#############################################
# Constants
#############################################
MAX_ATTEMPTS = 5
MAX_BACKOFF = 60


#############################################
# Configuration
#############################################

config = json.load(open("config.json"))
index_schema_file = config['search_index_schema_file']
# index_name = config["search_index_name"]
index_name = "financial-index"
search_service_name = config["search_service_name"]
search_service_url = "https://{}.search.windows.net/".format(search_service_name)
search_admin_key = config["search_admin_key"]
search_headers = {  
    'Content-Type': 'application/json',  
    'api-key': search_admin_key  
}  
search_api_version = config["search_api_version"]
openai_embeddings_model = config["openai_embedding_model"]
openai_embedding_api_key = config["openai_embedding_api_key"]
openai_embedding_api_base = config["openai_embedding_api_base"]
openai_gpt_model = config["openai_gpt_model"]
openai_embedding_api_version = config["openai_embedding_api_version"]
ingestion_function_url = config["ingestion_function_url"]


#############################################
# Embeddings Client
#############################################
embeddings_client = AzureOpenAI(
    api_version=openai_embedding_api_version,
    azure_endpoint=openai_embedding_api_base,
    api_key=openai_embedding_api_key,
    azure_deployment=openai_gpt_model
)


#############################################
# Embeddings Function
#############################################

def generate_embedding(text):
    if text == None:
        return None
        
    if len(text) < 10:
        return None
        
    client = AzureOpenAI(
        api_version=openai_embedding_api_version,
        azure_endpoint=openai_embedding_api_base,
        api_key=openai_embedding_api_key
    )    
    counter = 0
    incremental_backoff = 1   # seconds to wait on throttline - this will be incremental backoff
    while True and counter < MAX_ATTEMPTS:
        try:
            # text-embedding-3-small == 1536 dims
            response = client.embeddings.create(
                input=text,
                model=openai_embeddings_model
            )
            return json.loads(response.model_dump_json())["data"][0]['embedding']
        except openai.APIError as ex:
            # Handlethrottling - code 429
            if str(ex.code) == "429":
                incremental_backoff = min(MAX_BACKOFF, incremental_backoff * 1.5)
                print ('Waiting to retry after', incremental_backoff, 'seconds...')
                time.sleep(incremental_backoff)
            elif str(ex.code) == "content_filter":
                print ('API Error', ex.code)
                return None
        except Exception as ex:
            counter += 1
            print ('Error - Retry count:', counter, ex)
    return None


#############################################
# Create Index
#############################################


def create_index():
    dims = len(generate_embedding('That quick brown fox'))
    print ('Dimensions in Embedding Model:', dims)
    
    with open(index_schema_file, "r") as f_in:
        index_schema = json.loads(f_in.read())
        index_schema['name'] = index_name
        index_schema['vectorSearch']['vectorizers'][0]['azureOpenAIParameters']['resourceUri'] = openai_embedding_api_base
        index_schema['vectorSearch']['vectorizers'][0]['azureOpenAIParameters']['deploymentId'] = openai_embeddings_model
        index_schema['vectorSearch']['vectorizers'][0]['azureOpenAIParameters']['apiKey'] = openai_embedding_api_key

    
    # Making the POST requests to re-create the index  
    delete_url = f"{search_service_url}/indexes/{index_name}?api-version={search_api_version}"  
    response = requests.delete(delete_url, headers=search_headers)  
    if response.status_code == 204:  
        print(f"Index {index_name} deleted successfully.")  
        # print(json.dumps(response.json(), indent=2))  
    else:  
        print("Error deleting index, it may not exist.")  
    
    # The endpoint URL for creating the index  
    create_index_url = f"{search_service_url}/indexes?api-version={search_api_version}"  
    response = requests.post(create_index_url, headers=search_headers, json=index_schema)  
      
    # Check the response  
    if response.status_code == 201:  
        print(f"Index {index_name} created successfully.")  
        # print(json.dumps(response.json(), indent=2))  
    else:  
        print(f"Error creating index {index_name} :")  
        print(response.json())  



if __name__ == "__main__":
    create_index()

