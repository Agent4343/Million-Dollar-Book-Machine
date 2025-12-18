"""
Unit tests for the Book Processor module.
"""

import pytest
from decimal import Decimal
from datetime import datetime

from book_processor_refactored import (
    BookProcessor,
    ProcessingResult,
    ValidationResult,
    process_book_data,
    parse_date,
    parse_price,
    parse_int,
    format_title_case,
    normalize_isbn,
    sanitize_text,
    TitleValidator,
    AuthorValidator,
    ISBNValidator,
    DateValidator,
    PriceValidator,
    PagesValidator,
    GenreValidator,
    LanguageValidator,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def valid_book_data():
    """Return valid book data for testing."""
    return {
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


@pytest.fixture
def processor():
    """Return a BookProcessor instance."""
    return BookProcessor()


# =============================================================================
# Utility Function Tests
# =============================================================================

class TestParseDate:
    """Tests for parse_date function."""

    def test_parse_iso_format(self):
        result = parse_date("2023-05-15")
        assert result == datetime(2023, 5, 15)

    def test_parse_slash_format(self):
        result = parse_date("2023/05/15")
        assert result == datetime(2023, 5, 15)

    def test_parse_year_only(self):
        result = parse_date("1925")
        assert result == datetime(1925, 1, 1)

    def test_parse_invalid_format(self):
        result = parse_date("not a date")
        assert result is None

    def test_parse_european_format(self):
        result = parse_date("15-05-2023")
        assert result == datetime(2023, 5, 15)


class TestParsePrice:
    """Tests for parse_price function."""

    def test_parse_string_with_dollar(self):
        result = parse_price("$15.99")
        assert result == Decimal("15.99")

    def test_parse_string_with_comma(self):
        result = parse_price("$1,234.56")
        assert result == Decimal("1234.56")

    def test_parse_integer(self):
        result = parse_price(10)
        assert result == Decimal("10")

    def test_parse_float(self):
        result = parse_price(15.99)
        assert result == Decimal("15.99")

    def test_parse_invalid(self):
        result = parse_price("not a price")
        assert result is None

    def test_parse_decimal(self):
        result = parse_price(Decimal("15.99"))
        assert result == Decimal("15.99")


class TestParseInt:
    """Tests for parse_int function."""

    def test_parse_string(self):
        assert parse_int("100") == 100

    def test_parse_integer(self):
        assert parse_int(100) == 100

    def test_parse_invalid(self):
        assert parse_int("not a number") is None

    def test_parse_float_string(self):
        assert parse_int("10.5") is None


class TestFormatTitleCase:
    """Tests for format_title_case function."""

    def test_basic_title(self):
        result = format_title_case("the great gatsby")
        assert result == "The Great Gatsby"

    def test_small_words(self):
        result = format_title_case("war and peace")
        assert result == "War and Peace"

    def test_first_word_small(self):
        result = format_title_case("a tale of two cities")
        assert result == "A Tale of Two Cities"

    def test_last_word_small(self):
        result = format_title_case("what dreams are made of")
        assert result == "What Dreams Are Made Of"

    def test_empty_string(self):
        result = format_title_case("")
        assert result == ""


class TestNormalizeISBN:
    """Tests for normalize_isbn function."""

    def test_isbn13(self):
        isbn_10, isbn_13 = normalize_isbn("978-0743273565")
        assert isbn_10 is None
        assert isbn_13 == "9780743273565"

    def test_isbn10(self):
        isbn_10, isbn_13 = normalize_isbn("0-7432-7356-5")
        assert isbn_10 == "0743273565"
        assert isbn_13 is None

    def test_invalid_length(self):
        isbn_10, isbn_13 = normalize_isbn("123")
        assert isbn_10 is None
        assert isbn_13 is None


class TestSanitizeText:
    """Tests for sanitize_text function."""

    def test_html_escape(self):
        result = sanitize_text("<script>alert('xss')</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_ampersand_escape(self):
        result = sanitize_text("Tom & Jerry")
        assert result == "Tom &amp; Jerry"

    def test_plain_text_unchanged(self):
        result = sanitize_text("Hello World")
        assert result == "Hello World"


# =============================================================================
# Validator Tests
# =============================================================================

class TestTitleValidator:
    """Tests for TitleValidator."""

    def test_valid_title(self):
        validator = TitleValidator()
        result = validator.validate("The Great Gatsby", {})
        assert result.is_valid
        assert len(result.errors) == 0

    def test_missing_title(self):
        validator = TitleValidator()
        result = validator.validate(None, {})
        assert not result.is_valid
        assert "Title is required" in result.errors

    def test_empty_title(self):
        validator = TitleValidator()
        result = validator.validate("", {})
        assert not result.is_valid

    def test_title_too_long(self):
        validator = TitleValidator()
        result = validator.validate("x" * 501, {})
        assert not result.is_valid
        assert any("500" in e for e in result.errors)

    def test_title_with_special_chars(self):
        validator = TitleValidator()
        result = validator.validate("Title @#$%", {})
        assert result.is_valid  # Still valid but with warning
        assert len(result.warnings) > 0

    def test_non_string_title(self):
        validator = TitleValidator()
        result = validator.validate(123, {})
        assert not result.is_valid
        assert "must be a string" in result.errors[0]


class TestAuthorValidator:
    """Tests for AuthorValidator."""

    def test_valid_author(self):
        validator = AuthorValidator()
        result = validator.validate("John Doe", {})
        assert result.is_valid

    def test_missing_author(self):
        validator = AuthorValidator()
        result = validator.validate(None, {})
        assert not result.is_valid

    def test_author_too_short(self):
        validator = AuthorValidator()
        result = validator.validate("J", {})
        assert not result.is_valid

    def test_author_list(self):
        validator = AuthorValidator()
        result = validator.validate(["John Doe", "Jane Doe"], {})
        assert result.is_valid

    def test_empty_author_list(self):
        validator = AuthorValidator()
        result = validator.validate([], {})
        assert not result.is_valid

    def test_author_list_with_invalid_entry(self):
        validator = AuthorValidator()
        result = validator.validate(["John Doe", 123], {})
        assert not result.is_valid
        assert any("must be a string" in e for e in result.errors)


class TestISBNValidator:
    """Tests for ISBNValidator."""

    def test_valid_isbn13(self):
        validator = ISBNValidator()
        result = validator.validate("978-0743273565", {})
        assert result.is_valid

    def test_valid_isbn10(self):
        validator = ISBNValidator()
        result = validator.validate("0-13-110362-8", {})
        assert result.is_valid

    def test_isbn10_with_x(self):
        validator = ISBNValidator()
        # ISBN-10 with X check digit
        result = validator.validate("0-8044-2957-X", {})
        assert result.is_valid

    def test_invalid_isbn_length(self):
        validator = ISBNValidator()
        result = validator.validate("12345", {})
        assert not result.is_valid

    def test_invalid_isbn_checksum(self):
        validator = ISBNValidator()
        result = validator.validate("978-0743273566", {})  # Wrong checksum
        assert not result.is_valid

    def test_optional_isbn(self):
        validator = ISBNValidator()
        result = validator.validate(None, {})
        assert result.is_valid


class TestPriceValidator:
    """Tests for PriceValidator."""

    def test_valid_price(self):
        validator = PriceValidator()
        result = validator.validate("$15.99", {})
        assert result.is_valid

    def test_negative_price(self):
        validator = PriceValidator()
        result = validator.validate(-5.00, {})
        assert not result.is_valid

    def test_high_price_warning(self):
        validator = PriceValidator()
        result = validator.validate(15000, {})
        assert result.is_valid
        assert len(result.warnings) > 0

    def test_free_book_warning(self):
        validator = PriceValidator()
        result = validator.validate(0, {})
        assert result.is_valid
        assert "free" in result.warnings[0].lower()

    def test_optional_price(self):
        validator = PriceValidator()
        result = validator.validate(None, {})
        assert result.is_valid


class TestGenreValidator:
    """Tests for GenreValidator."""

    def test_valid_genre(self):
        validator = GenreValidator()
        result = validator.validate("fiction", {})
        assert result.is_valid
        assert len(result.warnings) == 0

    def test_unknown_genre_warning(self):
        validator = GenreValidator()
        result = validator.validate("unknown-genre", {})
        assert result.is_valid  # Still valid, but with warning
        assert len(result.warnings) > 0

    def test_genre_list(self):
        validator = GenreValidator()
        result = validator.validate(["fiction", "mystery"], {})
        assert result.is_valid

    def test_non_string_genre_in_list(self):
        validator = GenreValidator()
        result = validator.validate(["fiction", 123], {})
        assert not result.is_valid


# =============================================================================
# BookProcessor Tests
# =============================================================================

class TestBookProcessor:
    """Tests for BookProcessor class."""

    def test_process_valid_book(self, valid_book_data, processor):
        result = processor.process(valid_book_data)
        assert result.success
        assert result.data is not None
        assert result.data["title"] == "The Great Gatsby"

    def test_process_empty_data(self, processor):
        result = processor.process({})
        assert not result.success
        # Empty dict triggers validation which finds missing required fields
        assert any("required" in e.lower() for e in result.errors)

    def test_process_none_data(self, processor):
        result = processor.process(None)
        assert not result.success
        assert "Book data is required" in result.errors

    def test_process_non_dict_data(self, processor):
        result = processor.process("not a dict")
        assert not result.success
        assert "must be a dictionary" in result.errors[0]

    def test_sanitize_output_enabled(self, valid_book_data):
        book_data = valid_book_data.copy()
        book_data["title"] = "Book <script>alert('xss')</script>"
        processor = BookProcessor({"sanitize_output": True})
        result = processor.process(book_data)
        assert "&lt;script&gt;" in result.data["title"]

    def test_sanitize_output_disabled(self, valid_book_data):
        book_data = valid_book_data.copy()
        book_data["title"] = "Book <test>"
        processor = BookProcessor({"sanitize_output": False})
        result = processor.process(book_data)
        assert "<test>" in result.data["title"]

    def test_title_case_option(self, valid_book_data):
        processor = BookProcessor({"title_case": False})
        result = processor.process(valid_book_data)
        assert result.data["title"] == "the great gatsby"

    def test_description_truncation(self, valid_book_data):
        book_data = valid_book_data.copy()
        book_data["description"] = "x" * 600
        processor = BookProcessor({
            "truncate_description": True,
            "description_max_length": 100
        })
        result = processor.process(book_data)
        assert len(result.data["description"]) == 100
        assert result.data["description"].endswith("...")

    def test_processed_metadata(self, valid_book_data, processor):
        result = processor.process(valid_book_data)
        assert "processed_at" in result.data
        assert "processor_version" in result.data
        assert result.data["processed_at"].endswith("Z")

    def test_price_formatting(self, valid_book_data, processor):
        result = processor.process(valid_book_data)
        assert result.data["price"] == 15.99
        assert result.data["price_formatted"] == "$15.99"

    def test_authors_normalized(self, valid_book_data, processor):
        result = processor.process(valid_book_data)
        assert result.data["authors"] == ["F. Scott Fitzgerald"]

    def test_multiple_authors(self, valid_book_data, processor):
        book_data = valid_book_data.copy()
        book_data["author"] = ["Author One", "Author Two"]
        result = processor.process(book_data)
        assert len(result.data["authors"]) == 2


# =============================================================================
# Integration Tests
# =============================================================================

class TestProcessBookDataFunction:
    """Tests for the process_book_data backwards-compatible function."""

    def test_returns_dict(self, valid_book_data):
        result = process_book_data(valid_book_data)
        assert isinstance(result, dict)
        assert "success" in result
        assert "errors" in result
        assert "warnings" in result
        assert "data" in result

    def test_errors_as_list(self):
        result = process_book_data({})
        assert isinstance(result["errors"], list)

    def test_warnings_as_list(self, valid_book_data):
        result = process_book_data(valid_book_data)
        assert isinstance(result["warnings"], list)


# =============================================================================
# Edge Case Tests
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_whitespace_only_title(self, processor):
        result = processor.process({"title": "   ", "author": "Test Author"})
        assert not result.success

    def test_unicode_title(self, processor):
        result = processor.process({
            "title": "Les Misérables",
            "author": "Victor Hugo"
        })
        # Should have warning about special characters
        assert result.success or len(result.warnings) > 0

    def test_very_old_publication_date(self, processor):
        result = processor.process({
            "title": "Ancient Text",
            "author": "Unknown",
            "publication_date": "1400"
        })
        assert result.success
        assert any("printing press" in w.lower() for w in result.warnings)

    def test_future_publication_date(self, processor):
        result = processor.process({
            "title": "Future Book",
            "author": "Future Author",
            "publication_date": "2099-01-01"
        })
        assert result.success
        assert any("future" in w.lower() for w in result.warnings)

    def test_max_pages(self, processor):
        result = processor.process({
            "title": "Long Book",
            "author": "Prolific Author",
            "pages": "60000"
        })
        assert result.success
        assert any("high" in w.lower() for w in result.warnings)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
