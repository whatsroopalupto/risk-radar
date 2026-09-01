"""The dashboard's only data boundary: FastAPI over HTTP."""
import os
import httpx
API_BASE_URL=os.getenv("API_BASE_URL","http://localhost:8000")
# A shared, connection-pooled client: a page load fires several sequential reads,
# and a fresh TCP handshake per call was the dominant cost on loopback.
_client=httpx.Client(base_url=API_BASE_URL,timeout=10)
def get(path:str):
    """Read dashboard data with a short timeout and useful failure context."""
    response=_client.get(path); response.raise_for_status(); return response.json()
def post(path:str,params:dict|None=None):
    """Invoke an explicit API action. Generous timeout: a live run can fetch several RSS feeds (each with its
    own bounded timeout) and then run several sequential LLM extraction batches, each taking tens of seconds."""
    response=_client.post(path,params=params,timeout=300); response.raise_for_status(); return response.json()
