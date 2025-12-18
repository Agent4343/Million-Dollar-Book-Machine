"""
Book Processing Module for Million-Dollar-Book-Machine

This module handles book data processing, validation, and formatting.
"""

import re
from datetime import datetime
from typing import Dict, List, Any, Optional


def process_book_data(book_data: Dict[str, Any], options: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Process book data with validation, formatting, and enrichment.

    This function is intentionally complex to demonstrate refactoring opportunities.
    It violates single responsibility principle and has high cyclomatic complexity.
    """
    if options is None:
        options = {}

    result = {"success": False, "errors": [], "warnings": [], "data": None}

    # Validate required fields
    if not book_data:
        result["errors"].append("Book data is required")
        return result

    if "title" not in book_data or not book_data["title"]:
        result["errors"].append("Title is required")
    elif len(book_data["title"]) < 1:
        result["errors"].append("Title must be at least 1 character")
    elif len(book_data["title"]) > 500:
        result["errors"].append("Title must be less than 500 characters")
    else:
        if not re.match(r'^[a-zA-Z0-9\s\-\'\"\:\!\?\.\,]+$', book_data["title"]):
            result["warnings"].append("Title contains special characters that may cause display issues")

    if "author" not in book_data or not book_data["author"]:
        result["errors"].append("Author is required")
    elif isinstance(book_data["author"], str):
        if len(book_data["author"]) < 2:
            result["errors"].append("Author name must be at least 2 characters")
        elif len(book_data["author"]) > 200:
            result["errors"].append("Author name must be less than 200 characters")
    elif isinstance(book_data["author"], list):
        if len(book_data["author"]) == 0:
            result["errors"].append("At least one author is required")
        else:
            for i, author in enumerate(book_data["author"]):
                if not author or len(author) < 2:
                    result["errors"].append(f"Author {i+1} name must be at least 2 characters")
                elif len(author) > 200:
                    result["errors"].append(f"Author {i+1} name must be less than 200 characters")
    else:
        result["errors"].append("Author must be a string or list of strings")

    if "isbn" in book_data and book_data["isbn"]:
        isbn = str(book_data["isbn"]).replace("-", "").replace(" ", "")
        if len(isbn) == 10:
            # Validate ISBN-10
            total = 0
            for i, char in enumerate(isbn):
                if i == 9 and char.upper() == 'X':
                    total += 10
                elif char.isdigit():
                    total += int(char) * (10 - i)
                else:
                    result["errors"].append("Invalid ISBN-10 format")
                    break
            else:
                if total % 11 != 0:
                    result["errors"].append("Invalid ISBN-10 checksum")
        elif len(isbn) == 13:
            # Validate ISBN-13
            if not isbn.isdigit():
                result["errors"].append("ISBN-13 must contain only digits")
            else:
                total = 0
                for i, char in enumerate(isbn):
                    if i % 2 == 0:
                        total += int(char)
                    else:
                        total += int(char) * 3
                if total % 10 != 0:
                    result["errors"].append("Invalid ISBN-13 checksum")
        else:
            result["errors"].append("ISBN must be 10 or 13 characters")

    if "publication_date" in book_data and book_data["publication_date"]:
        date_str = book_data["publication_date"]
        parsed_date = None
        for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y", "%m-%d-%Y", "%m/%d/%Y", "%Y"]:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                break
            except ValueError:
                continue
        if parsed_date is None:
            result["errors"].append("Invalid publication date format")
        elif parsed_date > datetime.now():
            result["warnings"].append("Publication date is in the future")
        elif parsed_date.year < 1450:
            result["warnings"].append("Publication date is before the invention of the printing press")

    if "price" in book_data:
        price = book_data["price"]
        if isinstance(price, str):
            price = price.replace("$", "").replace(",", "").strip()
            try:
                price = float(price)
            except ValueError:
                result["errors"].append("Invalid price format")
                price = None
        if price is not None:
            if price < 0:
                result["errors"].append("Price cannot be negative")
            elif price > 10000:
                result["warnings"].append("Price seems unusually high")
            elif price == 0:
                result["warnings"].append("Book is marked as free")

    if "pages" in book_data:
        pages = book_data["pages"]
        if isinstance(pages, str):
            try:
                pages = int(pages)
            except ValueError:
                result["errors"].append("Pages must be a number")
                pages = None
        if pages is not None:
            if pages < 1:
                result["errors"].append("Pages must be at least 1")
            elif pages > 50000:
                result["warnings"].append("Page count seems unusually high")

    if "genre" in book_data and book_data["genre"]:
        valid_genres = ["fiction", "non-fiction", "mystery", "thriller", "romance",
                       "science-fiction", "fantasy", "biography", "history", "self-help",
                       "children", "young-adult", "horror", "poetry", "drama", "comedy",
                       "adventure", "crime", "literary", "classic"]
        genre = book_data["genre"]
        if isinstance(genre, str):
            if genre.lower() not in valid_genres:
                result["warnings"].append(f"Unknown genre: {genre}")
        elif isinstance(genre, list):
            for g in genre:
                if g.lower() not in valid_genres:
                    result["warnings"].append(f"Unknown genre: {g}")

    if "language" in book_data and book_data["language"]:
        valid_languages = ["en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko",
                          "ar", "hi", "nl", "sv", "no", "da", "fi", "pl", "tr", "he"]
        lang = book_data["language"]
        if isinstance(lang, str):
            if lang.lower() not in valid_languages:
                result["warnings"].append(f"Unsupported language code: {lang}")

    if result["errors"]:
        return result

    # Format and enrich the data
    processed = {}

    # Format title
    title = book_data["title"].strip()
    if options.get("title_case", True):
        words = title.split()
        small_words = ["a", "an", "the", "and", "but", "or", "for", "nor", "on", "at",
                      "to", "from", "by", "of", "in"]
        formatted_words = []
        for i, word in enumerate(words):
            if i == 0 or i == len(words) - 1:
                formatted_words.append(word.capitalize())
            elif word.lower() in small_words:
                formatted_words.append(word.lower())
            else:
                formatted_words.append(word.capitalize())
        processed["title"] = " ".join(formatted_words)
    else:
        processed["title"] = title

    # Format author
    author = book_data["author"]
    if isinstance(author, str):
        processed["authors"] = [author.strip()]
    else:
        processed["authors"] = [a.strip() for a in author]

    # Format ISBN
    if "isbn" in book_data and book_data["isbn"]:
        isbn = str(book_data["isbn"]).replace("-", "").replace(" ", "")
        if len(isbn) == 10:
            processed["isbn_10"] = isbn
            processed["isbn_13"] = None
        else:
            processed["isbn_10"] = None
            processed["isbn_13"] = isbn

    # Format date
    if "publication_date" in book_data and book_data["publication_date"]:
        date_str = book_data["publication_date"]
        for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y", "%m-%d-%Y", "%m/%d/%Y", "%Y"]:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                processed["publication_date"] = parsed_date.strftime("%Y-%m-%d")
                processed["publication_year"] = parsed_date.year
                break
            except ValueError:
                continue

    # Format price
    if "price" in book_data:
        price = book_data["price"]
        if isinstance(price, str):
            price = float(price.replace("$", "").replace(",", "").strip())
        processed["price"] = round(price, 2)
        processed["price_formatted"] = f"${price:.2f}"

    # Copy other fields
    if "pages" in book_data:
        pages = book_data["pages"]
        if isinstance(pages, str):
            pages = int(pages)
        processed["pages"] = pages

    if "genre" in book_data:
        genre = book_data["genre"]
        if isinstance(genre, str):
            processed["genres"] = [genre.lower()]
        else:
            processed["genres"] = [g.lower() for g in genre]

    if "language" in book_data:
        processed["language"] = book_data["language"].lower()

    if "description" in book_data:
        desc = book_data["description"].strip()
        if options.get("truncate_description"):
            max_len = options.get("description_max_length", 500)
            if len(desc) > max_len:
                desc = desc[:max_len-3] + "..."
        processed["description"] = desc

    # Add metadata
    processed["processed_at"] = datetime.now().isoformat()
    processed["processor_version"] = "1.0.0"

    result["success"] = True
    result["data"] = processed

    return result


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
