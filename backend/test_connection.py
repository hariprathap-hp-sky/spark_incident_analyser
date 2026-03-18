# test_connection.py
from qdrant_client import QdrantClient
import os
from dotenv import load_dotenv

load_dotenv()

# Only pass api_key if it's set (avoid warning for local Docker without auth)
qdrant_kwargs = {"url": os.getenv("QDRANT_URL"), "timeout": 30}
if os.getenv("QDRANT_API_KEY"):
    qdrant_kwargs["api_key"] = os.getenv("QDRANT_API_KEY")
qdrant = QdrantClient(**qdrant_kwargs)

print(qdrant.get_collections())