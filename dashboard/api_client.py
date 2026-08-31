"""The dashboard's only data boundary: FastAPI over HTTP."""
import os
import httpx
API_BASE_URL=os.getenv("API_BASE_URL","http://localhost:8000")
def get(path:str):
    """Read dashboard data with a short timeout and useful failure context."""
    response=httpx.get(f"{API_BASE_URL}{path}",timeout=10); response.raise_for_status(); return response.json()
def post(path:str,params:dict|None=None):
    """Invoke an explicit API action."""
    response=httpx.post(f"{API_BASE_URL}{path}",params=params,timeout=60); response.raise_for_status(); return response.json()
