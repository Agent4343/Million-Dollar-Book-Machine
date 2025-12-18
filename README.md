# Million-Dollar-Book-Machine

A book metadata processor with validation, formatting, and a web interface. Deployable to Vercel as a private site.

## Features

- Validate book metadata (title, author, ISBN, dates, prices, etc.)
- ISBN-10 and ISBN-13 checksum validation
- Title case formatting with smart handling of small words
- XSS protection via HTML sanitization
- RESTful API with batch processing support
- Modern web interface

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the API locally
uvicorn api.index:app --reload --port 3000

# Open http://localhost:3000 in your browser
```

### Deploy to Vercel

1. **Install Vercel CLI** (if not already installed):
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**:
   ```bash
   vercel login
   ```

3. **Deploy**:
   ```bash
   vercel
   ```

4. **Make it Private** (in Vercel Dashboard):
   - Go to your project settings
   - Navigate to "Deployment Protection"
   - Enable "Vercel Authentication" to make it private

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/api` | GET | API information |
| `/api/process` | POST | Process a single book |
| `/api/batch` | POST | Process multiple books |
| `/api/genres` | GET | List valid genres |
| `/api/languages` | GET | List valid language codes |

### Example Request

```bash
curl -X POST https://your-site.vercel.app/api/process \
  -H "Content-Type: application/json" \
  -d '{
    "book": {
      "title": "the great gatsby",
      "author": "F. Scott Fitzgerald",
      "isbn": "978-0743273565",
      "publication_date": "1925",
      "price": "$15.99",
      "pages": "180",
      "genre": ["fiction", "classic"],
      "language": "en"
    },
    "options": {
      "title_case": true,
      "sanitize_output": true
    }
  }'
```

### Example Response

```json
{
  "success": true,
  "errors": [],
  "warnings": [],
  "data": {
    "title": "The Great Gatsby",
    "authors": ["F. Scott Fitzgerald"],
    "isbn_10": null,
    "isbn_13": "9780743273565",
    "publication_date": "1925-01-01",
    "publication_year": 1925,
    "price": 15.99,
    "price_formatted": "$15.99",
    "pages": 180,
    "genres": ["fiction", "classic"],
    "language": "en",
    "processed_at": "2024-01-15T10:30:00.000000Z",
    "processor_version": "2.1.0"
  }
}
```

## Validation Rules

| Field | Rules |
|-------|-------|
| Title | Required, 1-500 chars, warns on special characters |
| Author | Required, 2-200 chars per author |
| ISBN | Optional, validates ISBN-10/13 checksum |
| Publication Date | Optional, multiple formats supported |
| Price | Optional, cannot be negative |
| Pages | Optional, must be positive integer |
| Genre | Optional, warns on unknown genres |
| Language | Optional, warns on unsupported codes |

## Project Structure

```
Million-Dollar-Book-Machine/
├── api/
│   └── index.py              # FastAPI serverless function
├── public/
│   └── index.html            # Web interface
├── book_processor_refactored.py  # Core processing logic
├── test_book_processor.py    # Unit tests (73 tests)
├── requirements.txt          # Python dependencies
├── vercel.json              # Vercel configuration
└── README.md
```

## Running Tests

```bash
pip install pytest
pytest test_book_processor.py -v
```

## License

MIT
