"""
Vercel Serverless Function - Book Processor API with Authentication
"""

import hashlib
import hmac
import os
import secrets
import time
from fastapi import FastAPI, HTTPException, Request, Response, Cookie, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Any, Dict
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from book_processor_refactored import BookProcessor, process_book_data

app = FastAPI(
    title="Book Processor API",
    description="Process and validate book data",
    version="2.1.0",
    docs_url=None,  # Disable docs for security
    redoc_url=None
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# Authentication
# =============================================================================

# Password from environment variable, with fallback for development
# In Vercel, set APP_PASSWORD environment variable
APP_PASSWORD = os.environ.get("APP_PASSWORD", "Blake2011@")
SESSION_SECRET = os.environ.get("SESSION_SECRET", "book-processor-secret-key-change-in-prod")
SESSION_DURATION = 60 * 60 * 24 * 7  # 7 days in seconds


def hash_password(password: str) -> str:
    """Create a hash of the password."""
    return hashlib.sha256(password.encode()).hexdigest()


def create_session_token(timestamp: int) -> str:
    """Create a signed session token."""
    message = f"{timestamp}:{hash_password(APP_PASSWORD)}"
    signature = hmac.new(
        SESSION_SECRET.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return f"{timestamp}:{signature}"


def verify_session_token(token: str) -> bool:
    """Verify a session token is valid and not expired."""
    if not token:
        return False

    try:
        parts = token.split(":")
        if len(parts) != 2:
            return False

        timestamp = int(parts[0])
        signature = parts[1]

        # Check if expired
        if time.time() - timestamp > SESSION_DURATION:
            return False

        # Verify signature
        expected_token = create_session_token(timestamp)
        return hmac.compare_digest(token, expected_token)

    except (ValueError, TypeError):
        return False


async def require_auth(request: Request, session: Optional[str] = Cookie(None, alias="book_session")):
    """Dependency to require authentication."""
    if not verify_session_token(session):
        raise HTTPException(status_code=401, detail="Authentication required")
    return True


class LoginRequest(BaseModel):
    """Login request body."""
    password: str


class AuthResponse(BaseModel):
    """Authentication response."""
    success: bool
    message: str


@app.post("/api/auth/login")
async def login(request: LoginRequest, response: Response):
    """Authenticate with password and get session cookie."""
    if request.password == APP_PASSWORD:
        # Create session token
        token = create_session_token(int(time.time()))

        # Set cookie
        response.set_cookie(
            key="book_session",
            value=token,
            max_age=SESSION_DURATION,
            httponly=True,
            secure=True,
            samesite="strict"
        )

        return AuthResponse(success=True, message="Login successful")

    raise HTTPException(status_code=401, detail="Invalid password")


@app.post("/api/auth/logout")
async def logout(response: Response):
    """Clear session cookie."""
    response.delete_cookie(key="book_session")
    return AuthResponse(success=True, message="Logged out")


@app.get("/api/auth/check")
async def check_auth(session: Optional[str] = Cookie(None, alias="book_session")):
    """Check if current session is valid."""
    is_valid = verify_session_token(session)
    return {"authenticated": is_valid}


# =============================================================================
# Book Processing Models
# =============================================================================

class BookInput(BaseModel):
    """Input model for book data."""
    title: str
    author: str | List[str]
    isbn: Optional[str] = None
    publication_date: Optional[str] = None
    price: Optional[str | float] = None
    pages: Optional[str | int] = None
    genre: Optional[str | List[str]] = None
    language: Optional[str] = None
    description: Optional[str] = None


class ProcessingOptions(BaseModel):
    """Options for book processing."""
    title_case: bool = True
    truncate_description: bool = False
    description_max_length: int = 500
    sanitize_output: bool = True


class ProcessRequest(BaseModel):
    """Request body for processing endpoint."""
    book: BookInput
    options: Optional[ProcessingOptions] = None


class ProcessResponse(BaseModel):
    """Response model for processed book."""
    success: bool
    errors: List[str]
    warnings: List[str]
    data: Optional[Dict[str, Any]] = None


# =============================================================================
# Public Endpoints
# =============================================================================

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "Book Processor API",
        "version": "2.1.0",
        "auth_required": True
    }


@app.get("/api")
async def api_info():
    """API information endpoint."""
    return {
        "endpoints": {
            "POST /api/auth/login": "Authenticate with password",
            "POST /api/auth/logout": "Clear session",
            "GET /api/auth/check": "Check authentication status",
            "POST /api/process": "Process a single book (requires auth)",
            "POST /api/batch": "Process multiple books (requires auth)",
            "GET /api/genres": "List valid genres (requires auth)",
            "GET /api/languages": "List valid language codes (requires auth)"
        }
    }


# =============================================================================
# Protected Endpoints
# =============================================================================

@app.post("/api/process", response_model=ProcessResponse)
async def process_single_book(
    request: ProcessRequest,
    auth: bool = Depends(require_auth)
):
    """Process a single book and return validated/formatted data."""
    book_dict = request.book.model_dump()

    options = None
    if request.options:
        options = request.options.model_dump()

    result = process_book_data(book_dict, options)

    return ProcessResponse(
        success=result["success"],
        errors=result["errors"],
        warnings=result["warnings"],
        data=result["data"]
    )


class BatchRequest(BaseModel):
    """Request body for batch processing."""
    books: List[BookInput]
    options: Optional[ProcessingOptions] = None


class BatchResponse(BaseModel):
    """Response model for batch processing."""
    total: int
    successful: int
    failed: int
    results: List[ProcessResponse]


@app.post("/api/batch", response_model=BatchResponse)
async def process_batch(
    request: BatchRequest,
    auth: bool = Depends(require_auth)
):
    """Process multiple books at once."""
    results = []
    successful = 0
    failed = 0

    options = None
    if request.options:
        options = request.options.model_dump()

    for book in request.books:
        book_dict = book.model_dump()
        result = process_book_data(book_dict, options)

        if result["success"]:
            successful += 1
        else:
            failed += 1

        results.append(ProcessResponse(
            success=result["success"],
            errors=result["errors"],
            warnings=result["warnings"],
            data=result["data"]
        ))

    return BatchResponse(
        total=len(request.books),
        successful=successful,
        failed=failed,
        results=results
    )


@app.get("/api/genres")
async def list_genres(auth: bool = Depends(require_auth)):
    """Return list of valid genres."""
    from book_processor_refactored import VALID_GENRES
    return {"genres": sorted(list(VALID_GENRES))}


@app.get("/api/languages")
async def list_languages(auth: bool = Depends(require_auth)):
    """Return list of valid language codes."""
    from book_processor_refactored import VALID_LANGUAGES
    return {"languages": sorted(list(VALID_LANGUAGES))}
