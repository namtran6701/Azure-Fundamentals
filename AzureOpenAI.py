""" 
In this module, we will be attempting to use Azure OpenAI 
Authenticated with Microsoft Entra ID
to avoid exposing the API key in the code.
"""

import os 
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from langchain_openai import AzureChatOpenAI
from openai import AzureOpenAI
from langchain_azure_ai.chat_models import AzureAIChatCompletionsModel
from pydantic import BaseModel, Field
from typing import Dict, Union
import logging
from langchain_core.messages import HumanMessage, SystemMessage

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [AzureOpenAI] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)



class LLMConfig(BaseModel):

    """Configuration for the Azure OpenAI API for Microsoft Entra ID Authentication """

    api_base: str = Field(default=os.getenv("AZURE_OPENAI_API_BASE"), description="The base URL for the Azure OpenAI API")
    api_version: str = Field(default=os.getenv("AZURE_OPENAI_API_VERSION"), description="The API version for the Azure OpenAI API")
    deployment_name: str = Field(..., description="The name of the Azure OpenAI model to use")
    api_key: str = Field(default=os.getenv("AZURE_OPENAI_API_KEY"), description="The API key for the Azure OpenAI API in case of no Microsoft Entra ID Authentication")

    class Config: 
        frozen = True # makes the config object immutable 
    
    def get_token(self):
        """
        Get a token for the Azure OpenAI API
        """
        logger.info("Attempting to get bearer token for Azure OpenAI API")
        try:
            token = get_bearer_token_provider(
                DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")
            logger.info("Successfully obtained bearer token")
            return token
        except Exception as e:
            logger.error(f"Failed to get bearer token: {str(e)}", exc_info=True)
            raise
    
class PromptTemplate(BaseModel): 
    
    """ 
    This class is a collection of system prompts 
    """
    
    basic_system_prompt: str = Field(default = "You're a helpful assistant")

    creative_system_prompt: str = Field(default = "You're a creative assistant, answer questions in a creative way")

    class Config: 
        frozen = True

class LLMManager:
    def __init__(self, deployment_name: str):
        logger.info(f"Initializing LLMManager with deployment: {deployment_name}")
        logger.info("Setting up PromptTemplate and configuration")
        self.prompts = PromptTemplate()
        self._clients: Dict[str, Union[AzureOpenAI, AzureChatOpenAI]] = {}
        self.config = LLMConfig(deployment_name=deployment_name)
        logger.info("LLMManager initialization complete")
    
    def get_client(self, client_type: str, use_langchain: bool = False) -> Union[AzureOpenAI, AzureChatOpenAI]:
        logger.info(f"Getting client of type: {client_type} (use_langchain: {use_langchain})")
        
        """
        Get or create an Azure OpenAI client
        
        Args: 
            client_type: Type of client to create (chat model or embedding model)
            use_langchain: whether to use langchain or not
        """

        try:
            if use_langchain:
                logger.info("Creating LangChain client")
                client = AzureAIChatCompletionsModel(
                    endpoint = f"{self.config.api_base}openai/deployments/{self.config.deployment_name}",
                    credential = DefaultAzureCredential(),
                    model_name = self.config.deployment_name,
                )
            else:
                logger.info("Creating standard Azure OpenAI client")
                client = AzureOpenAI(
                    azure_ad_token_provider=self.config.get_token(), 
                    api_version=self.config.api_version,
                    azure_endpoint=self.config.api_base,
                )
            
            logger.info(f"Successfully created client: {type(client).__name__}")
            self._clients[client_type] = client
            return client
        except Exception as e:
            logger.error(f"Failed to create client: {str(e)}", exc_info=True)
            raise
    
    def get_prompt(self, prompt_type: str) -> str:
        """
        Get a system prompt
        """
        logger.info(f"Retrieving prompt of type: {prompt_type}")
        try:
            prompt = getattr(self.prompts, prompt_type)
            logger.info(f"Successfully retrieved prompt: {prompt[:50]}...")
            return prompt
        except AttributeError as e:
            logger.error(f"Unknown prompt type: {prompt_type}")
            raise ValueError(f"Unknown prompt type: {prompt_type}")
    
    def get_response(self, prompt_type: str, client_type: str, use_langchain: bool = False) -> str:
        logger.info(f"Getting response using prompt_type: {prompt_type}, client_type: {client_type}")
        try:
            client = self.get_client(client_type, use_langchain=use_langchain)
            prompt = self.get_prompt(prompt_type)
            
            logger.info(f"Sending request with deployment: {self.config.deployment_name}")
            
            if use_langchain:
                logger.info("Using LangChain for request")
                messages = [
                    SystemMessage(content=prompt),
                    HumanMessage(content="Hello!")]
                
                response = client.invoke(messages)
                logger.info("Successfully received LangChain response")
                return response.content
            else:
                logger.info("Using standard Azure OpenAI client for request")
                response = client.chat.completions.create(
                    model=self.config.deployment_name,
                    messages=[
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": "Hello!"}
                    ],
                    max_tokens=100
                )
                logger.info("Successfully received Azure OpenAI response")
                return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error getting response: {str(e)}", exc_info=True)
            raise

if __name__ == "__main__":
    # llm_manager = LLMManager(deployment_name="Agent")
    # print(llm_manager.get_response("basic_system_prompt", "Agent"))
    # test token
    llm_manager = LLMManager(deployment_name="Agent")
    print(llm_manager.get_response("basic_system_prompt", "Agent", use_langchain=True))


# todo:
""" 
Fix langchain client issue 

add message for chat in chat model

"""