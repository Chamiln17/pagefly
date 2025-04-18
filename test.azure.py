from dotenv import load_dotenv
import os
from langchain_openai import AzureChatOpenAI
import getpass

# Load environment variables from .env
load_dotenv()


if not os.environ.get("AZURE_OPENAI_API_KEY"):
    os.environ["AZURE_OPENAI_API_KEY"] = getpass.getpass("Enter API key for Azure: ")


llm = AzureChatOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT"],
    openai_api_version="2024-12-01-preview",
)

# Simple test prompt
response = llm.invoke("Hello! Can you suggest a creative UI idea for a weather app?")

print(response)
