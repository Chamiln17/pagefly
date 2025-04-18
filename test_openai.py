from dotenv import load_dotenv
import os
# Change this import
from langchain_openai import ChatOpenAI 
import getpass

# Load environment variables from .env
load_dotenv()

# Keep this check, but now for OPENAI_API_KEY
if not os.environ.get("OPENAI_API_KEY"):
  os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter your OpenAI API key: ")

# Instantiate ChatOpenAI 
llm = ChatOpenAI(
    model="gpt-3.5-turbo" # Or "gpt-4", "gpt-4-turbo", etc. - specify the model you want to use
    # No need for endpoint, deployment, or api_version here
)

# Simple test prompt (remains the same)
try:
    print("Attempting to invoke the OpenAI model...")
    response = llm.invoke("Hello! Can you suggest a creative UI idea for a weather app?")
    print("\nSuccess! Response:")
    print(response) # Should now print the AIMessage object
    # print(response.content) # To print just the text content of the response

except Exception as e:
    print(f"\nAn error occurred: {e}") # Print any errors encountered