from __future__ import annotations

import io
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pdfplumber
from docx import Document

from .models import SectionChunk


@dataclass
class PageText:
    number: int
    text: str


class UnsupportedFileTypeError(ValueError):
    pass


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\t+", " ", text)
    text = re.sub(r"[ \xa0]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_text_pages_from_marked_text(text: str) -> list[PageText]:
    normalized = normalize_text(text)
    marker = re.compile(r"\[\[PAGE\s+(\d+)\]\]", re.IGNORECASE)
    matches = list(marker.finditer(normalized))
    if not matches:
        return [PageText(number=1, text=normalized)] if normalized else []

    pages: list[PageText] = []
    for index, match in enumerate(matches):
        page_number = int(match.group(1))
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(normalized)
        chunk = normalize_text(normalized[start:end])
        if chunk:
            pages.append(PageText(number=page_number, text=chunk))
    return pages


def parse_pdf_bytes(file_bytes: bytes) -> list[PageText]:
    pages: list[PageText] = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for idx, page in enumerate(pdf.pages, start=1):
            text = normalize_text(page.extract_text() or "")
            pages.append(PageText(number=idx, text=text))
    return pages


def parse_docx_bytes(file_bytes: bytes) -> list[PageText]:
    document = Document(io.BytesIO(file_bytes))
    paragraphs = [p.text for p in document.paragraphs if p.text and p.text.strip()]
    text = normalize_text("\n\n".join(paragraphs))
    return [PageText(number=1, text=text)] if text else []


def parse_image_bytes(file_bytes: bytes) -> list[PageText]:
    try:
        from PIL import Image
        import pytesseract
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "OCR dependencies are not installed. Install Pillow and pytesseract, and ensure the Tesseract binary is available."
        ) from exc

    image = Image.open(io.BytesIO(file_bytes))
    text = normalize_text(pytesseract.image_to_string(image))
    return [PageText(number=1, text=text)] if text else []


def parse_upload(file_name: str, file_bytes: bytes) -> tuple[str, list[PageText], dict[str, str]]:
    suffix = Path(file_name).suffix.lower()
    notes: dict[str, str] = {}

    if suffix == ".pdf":
        pages = parse_pdf_bytes(file_bytes)
        if not any(page.text.strip() for page in pages):
            notes["ocr_status"] = (
                "No embedded PDF text was detected. This prototype can OCR image files directly; scanned PDFs require adding an OCR step such as Docling, OCRmyPDF, or pdf-to-image + Tesseract."
            )
        return "pdf", pages, notes
    if suffix == ".docx":
        return "docx", parse_docx_bytes(file_bytes), notes
    if suffix in {".txt", ".md"}:
        text = file_bytes.decode("utf-8", errors="ignore")
        return "txt", extract_text_pages_from_marked_text(text), notes
    if suffix in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}:
        return "image", parse_image_bytes(file_bytes), notes

    raise UnsupportedFileTypeError(
        f"Unsupported file type '{suffix or 'unknown'}'. Upload PDF, DOCX, TXT, MD, or an image file for OCR."
    )


def is_heading(line: str) -> bool:
    stripped = line.strip()
    if not stripped or len(stripped) > 140:
        return False
    if re.match(r"^(Schedule|Exhibit|Appendix)\s+[A-Za-z0-9-]+", stripped, re.IGNORECASE):
        return True
    if re.match(r"^(Section\s+)?\d+(\.\d+){0,4}[\.)]?\s+[A-Z][A-Za-z0-9,&/()\- ]+$", stripped):
        return True
    if stripped.isupper() and 1 <= len(stripped.split()) <= 10:
        return True
    if stripped.endswith(":") and 1 <= len(stripped.split()) <= 10:
        return True
    return False


def infer_contract_type(text: str, file_name: str) -> str:
    combined = f"{file_name}\n{text[:1000]}".lower()
    if "master services agreement" in combined or re.search(r"\bmsa\b", combined):
        return "MSA"
    if "statement of work" in combined or re.search(r"\bsow\b", combined):
        return "SOW"
    if "non-disclosure" in combined or re.search(r"\bnda\b", combined):
        return "NDA"
    if "vendor agreement" in combined:
        return "Vendor Agreement"
    if "license agreement" in combined:
        return "License Agreement"
    return "Contract"


def infer_chunk_metadata(heading: str, text: str) -> dict[str, str]:
    combined = f"{heading} {text}".lower()
    clause_type = "general"
    mapping = [
        ("renewal", ["renew", "term"]),
        ("pricing", ["fee", "pricing", "price", "invoice"]),
        ("payment", ["pay", "invoice", "net ", "receipt"]),
        ("sla", ["service level", "availability", "uptime", "incident"]),
        ("liability", ["liability", "indemn", "damages"]),
        ("termination", ["terminate", "termination", "breach"]),
        ("governing_law", ["governed by", "governing law"]),
        ("data_processing", ["personal data", "data processing", "privacy"]),
    ]
    for name, hints in mapping:
        if any(hint in combined for hint in hints):
            clause_type = name
            break
    return {"clause_hint": clause_type}


def split_long_text(text: str, max_chars: int = 1000) -> list[str]:
    text = normalize_text(text)
    if len(text) <= max_chars:
        return [text] if text else []

    paragraphs = [p.strip() for p in re.split(r"\n\n+", text) if p.strip()]
    if not paragraphs:
        paragraphs = [text]

    parts: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if not current:
            current = paragraph
        elif len(current) + 2 + len(paragraph) <= max_chars:
            current = f"{current}\n\n{paragraph}"
        else:
            parts.append(current)
            current = paragraph
    if current:
        parts.append(current)

    if all(len(part) <= max_chars for part in parts):
        return parts

    sentence_parts: list[str] = []
    for part in parts:
        if len(part) <= max_chars:
            sentence_parts.append(part)
            continue
        sentences = re.split(r"(?<=[.!?])\s+", part)
        buffer = ""
        for sentence in sentences:
            if not buffer:
                buffer = sentence
            elif len(buffer) + 1 + len(sentence) <= max_chars:
                buffer = f"{buffer} {sentence}"
            else:
                sentence_parts.append(buffer)
                buffer = sentence
        if buffer:
            sentence_parts.append(buffer)
    return sentence_parts


def build_section_chunks(pages: Iterable[PageText], *, max_chars: int = 1000) -> list[SectionChunk]:
    chunks: list[SectionChunk] = []
    current_heading = "Preamble"
    current_lines: list[str] = []
    current_pages: list[int] = []

    def flush_section() -> None:
        nonlocal current_lines, current_pages, current_heading, chunks
        body = normalize_text("\n".join(current_lines))
        if not body:
            current_lines = []
            current_pages = []
            return
        page_start = min(current_pages) if current_pages else None
        page_end = max(current_pages) if current_pages else page_start
        for part_index, part_text in enumerate(split_long_text(body, max_chars=max_chars), start=1):
            chunk_id = f"chunk-{len(chunks) + 1:03d}"
            heading = current_heading if len(body) <= max_chars else f"{current_heading} (part {part_index})"
            chunks.append(
                SectionChunk(
                    id=chunk_id,
                    heading=heading,
                    page_start=page_start,
                    page_end=page_end,
                    text=part_text,
                    metadata=infer_chunk_metadata(current_heading, part_text),
                )
            )
        current_lines = []
        current_pages = []

    for page in pages:
        if not page.text.strip():
            continue
        for raw_line in page.text.split("\n"):
            line = raw_line.strip()
            if not line:
                current_lines.append("")
                if page.number not in current_pages:
                    current_pages.append(page.number)
                continue
            if is_heading(line) and current_lines:
                flush_section()
                current_heading = line
                current_lines = [line]
                current_pages = [page.number]
            elif is_heading(line) and not current_lines:
                current_heading = line
                current_lines = [line]
                current_pages = [page.number]
            else:
                current_lines.append(line)
                if page.number not in current_pages:
                    current_pages.append(page.number)

    flush_section()
    return chunks
