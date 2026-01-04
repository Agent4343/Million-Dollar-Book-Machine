"""
Railway entrypoint.

Railpack falls back to running main.py/app.py when it can't infer a start command.
This file starts the FastAPI app with uvicorn on the Railway-provided PORT.
"""

import os

import uvicorn


def main() -> None:
    port = int(os.environ.get("PORT", "3000"))
    uvicorn.run("api.index:app", host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    main()

