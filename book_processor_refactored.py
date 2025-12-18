"""
Book Processing Module for Million-Dollar-Book-Machine (Refactored)

This module handles book data processing, validation, and formatting
using a clean, modular architecture with clear separation of concerns.
"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple


# =============================================================================
# Result Types
# =============================================================================

@dataclass
class ProcessingResult:
    """Immutable result of book processing."""
    success: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    data: Optional[Dict[str, Any]] = None


@dataclass
class ValidationResult:
    """Result of a single validation check."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


# =============================================================================
# Constants
# =============================================================================

VALID_GENRES = frozenset([
    "fiction", "non-fiction", "mystery", "thriller", "romance",
    "science-fiction", "fantasy", "biography", "history", "self-help",
    "children", "young-adult", "horror", "poetry", "drama", "comedy",
    "adventure", "crime", "literary", "classic"
])

VALID_LANGUAGES = frozenset([
    "en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko",
    "ar", "hi", "nl", "sv", "no", "da", "fi", "pl", "tr", "he"
])

DATE_FORMATS = ["%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y", "%m-%d-%Y", "%m/%d/%Y", "%Y"]

TITLE_SMALL_WORDS = frozenset(["a", "an", "the", "and", "but", "or", "for", "nor", "on", "at", "to", "from", "by", "of", "in"])


# =============================================================================
# Validators
# =============================================================================

class Validator(ABC):
    """Abstract base class for field validators."""

    @abstractmethod
    def validate(self, value: Any, book_data: Dict[str, Any]) -> ValidationResult:
        """Validate a value and return the result."""
        pass


class TitleValidator(Validator):
    """Validates book title field."""

    def validate(self, value: Any, book_data: Dict[str, Any]) -> ValidationResult:
        errors, warnings = [], []

        if not value:
            errors.append("Title is required")
        elif len(value) > 500:
            errors.append("Title must be less than 500 characters")
        elif not re.match(r'^[a-zA-Z0-9\s\-\'\"\:\!\?\.\,]+$', value):
            warnings.append("Title contains special characters that may cause display issues")

        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)


class AuthorValidator(Validator):
    """Validates book author field."""

    MIN_LENGTH = 2
    MAX_LENGTH = 200

    def validate(self, value: Any, book_data: Dict[str, Any]) -> ValidationResult:
        errors, warnings = [], []

        if not value:
            errors.append("Author is required")
        elif isinstance(value, str):
            self._validate_single_author(value, 0, errors)
        elif isinstance(value, list):
            if len(value) == 0:
                errors.append("At least one author is required")
            else:
                for i, author in enumerate(value):
                    self._validate_single_author(author, i, errors)
        else:
            errors.append("Author must be a string or list of strings")

        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)

    def _validate_single_author(self, author: str, index: int, errors: List[str]) -> None:
        prefix = f"Author {index + 1} " if index > 0 else "Author "
        if not author or len(author) < self.MIN_LENGTH:
            errors.append(f"{prefix}name must be at least {self.MIN_LENGTH} characters")
        elif len(author) > self.MAX_LENGTH:
            errors.append(f"{prefix}name must be less than {self.MAX_LENGTH} characters")


class ISBNValidator(Validator):
    """Validates ISBN-10 and ISBN-13 formats."""

    def validate(self, value: Any, book_data: Dict[str, Any]) -> ValidationResult:
        if not value:
            return ValidationResult(is_valid=True)

        errors = []
        isbn = str(value).replace("-", "").replace(" ", "")

        if len(isbn) == 10:
            self._validate_isbn10(isbn, errors)
        elif len(isbn) == 13:
            self._validate_isbn13(isbn, errors)
        else:
            errors.append("ISBN must be 10 or 13 characters")

        return ValidationResult(is_valid=len(errors) == 0, errors=errors)

    def _validate_isbn10(self, isbn: str, errors: List[str]) -> None:
        total = 0
        for i, char in enumerate(isbn):
            if i == 9 and char.upper() == 'X':
                total += 10
            elif char.isdigit():
                total += int(char) * (10 - i)
            else:
                errors.append("Invalid ISBN-10 format")
                return

        if total % 11 != 0:
            errors.append("Invalid ISBN-10 checksum")

    def _validate_isbn13(self, isbn: str, errors: List[str]) -> None:
        if not isbn.isdigit():
            errors.append("ISBN-13 must contain only digits")
            return

        total = sum(int(char) * (1 if i % 2 == 0 else 3) for i, char in enumerate(isbn))
        if total % 10 != 0:
            errors.append("Invalid ISBN-13 checksum")


class DateValidator(Validator):
    """Validates publication date."""

    def validate(self, value: Any, book_data: Dict[str, Any]) -> ValidationResult:
        if not value:
            return ValidationResult(is_valid=True)

        warnings = []
        parsed_date = parse_date(value)

        if parsed_date is None:
            return ValidationResult(is_valid=False, errors=["Invalid publication date format"])

        if parsed_date > datetime.now():
            warnings.append("Publication date is in the future")
        elif parsed_date.year < 1450:
            warnings.append("Publication date is before the invention of the printing press")

        return ValidationResult(is_valid=True, warnings=warnings)


class PriceValidator(Validator):
    """Validates book price."""

    def validate(self, value: Any, book_data: Dict[str, Any]) -> ValidationResult:
        if value is None:
            return ValidationResult(is_valid=True)

        errors, warnings = [], []
        price = parse_price(value)

        if price is None:
            errors.append("Invalid price format")
        elif price < 0:
            errors.append("Price cannot be negative")
        elif price > 10000:
            warnings.append("Price seems unusually high")
        elif price == 0:
            warnings.append("Book is marked as free")

        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)


class PagesValidator(Validator):
    """Validates page count."""

    def validate(self, value: Any, book_data: Dict[str, Any]) -> ValidationResult:
        if value is None:
            return ValidationResult(is_valid=True)

        errors, warnings = [], []
        pages = parse_int(value)

        if pages is None:
            errors.append("Pages must be a number")
        elif pages < 1:
            errors.append("Pages must be at least 1")
        elif pages > 50000:
            warnings.append("Page count seems unusually high")

        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)


class GenreValidator(Validator):
    """Validates book genre(s)."""

    def validate(self, value: Any, book_data: Dict[str, Any]) -> ValidationResult:
        if not value:
            return ValidationResult(is_valid=True)

        warnings = []
        genres = [value] if isinstance(value, str) else value

        for genre in genres:
            if genre.lower() not in VALID_GENRES:
                warnings.append(f"Unknown genre: {genre}")

        return ValidationResult(is_valid=True, warnings=warnings)


class LanguageValidator(Validator):
    """Validates language code."""

    def validate(self, value: Any, book_data: Dict[str, Any]) -> ValidationResult:
        if not value:
            return ValidationResult(is_valid=True)

        warnings = []
        if value.lower() not in VALID_LANGUAGES:
            warnings.append(f"Unsupported language code: {value}")

        return ValidationResult(is_valid=True, warnings=warnings)


# =============================================================================
# Utility Functions
# =============================================================================

def parse_date(date_str: str) -> Optional[datetime]:
    """Parse a date string using multiple formats."""
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def parse_price(value: Any) -> Optional[float]:
    """Parse a price value from string or number."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace("$", "").replace(",", "").strip())
        except ValueError:
            return None
    return None


def parse_int(value: Any) -> Optional[int]:
    """Parse an integer value from string or number."""
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None


def format_title_case(title: str) -> str:
    """Format a title using proper title case rules."""
    words = title.strip().split()
    formatted = []

    for i, word in enumerate(words):
        if i == 0 or i == len(words) - 1 or word.lower() not in TITLE_SMALL_WORDS:
            formatted.append(word.capitalize())
        else:
            formatted.append(word.lower())

    return " ".join(formatted)


def normalize_isbn(isbn: str) -> Tuple[Optional[str], Optional[str]]:
    """Normalize ISBN and return (isbn_10, isbn_13) tuple."""
    clean = isbn.replace("-", "").replace(" ", "")
    if len(clean) == 10:
        return (clean, None)
    elif len(clean) == 13:
        return (None, clean)
    return (None, None)


# =============================================================================
# Book Processor
# =============================================================================

class BookProcessor:
    """Processes book data with validation and formatting."""

    DEFAULT_VALIDATORS = {
        "title": TitleValidator(),
        "author": AuthorValidator(),
        "isbn": ISBNValidator(),
        "publication_date": DateValidator(),
        "price": PriceValidator(),
        "pages": PagesValidator(),
        "genre": GenreValidator(),
        "language": LanguageValidator(),
    }

    def __init__(self, options: Optional[Dict[str, Any]] = None):
        self.options = options or {}
        self.validators = self.DEFAULT_VALIDATORS.copy()

    def process(self, book_data: Dict[str, Any]) -> ProcessingResult:
        """Process book data through validation and formatting pipeline."""
        if not book_data:
            return ProcessingResult(success=False, errors=["Book data is required"])

        # Run validation
        all_errors, all_warnings = self._validate(book_data)

        if all_errors:
            return ProcessingResult(success=False, errors=all_errors, warnings=all_warnings)

        # Format and enrich data
        processed = self._format(book_data)

        return ProcessingResult(success=True, errors=[], warnings=all_warnings, data=processed)

    def _validate(self, book_data: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Run all validators and collect errors/warnings."""
        all_errors, all_warnings = [], []

        for field_name, validator in self.validators.items():
            value = book_data.get(field_name)
            result = validator.validate(value, book_data)
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)

        return all_errors, all_warnings

    def _format(self, book_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format and enrich validated book data."""
        processed = {}

        # Title
        title = book_data["title"].strip()
        processed["title"] = format_title_case(title) if self.options.get("title_case", True) else title

        # Authors
        author = book_data["author"]
        processed["authors"] = [author.strip()] if isinstance(author, str) else [a.strip() for a in author]

        # ISBN
        if book_data.get("isbn"):
            processed["isbn_10"], processed["isbn_13"] = normalize_isbn(str(book_data["isbn"]))

        # Publication date
        if book_data.get("publication_date"):
            parsed = parse_date(book_data["publication_date"])
            if parsed:
                processed["publication_date"] = parsed.strftime("%Y-%m-%d")
                processed["publication_year"] = parsed.year

        # Price
        if "price" in book_data:
            price = parse_price(book_data["price"])
            if price is not None:
                processed["price"] = round(price, 2)
                processed["price_formatted"] = f"${price:.2f}"

        # Pages
        if "pages" in book_data:
            pages = parse_int(book_data["pages"])
            if pages is not None:
                processed["pages"] = pages

        # Genres
        if book_data.get("genre"):
            genre = book_data["genre"]
            processed["genres"] = [genre.lower()] if isinstance(genre, str) else [g.lower() for g in genre]

        # Language
        if book_data.get("language"):
            processed["language"] = book_data["language"].lower()

        # Description
        if book_data.get("description"):
            processed["description"] = self._format_description(book_data["description"])

        # Metadata
        processed["processed_at"] = datetime.now().isoformat()
        processed["processor_version"] = "2.0.0"

        return processed

    def _format_description(self, description: str) -> str:
        """Format and optionally truncate description."""
        desc = description.strip()

        if self.options.get("truncate_description"):
            max_len = self.options.get("description_max_length", 500)
            if len(desc) > max_len:
                desc = desc[:max_len - 3] + "..."

        return desc


# =============================================================================
# Public API (backwards compatible with original function)
# =============================================================================

def process_book_data(book_data: Dict[str, Any], options: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Process book data with validation, formatting, and enrichment.

    This is a backwards-compatible wrapper around the BookProcessor class.
    """
    processor = BookProcessor(options)
    result = processor.process(book_data)

    return {
        "success": result.success,
        "errors": result.errors,
        "warnings": result.warnings,
        "data": result.data,
    }


if __name__ == "__main__":
    # Example usage
    sample_book = {
        "title": "the great gatsby",
        "author": "F. Scott Fitzgerald",
        "isbn": "978-0743273565",
        "publication_date": "1925",
        "price": "$15.99",
        "pages": "180",
        "genre": ["fiction", "classic", "literary"],
        "language": "en",
        "description": "A novel about the American Dream set in the Jazz Age."
    }

    result = process_book_data(sample_book)
    print(f"Success: {result['success']}")
    print(f"Errors: {result['errors']}")
    print(f"Warnings: {result['warnings']}")
    if result['data']:
        print(f"Processed data: {result['data']}")
