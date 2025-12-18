"""
Book Export Module

Generates professional book formats:
- Word Document (.docx)
- EPUB for Kindle/eReaders
- Markdown
"""

import io
import re
from typing import Dict, Any, List, Optional
from datetime import datetime


def generate_docx(project, include_outline: bool = False) -> bytes:
    """
    Generate a Word document from the project manuscript.

    Args:
        project: BookProject instance
        include_outline: Whether to include the development outline

    Returns:
        bytes: The .docx file content
    """
    from docx import Document
    from docx.shared import Pt, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.style import WD_STYLE_TYPE

    doc = Document()

    # Set up styles
    styles = doc.styles

    # Title style
    title_style = styles['Title']
    title_style.font.size = Pt(28)
    title_style.font.bold = True

    # Heading 1 for chapters
    h1_style = styles['Heading 1']
    h1_style.font.size = Pt(18)
    h1_style.font.bold = True

    # Normal paragraph style
    normal_style = styles['Normal']
    normal_style.font.size = Pt(12)
    normal_style.font.name = 'Times New Roman'

    # === Title Page ===
    title_para = doc.add_paragraph()
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_para.add_run(project.title)
    title_run.font.size = Pt(36)
    title_run.font.bold = True

    # Add some space
    for _ in range(3):
        doc.add_paragraph()

    # Subtitle/description if available
    if project.user_constraints.get('description'):
        subtitle = doc.add_paragraph()
        subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
        desc_text = project.user_constraints['description'][:200]
        if len(project.user_constraints['description']) > 200:
            desc_text += '...'
        subtitle.add_run(desc_text).italic = True

    # Genre and word count
    for _ in range(5):
        doc.add_paragraph()

    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    genre = project.user_constraints.get('genre', 'Fiction').replace('_', ' ').title()
    meta.add_run(f"Genre: {genre}")

    # Page break after title
    doc.add_page_break()

    # === Table of Contents placeholder ===
    toc_heading = doc.add_heading('Table of Contents', level=1)

    chapters = project.manuscript.get('chapters', [])
    if chapters:
        for chapter in sorted(chapters, key=lambda x: x.get('number', 0)):
            ch_num = chapter.get('number', '?')
            ch_title = chapter.get('title', f'Chapter {ch_num}')
            toc_entry = doc.add_paragraph(f"Chapter {ch_num}: {ch_title}")
            toc_entry.paragraph_format.left_indent = Inches(0.5)
    else:
        doc.add_paragraph("No chapters written yet.")

    doc.add_page_break()

    # === Chapters ===
    if chapters:
        for chapter in sorted(chapters, key=lambda x: x.get('number', 0)):
            ch_num = chapter.get('number', '?')
            ch_title = chapter.get('title', f'Chapter {ch_num}')

            # Chapter heading
            doc.add_heading(f"Chapter {ch_num}: {ch_title}", level=1)

            # Chapter content
            text = chapter.get('text', '')
            if text:
                # Split into paragraphs and add each
                paragraphs = text.split('\n\n')
                for para_text in paragraphs:
                    para_text = para_text.strip()
                    if para_text:
                        # Handle scene breaks
                        if para_text in ['* * *', '---', '***']:
                            scene_break = doc.add_paragraph()
                            scene_break.alignment = WD_ALIGN_PARAGRAPH.CENTER
                            scene_break.add_run('* * *')
                        else:
                            para = doc.add_paragraph(para_text)
                            para.paragraph_format.first_line_indent = Inches(0.5)
            else:
                doc.add_paragraph("[Chapter content not yet written]").italic = True

            # Page break between chapters
            doc.add_page_break()
    else:
        doc.add_paragraph("No chapters have been written yet.")
        doc.add_paragraph("Use the Chapter Writer to generate content from your outline.")

    # === Optional Outline Section ===
    if include_outline:
        doc.add_page_break()
        doc.add_heading("Development Outline", level=1)

        # Get agent outputs
        outputs = {}
        for layer in project.layers.values():
            for agent_id, agent_state in layer.agents.items():
                if agent_state.current_output:
                    outputs[agent_id] = agent_state.current_output.content

        # Core concept
        if 'concept_definition' in outputs:
            cd = outputs['concept_definition']
            doc.add_heading("Core Concept", level=2)
            if cd.get('one_line_hook'):
                doc.add_paragraph(f"Hook: {cd['one_line_hook']}")
            if cd.get('elevator_pitch'):
                doc.add_paragraph(cd['elevator_pitch'])

        # Character info
        if 'character_architecture' in outputs:
            ca = outputs['character_architecture']
            doc.add_heading("Characters", level=2)
            if ca.get('protagonist_profile'):
                pp = ca['protagonist_profile']
                doc.add_paragraph(f"Protagonist: {pp.get('name', 'Unknown')}")
                doc.add_paragraph(f"Role: {pp.get('role', 'N/A')}")

    # Save to bytes
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


def generate_epub(project) -> bytes:
    """
    Generate an EPUB file from the project manuscript.
    Compatible with Kindle and other eReaders.

    Args:
        project: BookProject instance

    Returns:
        bytes: The .epub file content
    """
    from ebooklib import epub

    book = epub.EpubBook()

    # Set metadata
    book.set_identifier(f'million-dollar-book-{project.project_id}')
    book.set_title(project.title)
    book.set_language('en')

    # Add author (placeholder - could be made configurable)
    book.add_author('Author Name')

    # Add description
    if project.user_constraints.get('description'):
        book.add_metadata('DC', 'description', project.user_constraints['description'])

    # Genre as subject
    genre = project.user_constraints.get('genre', 'Fiction').replace('_', ' ').title()
    book.add_metadata('DC', 'subject', genre)

    # Create chapters
    chapters = project.manuscript.get('chapters', [])
    epub_chapters = []

    # Title page
    title_page = epub.EpubHtml(title='Title Page', file_name='title.xhtml', lang='en')
    title_page.content = f'''
    <html>
    <head><title>{project.title}</title></head>
    <body>
        <div style="text-align: center; margin-top: 30%;">
            <h1 style="font-size: 2.5em;">{project.title}</h1>
            <p style="margin-top: 2em; font-style: italic;">{genre}</p>
        </div>
    </body>
    </html>
    '''
    book.add_item(title_page)
    epub_chapters.append(title_page)

    if chapters:
        for chapter in sorted(chapters, key=lambda x: x.get('number', 0)):
            ch_num = chapter.get('number', '?')
            ch_title = chapter.get('title', f'Chapter {ch_num}')

            # Create chapter
            ch = epub.EpubHtml(
                title=f'Chapter {ch_num}: {ch_title}',
                file_name=f'chapter_{ch_num}.xhtml',
                lang='en'
            )

            # Format chapter content
            text = chapter.get('text', '')
            if text:
                # Convert text to HTML paragraphs
                paragraphs = text.split('\n\n')
                html_content = f'<h1>Chapter {ch_num}: {ch_title}</h1>\n'

                for para in paragraphs:
                    para = para.strip()
                    if para:
                        # Handle scene breaks
                        if para in ['* * *', '---', '***']:
                            html_content += '<p style="text-align: center; margin: 2em 0;">* * *</p>\n'
                        else:
                            # Escape HTML entities
                            para = para.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                            html_content += f'<p style="text-indent: 1.5em; margin: 0.5em 0;">{para}</p>\n'
            else:
                html_content = f'''
                <h1>Chapter {ch_num}: {ch_title}</h1>
                <p><em>Chapter content not yet written.</em></p>
                '''

            ch.content = f'''
            <html>
            <head><title>Chapter {ch_num}</title></head>
            <body>
                {html_content}
            </body>
            </html>
            '''

            book.add_item(ch)
            epub_chapters.append(ch)
    else:
        # No chapters yet
        empty_ch = epub.EpubHtml(title='No Content', file_name='empty.xhtml', lang='en')
        empty_ch.content = '''
        <html>
        <head><title>No Content</title></head>
        <body>
            <h1>No Chapters Written</h1>
            <p>Use the Chapter Writer to generate content from your outline.</p>
        </body>
        </html>
        '''
        book.add_item(empty_ch)
        epub_chapters.append(empty_ch)

    # Define Table of Contents
    book.toc = tuple(epub_chapters)

    # Add navigation files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Define CSS style
    style = '''
    body {
        font-family: Georgia, serif;
        margin: 1em;
        line-height: 1.6;
    }
    h1 {
        text-align: center;
        margin-bottom: 1.5em;
        font-size: 1.5em;
    }
    p {
        text-indent: 1.5em;
        margin: 0.5em 0;
    }
    '''
    nav_css = epub.EpubItem(
        uid="style_nav",
        file_name="style/nav.css",
        media_type="text/css",
        content=style
    )
    book.add_item(nav_css)

    # Create spine
    book.spine = ['nav'] + epub_chapters

    # Write to bytes
    buffer = io.BytesIO()
    epub.write_epub(buffer, book)
    buffer.seek(0)
    return buffer.getvalue()


def generate_kindle_mobi(project) -> Optional[bytes]:
    """
    Generate a MOBI file for Kindle.
    Note: This requires kindlegen or calibre's ebook-convert to be installed.
    Returns None if conversion tools aren't available.

    For now, we'll just return the EPUB since modern Kindles support EPUB,
    and users can use Calibre to convert if needed.
    """
    # MOBI generation typically requires external tools
    # For simplicity, we recommend using the EPUB and converting with Calibre
    # or Amazon's Kindle Previewer
    return None


def get_word_count(project) -> int:
    """Calculate total word count of written chapters."""
    chapters = project.manuscript.get('chapters', [])
    return sum(ch.get('word_count', 0) for ch in chapters)


def get_chapter_summary(project) -> List[Dict[str, Any]]:
    """Get summary of all chapters."""
    chapters = project.manuscript.get('chapters', [])
    return [
        {
            'number': ch.get('number'),
            'title': ch.get('title'),
            'word_count': ch.get('word_count', 0),
            'written': bool(ch.get('text'))
        }
        for ch in sorted(chapters, key=lambda x: x.get('number', 0))
    ]
