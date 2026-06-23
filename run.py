"""
Server entry point — starts the FastAPI application with uvicorn.
Run: python run.py
"""
import os
import sys
from pathlib import Path

# Ensure project root is on the Python path
root = Path(__file__).parent
sys.path.insert(0, str(root))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    is_prod = "PORT" in os.environ
    
    print("ClaimIQ OPD Claim Adjudication Tool")
    print("-" * 40)
    print(f"Starting server at:  http://0.0.0.0:{port}")
    print(f"API docs at:         http://0.0.0.0:{port}/docs")
    print("-" * 40)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=not is_prod,
        log_level="info",
    )
