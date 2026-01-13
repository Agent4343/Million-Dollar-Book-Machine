"""
Entry point for Railway deployment.
"""
import sys
import os

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.index import app

# Railway will automatically detect this FastAPI app and run it with uvicorn
