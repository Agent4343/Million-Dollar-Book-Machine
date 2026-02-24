"""
Book Export Module

Generates professional book formats:
- Word Document (.docx)
- EPUB for Kindle/eReaders
- Markdown
"""

import html
import io
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone


def _get_best_chapters(project, chapters_override: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    if isinstance(chapters_override, list):
        return chapters_override
    chapters = project.manuscript.get("chapters", [])
    if isinstance(chapters, list):
        return chapters
    return []


def _front_matter_defaults(project) -> Dict[str, Any]:
    c = project.user_constraints or {}
    year = c.get("copyright_year") or datetime.now(timezone.utc).year
    return {
        "author_name": c.get("author_name") or c.get("pen_name") or "Author Name",
        "publisher_name": c.get("publisher_name") or "",
        "copyright_year": year,
        "include_disclaimer": bool(c.get("include_disclaimer", True)),
        "disclaimer_text": c.get("disclaimer_text") or "This is a work of fiction. Names, characters, businesses, places, events, and incidents are either the products of the author’s imagination or used in a fictitious manner.",
        "isbn": c.get("isbn") or "",
        "rights_statement": c.get("rights_statement") or "All rights reserved.",
        "dedication": (c.get("dedication") or "").strip(),
        "cover_image_path": c.get("cover_image_path") or "",
    }


def _supplemental_matter(project) -> Dict[str, Any]:
    c = project.user_constraints or {}
    also_by = c.get("also_by") or c.get("also_by_titles") or []
    if isinstance(also_by, str):
        also_by = [t.strip() for t in also_by.split(",") if t.strip()]
    if not isinstance(also_by, list):
        also_by = []
    also_by = [str(t).strip() for t in also_by if str(t).strip()]

    # Pull auto-generated content from publishing_package agent output
    # if user hasn't provided their own.  This closes the gap where the
    # pipeline generates a bio/blurb but it never reaches the export.
    agent_bio = ""
    agent_blurb = ""
    for layer in project.layers.values():
        pp_state = layer.agents.get("publishing_package")
        if pp_state and pp_state.current_output:
            pp = pp_state.current_output.content or {}
            agent_bio = (pp.get("author_bio") or "").strip()
            agent_blurb = (pp.get("blurb") or "").strip()
            break

    return {
        "also_by": also_by,
        "acknowledgements": (c.get("acknowledgements") or "").strip(),
        "about_author": (c.get("about_author") or c.get("about_author_text") or agent_bio).strip(),
        "newsletter_cta": (c.get("newsletter_cta") or "").strip(),
        "newsletter_url": (c.get("newsletter_url") or "").strip(),
        "blurb": (c.get("blurb") or agent_blurb).strip(),
    }


def generate_docx(project, include_outline: bool = False, chapters_override: Optional[List[Dict[str, Any]]] = None) -> bytes:
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

    fm = _front_matter_defaults(project)

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

    # === Copyright / Disclaimer Page (KDP recommended) ===
    copyright_heading = doc.add_heading("Copyright", level=1)
    copyright_heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph()
    cpara = doc.add_paragraph()
    cpara.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cpara.add_run(f"© {fm['copyright_year']} {fm['author_name']}\n{fm['rights_statement']}")
    if fm.get("isbn"):
        doc.add_paragraph().add_run(f"ISBN: {fm['isbn']}")
    if fm.get("publisher_name"):
        doc.add_paragraph().add_run(f"Publisher: {fm['publisher_name']}")
    if fm.get("include_disclaimer"):
        doc.add_paragraph()
        disc = doc.add_paragraph()
        disc.add_run("Disclaimer: ").bold = True
        doc.add_paragraph(fm.get("disclaimer_text", ""))

    doc.add_page_break()

    # === Dedication (optional) ===
    if fm.get("dedication"):
        for _ in range(6):
            doc.add_paragraph()
        ded_para = doc.add_paragraph()
        ded_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        ded_para.add_run(fm["dedication"]).italic = True
        doc.add_page_break()

    sup = _supplemental_matter(project)

    # === Also By (optional) ===
    if sup["also_by"]:
        doc.add_heading("Also By", level=1)
        for t in sup["also_by"]:
            doc.add_paragraph(t)
        doc.add_page_break()

    # Get all agent outputs for use throughout document
    outputs = {}
    for layer in project.layers.values():
        for agent_id, agent_state in layer.agents.items():
            if agent_state.current_output:
                outputs[agent_id] = agent_state.current_output.content

    # === Table of Contents ===
    toc_heading = doc.add_heading('Table of Contents', level=1)

    chapters = _get_best_chapters(project, chapters_override=chapters_override)

    # If no written chapters, use chapter blueprint for TOC
    if not chapters and 'chapter_blueprint' in outputs:
        blueprint = outputs['chapter_blueprint']
        chapter_outline = blueprint.get('chapter_outline', [])
        for ch in chapter_outline:
            ch_num = ch.get('number', '?')
            ch_title = ch.get('title', f'Chapter {ch_num}')
            toc_entry = doc.add_paragraph(f"Chapter {ch_num}: {ch_title}")
            toc_entry.paragraph_format.left_indent = Inches(0.5)
    elif chapters:
        for chapter in sorted(chapters, key=lambda x: x.get('number', 0)):
            ch_num = chapter.get('number', '?')
            ch_title = chapter.get('title', f'Chapter {ch_num}')
            toc_entry = doc.add_paragraph(f"Chapter {ch_num}: {ch_title}")
            toc_entry.paragraph_format.left_indent = Inches(0.5)
    else:
        doc.add_paragraph("No chapters planned yet. Run the pipeline first.")

    doc.add_page_break()

    # === Core Concept Section (always include if available) ===
    if 'concept_definition' in outputs:
        cd = outputs['concept_definition']
        doc.add_heading("Book Concept", level=1)

        if cd.get('one_line_hook'):
            hook_para = doc.add_paragraph()
            hook_para.add_run("Hook: ").bold = True
            hook_para.add_run(cd['one_line_hook'])

        if cd.get('elevator_pitch'):
            doc.add_paragraph()
            pitch_para = doc.add_paragraph()
            pitch_para.add_run("Elevator Pitch: ").bold = True
            doc.add_paragraph(cd['elevator_pitch'])

        if cd.get('core_promise'):
            cp = cd['core_promise']
            doc.add_paragraph()
            doc.add_paragraph(f"Transformation: {cp.get('transformation', 'N/A')}")
            doc.add_paragraph(f"Emotional Payoff: {cp.get('emotional_payoff', 'N/A')}")

        doc.add_page_break()

    # === Character Section (always include if available) ===
    if 'character_architecture' in outputs:
        ca = outputs['character_architecture']
        doc.add_heading("Characters", level=1)

        if ca.get('protagonist_profile'):
            pp = ca['protagonist_profile']
            doc.add_heading("Protagonist", level=2)
            doc.add_paragraph(f"Name: {pp.get('name', 'Unknown')}")
            doc.add_paragraph(f"Role: {pp.get('role', 'N/A')}")
            if pp.get('traits'):
                doc.add_paragraph(f"Traits: {', '.join(pp['traits'])}")
            if pp.get('backstory_wound'):
                doc.add_paragraph(f"Wound: {pp.get('backstory_wound')}")

        if ca.get('protagonist_arc'):
            pa = ca['protagonist_arc']
            doc.add_heading("Character Arc", level=2)
            doc.add_paragraph(f"Starting State: {pa.get('starting_state', 'N/A')}")
            doc.add_paragraph(f"Transformation: {pa.get('transformation', 'N/A')}")
            doc.add_paragraph(f"Ending State: {pa.get('ending_state', 'N/A')}")

        if ca.get('supporting_cast'):
            doc.add_heading("Supporting Cast", level=2)
            for char in ca['supporting_cast'][:5]:
                doc.add_paragraph(f"• {char.get('name', '?')}: {char.get('function', 'N/A')}")

        doc.add_page_break()

    # === Chapters ===
    if chapters:
        doc.add_heading("Manuscript", level=1)
        doc.add_page_break()

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

    # === Chapter Blueprint (if no written chapters) ===
    elif 'chapter_blueprint' in outputs:
        doc.add_heading("Chapter Outline", level=1)
        doc.add_paragraph("Note: Use the Chapter Writer to generate full prose for each chapter.")
        doc.add_paragraph()

        blueprint = outputs['chapter_blueprint']
        chapter_outline = blueprint.get('chapter_outline', [])

        for ch in chapter_outline:
            ch_num = ch.get('number', '?')
            ch_title = ch.get('title', f'Chapter {ch_num}')

            doc.add_heading(f"Chapter {ch_num}: {ch_title}", level=2)

            if ch.get('chapter_goal'):
                goal_para = doc.add_paragraph()
                goal_para.add_run("Goal: ").bold = True
                goal_para.add_run(ch['chapter_goal'])

            if ch.get('opening_hook'):
                hook_para = doc.add_paragraph()
                hook_para.add_run("Opening: ").bold = True
                hook_para.add_run(ch['opening_hook'])

            if ch.get('closing_hook'):
                close_para = doc.add_paragraph()
                close_para.add_run("Closing: ").bold = True
                close_para.add_run(ch['closing_hook'])

            # Scenes
            if ch.get('scenes'):
                doc.add_paragraph()
                scenes_para = doc.add_paragraph()
                scenes_para.add_run("Scenes:").bold = True
                for scene in ch['scenes']:
                    doc.add_paragraph(
                        f"  {scene.get('scene_number', '?')}. {scene.get('scene_question', 'Scene')} "
                        f"[{scene.get('location', 'Location')}]"
                    )

            doc.add_paragraph()
    else:
        doc.add_heading("No Content Yet", level=1)
        doc.add_paragraph("Run the pipeline to generate your book outline, then use the Chapter Writer to create full chapters.")

    # === Back Matter (standard order: About Author, Acknowledgements, Newsletter) ===
    if sup.get("about_author"):
        doc.add_heading("About the Author", level=1)
        doc.add_paragraph(sup["about_author"])
        doc.add_page_break()

    if sup.get("acknowledgements"):
        doc.add_heading("Acknowledgements", level=1)
        doc.add_paragraph(sup["acknowledgements"])
        doc.add_page_break()

    if sup.get("newsletter_cta") or sup.get("newsletter_url"):
        doc.add_heading("Stay in Touch", level=1)
        if sup.get("newsletter_cta"):
            doc.add_paragraph(sup["newsletter_cta"])
        if sup.get("newsletter_url"):
            doc.add_paragraph(sup["newsletter_url"])
        doc.add_page_break()

    # Save to bytes
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


def _load_cover_image(path: str) -> Optional[bytes]:
    """Load a cover image from disk. Returns None if not found."""
    import os
    if not path or not os.path.isfile(path):
        return None
    try:
        with open(path, "rb") as f:
            return f.read()
    except Exception:
        return None


def _cover_media_type(path: str) -> str:
    """Guess media type from file extension."""
    lower = path.lower()
    if lower.endswith(".png"):
        return "image/png"
    if lower.endswith(".gif"):
        return "image/gif"
    if lower.endswith(".webp"):
        return "image/webp"
    return "image/jpeg"  # default for .jpg/.jpeg/.tiff


# Kindle-optimised CSS — used by all XHTML pages in the EPUB.
_KINDLE_CSS = '''\
@page { margin: 0; }
body {
    font-family: Georgia, "Times New Roman", serif;
    margin: 1em 1.2em;
    line-height: 1.65;
    orphans: 2;
    widows: 2;
}
h1 {
    text-align: center;
    margin-top: 2em;
    margin-bottom: 1.5em;
    font-size: 1.6em;
    font-weight: bold;
    page-break-before: always;
}
h1.title-page {
    font-size: 2.5em;
    margin-top: 35%;
    page-break-before: auto;
}
p {
    text-indent: 1.5em;
    margin: 0.2em 0;
}
p.first, p.no-indent {
    text-indent: 0;
}
p.scene-break {
    text-align: center;
    text-indent: 0;
    margin: 1.5em 0;
    font-size: 1.2em;
    letter-spacing: 0.3em;
}
p.center {
    text-align: center;
    text-indent: 0;
}
p.dedication {
    text-align: center;
    text-indent: 0;
    font-style: italic;
    margin-top: 35%;
}
div.copyright {
    margin-top: 20%;
    text-align: center;
    font-size: 0.9em;
    line-height: 1.8;
}
ul.also-by {
    list-style: none;
    padding: 0;
    text-align: center;
}
ul.also-by li {
    margin: 0.4em 0;
    font-style: italic;
}
span.dropcap {
    float: left;
    font-size: 3.2em;
    line-height: 0.8;
    padding-right: 0.08em;
    margin-top: 0.05em;
    font-weight: bold;
}
'''


def _make_xhtml(title: str, body: str, css_file: str = "style/kindle.css") -> str:
    """Wrap body content in an HTML page with CSS link.

    ebooklib handles the EPUB-specific XML serialisation itself, so we
    provide simple HTML here (no xmlns or XML prolog) which its internal
    lxml parser can consume without issues.
    """
    return (
        '<html>\n'
        f'<head><title>{html.escape(title)}</title>'
        f'<link rel="stylesheet" type="text/css" href="{css_file}"/>'
        '</head>\n'
        f'<body>\n{body}\n</body>\n</html>'
    )


def _text_to_html_paragraphs(text: str, first_para_dropcap: bool = True) -> str:
    """Convert plain text to styled HTML paragraphs with scene-break handling."""
    if not text:
        return ""
    paragraphs = text.split('\n\n')
    parts: List[str] = []
    is_first_body_para = True
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if para in ('* * *', '---', '***', '~ ~ ~', '###'):
            parts.append('<p class="scene-break">* * *</p>')
            is_first_body_para = True  # next para after break gets no indent
            continue
        escaped = html.escape(para)
        if is_first_body_para:
            if first_para_dropcap and len(escaped) > 1 and escaped[0].isalpha():
                escaped = f'<span class="dropcap">{escaped[0]}</span>{escaped[1:]}'
            parts.append(f'<p class="first">{escaped}</p>')
            is_first_body_para = False
        else:
            parts.append(f'<p>{escaped}</p>')
    return '\n'.join(parts)


def generate_epub(project, chapters_override: Optional[List[Dict[str, Any]]] = None) -> bytes:
    """
    Generate a publication-quality EPUB file from the project manuscript.
    Compatible with Kindle Direct Publishing and other eReaders.

    Features:
    - Cover image embedding (KDP requirement)
    - Proper front matter (title, copyright, dedication, also-by)
    - Kindle-optimised CSS (drop caps, scene breaks, orphan/widow control)
    - Auto-populated back matter from publishing_package agent output
    - NCX + Nav for full device compatibility

    Args:
        project: BookProject instance
        chapters_override: Optional list of chapter dicts to use instead of project.manuscript

    Returns:
        bytes: The .epub file content
    """
    from ebooklib import epub

    book = epub.EpubBook()
    fm = _front_matter_defaults(project)
    sup = _supplemental_matter(project)
    genre = project.user_constraints.get('genre', 'Fiction').replace('_', ' ').title()

    # --- Metadata ---
    book.set_identifier(f'million-dollar-book-{project.project_id}')
    book.set_title(project.title)
    book.set_language('en')
    book.add_author(fm["author_name"])
    if project.user_constraints.get('description'):
        book.add_metadata('DC', 'description', project.user_constraints['description'])
    elif sup.get("blurb"):
        book.add_metadata('DC', 'description', sup["blurb"])
    book.add_metadata('DC', 'subject', genre)
    book.add_metadata('DC', 'date', str(fm["copyright_year"]))
    if fm.get("publisher_name"):
        book.add_metadata('DC', 'publisher', fm["publisher_name"])

    # --- CSS ---
    kindle_css = epub.EpubItem(
        uid="style_kindle",
        file_name="style/kindle.css",
        media_type="text/css",
        content=_KINDLE_CSS.encode("utf-8"),
    )
    book.add_item(kindle_css)

    # --- Cover Image ---
    cover_data = _load_cover_image(fm.get("cover_image_path", ""))
    if cover_data:
        cover_path = fm["cover_image_path"]
        ext = cover_path.rsplit(".", 1)[-1].lower() if "." in cover_path else "jpg"
        cover_filename = f"images/cover.{ext}"
        # set_cover() creates both the image item and cover XHTML page
        # internally — do NOT add a manual EpubItem or cover page, as that
        # creates duplicates that corrupt the EPUB manifest.
        book.set_cover(cover_filename, cover_data)

    # --- Spine items (ordered reading list) ---
    # epub_chapters collects all spine pages; toc_items collects only those
    # that should appear in the reader-facing Table of Contents.
    epub_chapters: List[Any] = []
    toc_items: List[Any] = []

    # Title page
    title_body = (
        f'<h1 class="title-page">{html.escape(project.title)}</h1>\n'
        f'<p class="center" style="margin-top:2em;font-style:italic;">{html.escape(genre)}</p>\n'
        f'<p class="center" style="margin-top:1em;">{html.escape(fm["author_name"])}</p>'
    )
    title_page = epub.EpubHtml(title="Title Page", file_name="title.xhtml", lang="en")
    title_page.content = _make_xhtml(project.title, title_body)
    book.add_item(title_page)
    epub_chapters.append(title_page)

    # Copyright page
    cr_parts = [
        f'<p>Copyright &copy; {fm["copyright_year"]} {html.escape(fm["author_name"])}</p>',
        f'<p>{html.escape(fm["rights_statement"])}</p>',
    ]
    if fm.get("publisher_name"):
        cr_parts.append(f'<p>Published by {html.escape(fm["publisher_name"])}</p>')
    if fm.get("isbn"):
        cr_parts.append(f'<p>ISBN: {html.escape(str(fm["isbn"]))}</p>')
    if fm.get("include_disclaimer"):
        cr_parts.append(f'<p style="margin-top:1.5em;font-size:0.85em;">{html.escape(fm["disclaimer_text"])}</p>')
    copyright_page = epub.EpubHtml(title="Copyright", file_name="copyright.xhtml", lang="en")
    copyright_page.content = _make_xhtml("Copyright", f'<div class="copyright">{"".join(cr_parts)}</div>')
    book.add_item(copyright_page)
    epub_chapters.append(copyright_page)

    # Dedication (optional)
    if fm.get("dedication"):
        ded_page = epub.EpubHtml(title="Dedication", file_name="dedication.xhtml", lang="en")
        ded_page.content = _make_xhtml("Dedication",
            f'<p class="dedication">{html.escape(fm["dedication"])}</p>')
        book.add_item(ded_page)
        epub_chapters.append(ded_page)

    # Content Warnings / Trigger Warnings (optional — standard for dark romance)
    content_warnings = project.user_constraints.get("content_warnings", "")
    if content_warnings:
        if isinstance(content_warnings, list):
            warnings_html = "".join(f"<li>{html.escape(w)}</li>" for w in content_warnings)
        else:
            # Split comma/semicolon-separated string into list items
            items = [w.strip() for w in str(content_warnings).replace(";", ",").split(",") if w.strip()]
            warnings_html = "".join(f"<li>{html.escape(w)}</li>" for w in items)
        cw_page = epub.EpubHtml(title="Content Warnings", file_name="content_warnings.xhtml", lang="en")
        cw_page.content = _make_xhtml("Content Warnings",
            '<h1>Content Warnings</h1>\n'
            '<p style="margin-bottom:1em;">This book contains themes and scenes that some readers may find '
            'triggering. Please review the list below before continuing.</p>\n'
            f'<ul style="line-height:1.8;">{warnings_html}</ul>\n'
            '<p style="margin-top:1.5em;font-style:italic;">Reader discretion is advised. '
            'This is a work of fiction.</p>')
        book.add_item(cw_page)
        epub_chapters.append(cw_page)

    # Also By (optional)
    if sup["also_by"]:
        items_html = "".join(f"<li>{html.escape(t)}</li>" for t in sup["also_by"])
        also_page = epub.EpubHtml(title="Also By", file_name="also_by.xhtml", lang="en")
        also_page.content = _make_xhtml("Also By",
            f'<h1>Also by {html.escape(fm["author_name"])}</h1>\n<ul class="also-by">{items_html}</ul>')
        book.add_item(also_page)
        epub_chapters.append(also_page)

    # --- Chapters ---
    chapters = _get_best_chapters(project, chapters_override=chapters_override)
    if chapters:
        for chapter in sorted(chapters, key=lambda x: x.get('number', 0)):
            ch_num = chapter.get('number', '?')
            ch_title = chapter.get('title', f'Chapter {ch_num}')
            ch = epub.EpubHtml(
                title=f'Chapter {ch_num}: {ch_title}',
                file_name=f'chapter_{ch_num}.xhtml',
                lang='en',
            )
            text = chapter.get('text', '')
            heading = f'<h1>Chapter {ch_num}<br/><span style="font-size:0.7em;font-weight:normal;">{html.escape(ch_title)}</span></h1>\n'
            if text:
                body_html = heading + _text_to_html_paragraphs(text, first_para_dropcap=True)
            else:
                body_html = heading + '<p class="first"><em>Chapter content not yet written.</em></p>'
            ch.content = _make_xhtml(f"Chapter {ch_num}", body_html)
            book.add_item(ch)
            epub_chapters.append(ch)
            toc_items.append(ch)
    else:
        empty_ch = epub.EpubHtml(title="No Content", file_name="empty.xhtml", lang="en")
        empty_ch.content = _make_xhtml("No Content",
            '<h1>No Chapters Written</h1><p class="first">Use the pipeline to generate your manuscript.</p>')
        book.add_item(empty_ch)
        epub_chapters.append(empty_ch)
        toc_items.append(empty_ch)

    # --- Back matter (standard order: About Author, Acknowledgements, Newsletter CTA) ---
    if sup.get("about_author"):
        about = epub.EpubHtml(title="About the Author", file_name="about_author.xhtml", lang="en")
        about.content = _make_xhtml("About the Author",
            f'<h1>About the Author</h1>\n<p class="first">{html.escape(sup["about_author"])}</p>')
        book.add_item(about)
        epub_chapters.append(about)
        toc_items.append(about)

    if sup.get("acknowledgements"):
        acks = epub.EpubHtml(title="Acknowledgements", file_name="acknowledgements.xhtml", lang="en")
        acks.content = _make_xhtml("Acknowledgements",
            f'<h1>Acknowledgements</h1>\n<p class="first">{html.escape(sup["acknowledgements"])}</p>')
        book.add_item(acks)
        epub_chapters.append(acks)

    if sup.get("newsletter_cta") or sup.get("newsletter_url"):
        parts: List[str] = []
        if sup.get("newsletter_cta"):
            parts.append(f'<p class="center">{html.escape(sup["newsletter_cta"])}</p>')
        if sup.get("newsletter_url"):
            url = html.escape(sup["newsletter_url"])
            parts.append(f'<p class="center"><a href="{url}">{url}</a></p>')
        news = epub.EpubHtml(title="Stay in Touch", file_name="newsletter.xhtml", lang="en")
        news.content = _make_xhtml("Stay in Touch", f'<h1>Stay in Touch</h1>\n{"".join(parts)}')
        book.add_item(news)
        epub_chapters.append(news)

    # --- Link CSS to every page ---
    for page in epub_chapters:
        page.add_item(kindle_css)

    # --- Table of Contents ---
    # Only chapters and major back matter appear in the TOC — front matter
    # (copyright, dedication, also-by) is excluded for a professional look.
    book.toc = tuple(toc_items)

    # --- Navigation ---
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # --- Spine ---
    spine_items: List[Any] = ['nav']
    if cover_data:
        spine_items.insert(0, 'cover')
    spine_items.extend(epub_chapters)
    book.spine = spine_items

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
    total = 0
    for ch in chapters:
        wc = ch.get('word_count', 0)
        if not wc and ch.get('text'):
            wc = len(ch['text'].split())
        total += wc
    return total


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
