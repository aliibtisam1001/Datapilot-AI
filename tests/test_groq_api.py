"""
Module 2 - Minimal test script to verify Groq API connectivity.
Sends one prompt and prints the real response.
"""
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
from langchain_groq import ChatGroq

# Load the API key from .env
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    print("ERROR: GROQ_API_KEY not found in environment.")
    exit(1)

print(f"API key loaded: {api_key[:8]}...{api_key[-4:]}")

# Create a ChatGroq instance
llm = ChatGroq(
    model="qwen/qwen3.6-27b",
    temperature=0,
    api_key=api_key,
)

# Send a simple test prompt
print("\nSending test prompt to Groq...")
response = llm.invoke("What is 2 + 2? Reply in one sentence.")

print(f"\nModel used: qwen/qwen3.6-27b")
print(f"Response:   {response.content}")
print("\n✅ Groq API connection verified!")
