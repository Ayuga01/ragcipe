import os
from dotenv import load_dotenv
from langchain_community.tools.tavily_search import TavilySearchResults

load_dotenv()
api_key = os.getenv("TAVILY_API_KEY")
if not api_key:
    print("TAVILY_API_KEY is not set.")
    exit(1)

print("Testing Tavily with API key:", api_key[:5] + "...")
try:
    tool = TavilySearchResults(max_results=1, tavily_api_key=api_key)
    res = tool.invoke("recipe with tomato")
    print("Result:", res)
except Exception as e:
    print("Error:", e)
