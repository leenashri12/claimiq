"""
Server entry point — starts the FastAPI application with uvicorn.
Run: python run.py
"""
import sys
import subprocess
from pathlib import Path

# Ensure project root is on the Python path
root = Path(__file__).parent
sys.path.insert(0, str(root))

if __name__ == "__main__":
    import uvicorn
    print("Plum OPD Claim Adjudication Tool")
    print("-" * 40)
    print("Starting server at:  http://localhost:8000")
    print("API docs at:         http://localhost:8000/docs")
    print("-" * 40)
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
