"""
Entry point for Railway and other platforms that expect main.py.
"""
from api.index import app

# For platforms that run main.py directly
if __name__ == "__main__":
    import uvicorn
    import os

    port = int(os.environ.get("PORT", 3000))
    uvicorn.run(app, host="0.0.0.0", port=port)
