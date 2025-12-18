"""
Book Processing Module for Million-Dollar-Book-Machine (Refactored)

This module handles book data processing, validation, and formatting
using a clean, modular architecture with clear separation of concerns.
"""

import html
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Any, Optional, Tuple

# Configure module logger
logger = logging.getLogger(__name__)

# =============================================================================
# Public API
# =============================================================================

__all__ = [
    "ProcessingResult",
    "ValidationResult",
    "BookProcessor",
    "process_book_data",
    "BookProcessingError",
]


# =============================================================================
# Exceptions
# =============================================================================

class BookProcessingError(Exception):
    """Base exception for book processing errors."""
    pass


# =============================================================================
# Result Types
# =============================================================================

@dataclass(frozen=True)
class ProcessingResult:
    """Immutable result of book processing."""
    success: bool
    errors: Tuple[str, ...] = field(default_factory=tuple)
    warnings: Tuple[str, ...] = field(default_factory=tuple)
    data: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class ValidationResult:
    """Immutable result of a single validation check."""
    is_valid: bool
    errors: Tuple[str, ...] = field(default_factory=tuple)
    warnings: Tuple[str, ...] = field(default_factory=tuple)


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

DATE_FORMATS = ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y", "%m-%d-%Y", "%m/%d/%Y", "%Y")

TITLE_SMALL_WORDS = frozenset(["a", "an", "the", "and", "but", "or", "for", "nor", "on", "at", "to", "from", "by", "of", "in"])

# Pre-compiled regex patterns for performance
TITLE_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-\'\"\:\!\?\.\,]+$')
PRICE_CLEANUP_PATTERN = re.compile(r'[$,\s]')

# Tolerance for float comparisons
PRICE_EPSILON = 0.001


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

    MIN_LENGTH = 1
    MAX_LENGTH = 500

    def validate(self, value: Any, book_data: Dict[str, Any]) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []

        if not value:
            errors.append("Title is required")
        elif not isinstance(value, str):
            errors.append("Title must be a string")
        elif not value.strip():
            errors.append("Title cannot be empty or whitespace only")
        elif len(value) < self.MIN_LENGTH:
            errors.append(f"Title must be at least {self.MIN_LENGTH} character")
        elif len(value) > self.MAX_LENGTH:
            errors.append(f"Title must be less than {self.MAX_LENGTH} characters")
        elif not TITLE_PATTERN.match(value):
            warnings.append("Title contains special characters that may cause display issues")

        return ValidationResult(is_valid=len(errors) == 0, errors=tuple(errors), warnings=tuple(warnings))


class AuthorValidator(Validator):
    """Validates book author field."""

    MIN_LENGTH = 2
    MAX_LENGTH = 200

    def validate(self, value: Any, book_data: Dict[str, Any]) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []

        if not value:
            errors.append("Author is required")
        elif isinstance(value, str):
            self._validate_single_author(value, 0, errors)
        elif isinstance(value, list):
            if len(value) == 0:
                errors.append("At least one author is required")
            else:
                for i, author in enumerate(value):
                    if not isinstance(author, str):
                        errors.append(f"Author {i + 1} must be a string")
                    else:
                        self._validate_single_author(author, i, errors)
        else:
            errors.append("Author must be a string or list of strings")

        return ValidationResult(is_valid=len(errors) == 0, errors=tuple(errors), warnings=tuple(warnings))

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

        errors: List[str] = []

        try:
            isbn = str(value).replace("-", "").replace(" ", "")
        except (TypeError, ValueError):
            return ValidationResult(is_valid=False, errors=("Invalid ISBN format",))

        if len(isbn) == 10:
            self._validate_isbn10(isbn, errors)
        elif len(isbn) == 13:
            self._validate_isbn13(isbn, errors)
        else:
            errors.append("ISBN must be 10 or 13 characters")

        return ValidationResult(is_valid=len(errors) == 0, errors=tuple(errors))

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

        warnings: List[str] = []

        if not isinstance(value, str):
            return ValidationResult(is_valid=False, errors=("Publication date must be a string",))

        parsed_date = parse_date(value)

        if parsed_date is None:
            return ValidationResult(is_valid=False, errors=("Invalid publication date format",))

        if parsed_date > datetime.now():
            warnings.append("Publication date is in the future")
        elif parsed_date.year < 1450:
            warnings.append("Publication date is before the invention of the printing press")

        return ValidationResult(is_valid=True, warnings=tuple(warnings))


class PriceValidator(Validator):
    """Validates book price."""

    MAX_PRICE = Decimal("10000")

    def validate(self, value: Any, book_data: Dict[str, Any]) -> ValidationResult:
        if value is None:
            return ValidationResult(is_valid=True)

        errors: List[str] = []
        warnings: List[str] = []
        price = parse_price(value)

        if price is None:
            errors.append("Invalid price format")
        elif price < 0:
            errors.append("Price cannot be negative")
        elif price > self.MAX_PRICE:
            warnings.append("Price seems unusually high")
        elif price == 0:
            warnings.append("Book is marked as free")

        return ValidationResult(is_valid=len(errors) == 0, errors=tuple(errors), warnings=tuple(warnings))


class PagesValidator(Validator):
    """Validates page count."""

    MIN_PAGES = 1
    MAX_PAGES = 50000

    def validate(self, value: Any, book_data: Dict[str, Any]) -> ValidationResult:
        if value is None:
            return ValidationResult(is_valid=True)

        errors: List[str] = []
        warnings: List[str] = []
        pages = parse_int(value)

        if pages is None:
            errors.append("Pages must be a number")
        elif pages < self.MIN_PAGES:
            errors.append(f"Pages must be at least {self.MIN_PAGES}")
        elif pages > self.MAX_PAGES:
            warnings.append("Page count seems unusually high")

        return ValidationResult(is_valid=len(errors) == 0, errors=tuple(errors), warnings=tuple(warnings))


class GenreValidator(Validator):
    """Validates book genre(s)."""

    def validate(self, value: Any, book_data: Dict[str, Any]) -> ValidationResult:
        if not value:
            return ValidationResult(is_valid=True)

        errors: List[str] = []
        warnings: List[str] = []

        if isinstance(value, str):
            genres = [value]
        elif isinstance(value, list):
            genres = value
        else:
            return ValidationResult(is_valid=False, errors=("Genre must be a string or list of strings",))

        for i, genre in enumerate(genres):
            if not isinstance(genre, str):
                errors.append(f"Genre {i + 1} must be a string")
            elif genre.lower() not in VALID_GENRES:
                warnings.append(f"Unknown genre: {genre}")

        return ValidationResult(is_valid=len(errors) == 0, errors=tuple(errors), warnings=tuple(warnings))


class LanguageValidator(Validator):
    """Validates language code."""

    def validate(self, value: Any, book_data: Dict[str, Any]) -> ValidationResult:
        if not value:
            return ValidationResult(is_valid=True)

        if not isinstance(value, str):
            return ValidationResult(is_valid=False, errors=("Language must be a string",))

        warnings: List[str] = []
        if value.lower() not in VALID_LANGUAGES:
            warnings.append(f"Unsupported language code: {value}")

        return ValidationResult(is_valid=True, warnings=tuple(warnings))


# =============================================================================
# Utility Functions
# =============================================================================

def parse_date(date_str: str) -> Optional[datetime]:
    """Parse a date string using multiple formats.

    Args:
        date_str: Date string to parse

    Returns:
        Parsed datetime or None if parsing fails
    """
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def parse_price(value: Any) -> Optional[Decimal]:
    """Parse a price value from string or number.

    Uses Decimal for precise monetary calculations.

    Args:
        value: Price value (string, int, or float)

    Returns:
        Decimal price or None if parsing fails
    """
    try:
        if isinstance(value, Decimal):
            return value
        if isinstance(value, (int, float)):
            return Decimal(str(value))
        if isinstance(value, str):
            cleaned = PRICE_CLEANUP_PATTERN.sub('', value)
            return Decimal(cleaned)
    except (InvalidOperation, ValueError, TypeError):
        return None
    return None


def parse_int(value: Any) -> Optional[int]:
    """Parse an integer value from string or number.

    Args:
        value: Integer value (string or int)

    Returns:
        Integer or None if parsing fails
    """
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None


def format_title_case(title: str) -> str:
    """Format a title using proper title case rules.

    Args:
        title: Title string to format

    Returns:
        Title-cased string
    """
    words = title.strip().split()
    if not words:
        return ""

    formatted = []

    for i, word in enumerate(words):
        if i == 0 or i == len(words) - 1 or word.lower() not in TITLE_SMALL_WORDS:
            formatted.append(word.capitalize())
        else:
            formatted.append(word.lower())

    return " ".join(formatted)


def normalize_isbn(isbn: str) -> Tuple[Optional[str], Optional[str]]:
    """Normalize ISBN and return (isbn_10, isbn_13) tuple.

    Args:
        isbn: ISBN string (may contain dashes/spaces)

    Returns:
        Tuple of (isbn_10, isbn_13) with None for the format not present
    """
    clean = isbn.replace("-", "").replace(" ", "")
    if len(clean) == 10:
        return (clean, None)
    elif len(clean) == 13:
        return (None, clean)
    return (None, None)


def sanitize_text(text: str) -> str:
    """Sanitize text to prevent XSS and injection attacks.

    Args:
        text: Text to sanitize

    Returns:
        HTML-escaped text
    """
    return html.escape(text)


# =============================================================================
# Book Processor
# =============================================================================

def _create_default_validators() -> Dict[str, Validator]:
    """Factory function to create fresh validator instances."""
    return {
        "title": TitleValidator(),
        "author": AuthorValidator(),
        "isbn": ISBNValidator(),
        "publication_date": DateValidator(),
        "price": PriceValidator(),
        "pages": PagesValidator(),
        "genre": GenreValidator(),
        "language": LanguageValidator(),
    }


class BookProcessor:
    """Processes book data with validation and formatting.

    Example:
        >>> processor = BookProcessor()
        >>> result = processor.process({"title": "My Book", "author": "John Doe"})
        >>> if result.success:
        ...     print(result.data)
    """

    def __init__(self, options: Optional[Dict[str, Any]] = None):
        """Initialize the processor with optional configuration.

        Args:
            options: Configuration options including:
                - title_case (bool): Apply title case formatting (default: True)
                - truncate_description (bool): Truncate long descriptions
                - description_max_length (int): Max description length (default: 500)
                - sanitize_output (bool): HTML-escape text fields (default: True)
        """
        self.options = options or {}
        self.validators = _create_default_validators()
        logger.debug("BookProcessor initialized with options: %s", self.options)

    def process(self, book_data: Dict[str, Any]) -> ProcessingResult:
        """Process book data through validation and formatting pipeline.

        Args:
            book_data: Dictionary containing book information

        Returns:
            ProcessingResult with success status, errors, warnings, and processed data
        """
        logger.info("Processing book data")

        if not book_data:
            logger.warning("Empty book data received")
            return ProcessingResult(success=False, errors=("Book data is required",))

        if not isinstance(book_data, dict):
            logger.error("Invalid book data type: %s", type(book_data))
            return ProcessingResult(success=False, errors=("Book data must be a dictionary",))

        # Run validation
        all_errors, all_warnings = self._validate(book_data)

        if all_errors:
            logger.warning("Validation failed with %d errors", len(all_errors))
            return ProcessingResult(success=False, errors=tuple(all_errors), warnings=tuple(all_warnings))

        # Format and enrich data
        try:
            processed = self._format(book_data)
        except Exception as e:
            logger.exception("Error during formatting: %s", e)
            return ProcessingResult(success=False, errors=(f"Formatting error: {str(e)}",))

        logger.info("Book processing completed successfully")
        return ProcessingResult(success=True, errors=(), warnings=tuple(all_warnings), data=processed)

    def _validate(self, book_data: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Run all validators and collect errors/warnings."""
        all_errors: List[str] = []
        all_warnings: List[str] = []

        for field_name, validator in self.validators.items():
            value = book_data.get(field_name)
            try:
                result = validator.validate(value, book_data)
                all_errors.extend(result.errors)
                all_warnings.extend(result.warnings)
            except Exception as e:
                logger.exception("Validator %s raised exception: %s", field_name, e)
                all_errors.append(f"Validation error for {field_name}: {str(e)}")

        return all_errors, all_warnings

    def _format(self, book_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format and enrich validated book data."""
        processed: Dict[str, Any] = {}
        sanitize = self.options.get("sanitize_output", True)

        # Title
        title = book_data["title"].strip()
        if self.options.get("title_case", True):
            title = format_title_case(title)
        processed["title"] = sanitize_text(title) if sanitize else title

        # Authors
        author = book_data["author"]
        if isinstance(author, str):
            authors = [author.strip()]
        else:
            authors = [a.strip() for a in author]
        processed["authors"] = [sanitize_text(a) if sanitize else a for a in authors]

        # ISBN
        if book_data.get("isbn"):
            processed["isbn_10"], processed["isbn_13"] = normalize_isbn(str(book_data["isbn"]))

        # Publication date
        if book_data.get("publication_date"):
            parsed = parse_date(book_data["publication_date"])
            if parsed:
                processed["publication_date"] = parsed.strftime("%Y-%m-%d")
                processed["publication_year"] = parsed.year

        # Price - use Decimal for precision
        if "price" in book_data:
            price = parse_price(book_data["price"])
            if price is not None:
                processed["price"] = float(round(price, 2))
                processed["price_formatted"] = f"${processed['price']:.2f}"

        # Pages
        if "pages" in book_data:
            pages = parse_int(book_data["pages"])
            if pages is not None:
                processed["pages"] = pages

        # Genres
        if book_data.get("genre"):
            genre = book_data["genre"]
            if isinstance(genre, str):
                processed["genres"] = [genre.lower()]
            else:
                processed["genres"] = [g.lower() for g in genre if isinstance(g, str)]

        # Language
        if book_data.get("language"):
            processed["language"] = book_data["language"].lower()

        # Description
        if book_data.get("description"):
            desc = self._format_description(book_data["description"])
            processed["description"] = sanitize_text(desc) if sanitize else desc

        # Metadata
        processed["processed_at"] = datetime.utcnow().isoformat() + "Z"
        processed["processor_version"] = "2.1.0"

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
    """Process book data with validation, formatting, and enrichment.

    This is a backwards-compatible wrapper around the BookProcessor class.

    Args:
        book_data: Dictionary containing book information
        options: Optional processing configuration

    Returns:
        Dictionary with success, errors, warnings, and data fields
    """
    processor = BookProcessor(options)
    result = processor.process(book_data)

    return {
        "success": result.success,
        "errors": list(result.errors),
        "warnings": list(result.warnings),
        "data": result.data,
    }


if __name__ == "__main__":
    # Configure logging for demo
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

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
