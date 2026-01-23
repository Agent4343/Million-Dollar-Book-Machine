import io
import unittest
import zipfile

from core.export import generate_epub
from core.orchestrator import Orchestrator


class TestKdpExports(unittest.TestCase):
    def test_epub_includes_optional_pages_when_configured(self):
        orch = Orchestrator(llm_client=None)
        project = orch.create_project(
            "Test Book",
            {
                "genre": "Fiction",
                "author_name": "Test Author",
                "also_by": ["Other Book 1", "Other Book 2"],
                "about_author": "Bio here.",
                "acknowledgements": "Thanks.",
                "newsletter_url": "https://example.com/newsletter",
            },
        )
        # Minimal fake chapter so EPUB includes a chapter
        project.manuscript["chapters"] = [
            {"number": 1, "title": "One", "text": "Hello world", "summary": "Hi", "word_count": 2}
        ]

        epub_bytes = generate_epub(project)
        zf = zipfile.ZipFile(io.BytesIO(epub_bytes))
        names = set(zf.namelist())
        self.assertIn("EPUB/copyright.xhtml", names)
        self.assertIn("EPUB/also_by.xhtml", names)
        self.assertIn("EPUB/about_author.xhtml", names)
        self.assertIn("EPUB/acknowledgements.xhtml", names)
        self.assertIn("EPUB/newsletter.xhtml", names)


if __name__ == "__main__":
    unittest.main()

