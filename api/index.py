"""
Vercel Serverless Function - Book Processor API
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Any, Dict
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from book_processor_refactored import BookProcessor, process_book_data

app = FastAPI(
    title="Book Processor API",
    description="Process and validate book data",
    version="2.1.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "Book Processor API",
        "version": "2.1.0"
    }


@app.get("/api")
async def api_info():
    """API information endpoint."""
    return {
        "endpoints": {
            "POST /api/process": "Process a single book",
            "POST /api/batch": "Process multiple books",
            "GET /api/genres": "List valid genres",
            "GET /api/languages": "List valid language codes"
        }
    }


@app.post("/api/process", response_model=ProcessResponse)
async def process_single_book(request: ProcessRequest):
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
async def process_batch(request: BatchRequest):
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
async def list_genres():
    """Return list of valid genres."""
    from book_processor_refactored import VALID_GENRES
    return {"genres": sorted(list(VALID_GENRES))}


@app.get("/api/languages")
async def list_languages():
    """Return list of valid language codes."""
    from book_processor_refactored import VALID_LANGUAGES
    return {"languages": sorted(list(VALID_LANGUAGES))}
