from pathlib import Path
import re
import time
import traceback

import numpy as np
from pypdf import PdfReader
from paddleocr import PaddleOCR
import fitz  # PyMuPDF - pure pip package, no poppler/system binary needed
from PIL import Image


# ============================================================
# PaddleOCR
# ============================================================

ocr = PaddleOCR(
    lang="en",
    ocr_version="PP-OCRv4",
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=True,
)


# ============================================================
# Basic text cleaning
# ============================================================

def clean_basic_text(text: str) -> str:
    """
    Basic cleanup without destroying useful line structure.
    """

    if not text:
        return ""

    # Normalize different dash characters
    text = text.replace("–", "-")
    text = text.replace("—", "-")
    text = text.replace("−", "-")

    # Normalize bullets
    text = text.replace("•", "•")

    # Remove carriage returns
    text = text.replace("\r", "\n")

    # Remove trailing spaces
    text = re.sub(r"[ \t]+", " ", text)

    # Remove spaces around newlines
    text = re.sub(r" *\n *", "\n", text)

    # Collapse excessive empty lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ============================================================
# Strip "Print to PDF" browser artifacts
# ============================================================
#
# Resumes that were exported by printing an HTML page to PDF
# (Chrome/Edge "Print to PDF") get a page header/footer stamped
# on EVERY page by the browser itself, e.g.:
#
#   8/15/2025, 2:24 PM Abdulrahman Burham - CV      <- header
#   file:///C:/Users/abdul/Downloads/pdf_cv.html 1/2 <- footer
#
# pypdf extracts these lines like any other text, and because
# they land at arbitrary points in the middle of the document
# (wherever a page break happens to fall), they get swallowed
# into whatever resume section is active at that point - which
# is why unrelated fragments like a timestamp or a file:// path
# show up inside "skills" or "languages". This is independent of
# which resume it is, so we strip it generically rather than
# hardcoding this one candidate's name/file path.

PRINT_ARTIFACT_PATTERNS = [

    # Footer: "file:///C:/Users/.../whatever.html" (+ optional
    # trailing "1/2" page counter). Never legitimate resume
    # content, so the whole line is dropped.
    re.compile(r"^.*\bfile:///\S+.*$", re.MULTILINE | re.IGNORECASE),

    # Header: a full "<date>, <time> AM/PM <tab title>" line, e.g.
    # "8/15/2025, 2:24 PM Abdulrahman Burham - CV".
    re.compile(
        r"^\s*\d{1,2}/\d{1,2}/\d{2,4},?\s*\d{1,2}:\d{2}\s*[AaPp]\.?[Mm]\.?\b.*$",
        re.MULTILINE,
    ),

    # Browser "Print to PDF" page footer: "Name - page 1 of 2".
    # Appears on every page when printing an HTML resume to PDF.
    re.compile(
        r"^\s*[A-Za-z][A-Za-z\s.'-]*\s*-\s*page\s+\d+\s+of\s+\d+\s*$",
        re.MULTILINE | re.IGNORECASE,
    ),
]

# Sometimes upstream whitespace collapsing has already chewed off
# the leading date, leaving only a fragment like
# "24 PM Abdulrahman Burham - CV" glued onto real content. Catch
# that leftover "<time> AM/PM <Title Case words> - CV" shape
# wherever it appears in the text, not just at line start.
PRINT_ARTIFACT_FRAGMENT_PATTERN = re.compile(
    r"\b\d{0,2}:?\d{2}\s*[AaPp]\.?[Mm]\.?\s+"
    r"(?:[A-Z][a-zA-Z]*\s+){1,4}-\s*CV\b"
)


def strip_print_artifacts(text: str) -> str:
    """
    Remove browser "Print to PDF" page headers/footers.

    Runs on RAW (pre-whitespace-collapsed) text so the full
    date+time pattern is still intact and easy to recognize.
    """

    if not text:
        return ""

    for pattern in PRINT_ARTIFACT_PATTERNS:
        text = pattern.sub("", text)

    text = PRINT_ARTIFACT_FRAGMENT_PATTERN.sub("", text)

    return text


# ============================================================
# Fix character-spaced PDF extraction
# ============================================================

def fix_character_spaced_text(text: str) -> str:
    """
    Fix PDFs where pypdf extracts text like:

        Y O U S E F A H M E D
        A i E n g i n e e r
        P y t h o n , N u m P y , P a n d a s

    into:

        YOUSEF AHMED
        Ai Engineer
        Python, NumPy, Pandas

    This function works line-by-line so normal text is preserved.
    """

    if not text:
        return ""

    lines = text.splitlines()
    fixed_lines = []

    for raw_line in lines:

        line = raw_line.strip()

        if not line:
            fixed_lines.append("")
            continue

        # ----------------------------------------------------
        # Detect character-spaced lines
        # ----------------------------------------------------

        tokens = line.split()

        # Example:
        # ["Y", "O", "U", "S", "E", "F", "A", "H", "M", "E", "D"]
        #
        # But we should NOT blindly join every line.
        #
        # Detect if most tokens are single characters.
        # ----------------------------------------------------

        if len(tokens) >= 3:

            single_char_count = sum(
                1 for token in tokens
                if len(token) == 1
            )

            ratio = single_char_count / len(tokens)

            # Strong character-spacing signal
            if ratio >= 0.70:

                rebuilt = ""

                for token in tokens:

                    # Single letters are usually separated
                    if len(token) == 1:
                        rebuilt += token

                    else:
                        # If a multi-character token appears,
                        # preserve it with a space.
                        if rebuilt and not rebuilt.endswith(" "):
                            rebuilt += " "

                        rebuilt += token

                line = rebuilt

        fixed_lines.append(line)

    text = "\n".join(fixed_lines)

    return clean_basic_text(text)


# ============================================================
# Smart spacing fixes
# ============================================================

def fix_common_pdf_spacing(text: str) -> str:
    """
    Fix common OCR / PDF extraction spacing issues.
    """

    if not text:
        return ""

    # --------------------------------------------------------
    # Email
    # --------------------------------------------------------

    # y o u s e f a h m e d 8 7 a 6 @ g m a i l . c o m
    # ->
    # youse fahmed87a6@gmail.com
    #
    # The character-spaced fixer should already handle most
    # cases. These rules are additional protection.
    # --------------------------------------------------------

    text = re.sub(
        r"(?i)([a-z0-9])\s*@\s*([a-z0-9])",
        r"\1@\2",
        text
    )

    text = re.sub(
        r"(?i)([a-z0-9])\s*\.\s*([a-z])",
        r"\1.\2",
        text
    )

    # --------------------------------------------------------
    # Phone numbers
    # --------------------------------------------------------

    text = re.sub(
        r"(?<!\d)(\d)\s+(\d)(?=\s+\d)",
        r"\1\2",
        text
    )

    # --------------------------------------------------------
    # Common technical terms
    # --------------------------------------------------------

    replacements = {
        "P y t o r c h": "PyTorch",
        "T e n s o r F l o w": "TensorFlow",
        "F a s t A P I": "FastAPI",
        "O p e n C V": "OpenCV",
        "P a n d a s": "Pandas",
        "N u m P y": "NumPy",
        "S c i k i t - l e a r n": "Scikit-learn",
        "M a t p l o t l i b": "Matplotlib",
        "S e a b o r n": "Seaborn",
        "L a n g C h a i n": "LangChain",
        "L a n g G r a p h": "LangGraph",
        "M a g F a c e": "MagFace",
        "J a v a S c r i p t": "JavaScript",
        "H T M L": "HTML",
        "C S S": "CSS",
        "G i t H u b": "GitHub",
        "G i t": "Git",
        "R A G": "RAG",
        "L L M": "LLM",
        "L L M s": "LLMs",
        "A I": "AI",
        "M L": "ML",
        "N L P": "NLP",
        "C N N": "CNN",
        "R N N": "RNN",
        "L S T M": "LSTM",
        "A N N": "ANN",
        "S Q L": "SQL",
        "V P S": "VPS",
        "n 8 n": "n8n",
        "P y t h o n": "Python",
        "D o c k e r": "Docker",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # --------------------------------------------------------
    # Fix excessive spaces around punctuation
    # --------------------------------------------------------

    text = re.sub(r"\s+@", "@", text)
    text = re.sub(r"@\s+", "@", text)

    text = re.sub(r"\s+\.", ".", text)
    text = re.sub(r"\.\s+", ".", text)

    text = re.sub(r"\s*,\s*", ", ", text)

    # Keep hyphens readable
    text = re.sub(r"\s*-\s*", " - ", text)

    # Fix duplicate spaces
    text = re.sub(r"[ \t]{2,}", " ", text)

    return clean_basic_text(text)


# ============================================================
# Final text normalization
# ============================================================

def normalize_resume_text(text: str) -> str:
    """
    Complete normalization pipeline.
    """

    if not text:
        return ""

    # Strip browser print-header/footer noise FIRST, while the
    # date/time pattern is still intact - clean_basic_text below
    # collapses whitespace and can otherwise fragment it.
    text = strip_print_artifacts(text)

    text = clean_basic_text(text)

    text = fix_character_spaced_text(text)

    text = fix_common_pdf_spacing(text)

    # Catch any fragment that only became recognizable after
    # spacing fixes ran (e.g. a character-spaced timestamp).
    text = strip_print_artifacts(text)

    # --------------------------------------------------------
    # Remove repeated Replit footer
    # --------------------------------------------------------

    text = re.sub(
        r"(M a d e\s+w i t h\s+R e p l i t)+",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"(Made\s+with\s+Replit)+",
        "",
        text,
        flags=re.IGNORECASE
    )

    # --------------------------------------------------------
    # Remove isolated page numbers
    # --------------------------------------------------------

    text = re.sub(
        r"\n\s*\d+\s*\n",
        "\n",
        text
    )

    return clean_basic_text(text)


# ============================================================
# TEXT QUALITY / BROKEN TEXT DETECTION
# ============================================================
#
# Problem this solves:
#
#   len(text) >= 100
#
# is NOT enough to decide a PDF's text layer is usable, because
# some PDFs have a text layer like:
#
#       Y O U S E F   A H M E D
#       A i   E n g i n e e r
#       0 1 0 0 6 9 4 7 2 6 2
#
# which is long, but garbage. We score the RAW pypdf output
# (before any character-spacing "fix" is attempted) and use
# that score to decide whether to trust pypdf at all or fall
# back to OCR straight away.
# ============================================================

# Score below this -> considered BROKEN_TEXT = True
QUALITY_SCORE_THRESHOLD = 55

# Minimum raw characters required even to consider pypdf usable
MIN_RAW_TEXT_LENGTH = 100

RESUME_SECTION_KEYWORDS = [
    "experience",
    "education",
    "skills",
    "summary",
    "projects",
    "certifications",
    "languages",
    "courses",
    "contact",
    "profile",
    "objective",
]


def analyze_text_quality(text: str) -> dict:
    """
    Score raw extracted text and decide if it looks like normal
    prose or "broken" character-spaced garbage
    (e.g. "Y O U S E F   A H M E D").

    Returns a dict with a numeric score (0-100) and the signals
    used to compute it, plus a final `is_broken` boolean.

    This function is intentionally conservative: it only flags
    text as broken when several independent signals agree, so it
    does not accidentally send clean digital PDFs to OCR.
    """

    result = {
        "score": 0.0,
        "is_broken": True,
        "single_char_ratio": 0.0,
        "broken_line_ratio": 0.0,
        "avg_token_length": 0.0,
        "keyword_hits": 0,
        "has_email": False,
        "has_phone_like": False,
        "reasons": [],
    }

    if not text or not text.strip():
        result["reasons"].append("empty_text")
        return result

    tokens = text.split()

    if not tokens:
        result["reasons"].append("no_tokens")
        return result

    total_tokens = len(tokens)

    # --------------------------------------------------------
    # Signal 1: ratio of single-character alphabetic tokens
    # ("Y O U S E F" -> almost every token has length 1)
    # --------------------------------------------------------

    alpha_single_tokens = [
        t for t in tokens
        if len(t) == 1 and t.isalpha()
    ]

    single_char_ratio = len(alpha_single_tokens) / total_tokens

    result["single_char_ratio"] = round(single_char_ratio, 3)

    # --------------------------------------------------------
    # Signal 2: ratio of LINES that are mostly single-char tokens
    # (line-level view catches cases where only some lines,
    # like the name/title, are broken)
    # --------------------------------------------------------

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    broken_line_count = 0
    checkable_line_count = 0

    for line in lines:

        line_tokens = line.split()

        if len(line_tokens) < 3:
            continue

        checkable_line_count += 1

        single_count = sum(
            1 for t in line_tokens
            if len(t) == 1
        )

        if (single_count / len(line_tokens)) >= 0.6:
            broken_line_count += 1

    broken_line_ratio = (
        broken_line_count / checkable_line_count
        if checkable_line_count else 0.0
    )

    result["broken_line_ratio"] = round(broken_line_ratio, 3)

    # --------------------------------------------------------
    # Signal 3: average token length
    # Normal English resume text averages ~4-6 chars/token.
    # Character-spaced text collapses this toward ~1.
    # --------------------------------------------------------

    avg_token_length = sum(len(t) for t in tokens) / total_tokens

    result["avg_token_length"] = round(avg_token_length, 2)

    # --------------------------------------------------------
    # Signal 4: presence of common resume section keywords
    # (coherence check - real resumes mention these words)
    # --------------------------------------------------------

    lower_text = text.lower()

    keyword_hits = sum(
        1 for kw in RESUME_SECTION_KEYWORDS
        if kw in lower_text
    )

    result["keyword_hits"] = keyword_hits

    # --------------------------------------------------------
    # Signal 5: does a valid-looking email / phone survive
    # as-is? (broken text usually breaks these too)
    # --------------------------------------------------------

    has_email = bool(
        re.search(
            r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
            text
        )
    )

    has_phone_like = bool(
        re.search(r"(?<!\d)\d{9,}(?!\d)", re.sub(r"[\s\-]", "", text))
    )

    result["has_email"] = has_email
    result["has_phone_like"] = has_phone_like

    # --------------------------------------------------------
    # Combine signals into a 0-100 score
    # --------------------------------------------------------

    score = 100.0

    if single_char_ratio >= 0.35:
        penalty = 45
        score -= penalty
        result["reasons"].append(
            f"high_single_char_ratio({single_char_ratio:.2f})"
        )

    if broken_line_ratio >= 0.3:
        penalty = 35
        score -= penalty
        result["reasons"].append(
            f"high_broken_line_ratio({broken_line_ratio:.2f})"
        )

    if avg_token_length < 2.3:
        penalty = 20
        score -= penalty
        result["reasons"].append(
            f"low_avg_token_length({avg_token_length:.2f})"
        )

    if keyword_hits == 0:
        penalty = 10
        score -= penalty
        result["reasons"].append("no_resume_keywords_found")

    if has_email:
        score += 8
        result["reasons"].append("valid_email_found(+)")

    if has_phone_like:
        score += 4
        result["reasons"].append("phone_like_digits_found(+)")

    score = max(0.0, min(100.0, score))

    result["score"] = round(score, 1)
    result["is_broken"] = score < QUALITY_SCORE_THRESHOLD

    return result


# ============================================================
# PDF TEXT EXTRACTION
# ============================================================

def extract_raw_text_with_pypdf(file_path: str) -> str:
    """
    Extract text from a digital PDF with ONLY light cleanup
    (no character-spacing fix, no replacements).

    This raw text is what we run quality/broken-text detection
    against, so the detection sees exactly what pypdf produced.
    """

    reader = PdfReader(file_path)

    pages = []

    for page in reader.pages:

        try:
            page_text = page.extract_text()

            if page_text:
                pages.append(page_text)

        except Exception as e:
            print(f"Failed to extract page: {e}")

    text = "\n".join(pages)

    return clean_basic_text(text)


def extract_text_with_pypdf(file_path: str) -> str:
    """
    Extract text from a normal digital PDF and fully normalize it.

    Kept for backward compatibility / direct use. The main
    pipeline (extract_text_from_pdf) now goes through
    extract_raw_text_with_pypdf + analyze_text_quality first,
    so it can decide whether normalizing pypdf's output is even
    worth trusting, or whether to fall back to OCR instead.
    """

    text = extract_raw_text_with_pypdf(file_path)

    return normalize_resume_text(text)


# ============================================================
# PaddleOCR IMAGE EXTRACTION
# ============================================================

# Large images (e.g. PDF pages rendered at 300 DPI, which can
# easily be 2400-3500px on the long side) are a known cause of
# PaddleOCR crashing or hanging on CPU-only servers. We cap the
# longest side before running OCR. This does not meaningfully
# hurt OCR accuracy for resume text - it just avoids feeding the
# model an unnecessarily huge array.
MAX_OCR_DIMENSION = 2000


def _downscale_for_ocr(image: Image.Image) -> Image.Image:
    """
    Resize an image so its longest side is at most
    MAX_OCR_DIMENSION, preserving aspect ratio. No-op if the
    image is already small enough.
    """

    width, height = image.size
    longest_side = max(width, height)

    if longest_side <= MAX_OCR_DIMENSION:
        return image

    scale = MAX_OCR_DIMENSION / float(longest_side)

    new_size = (
        max(1, int(width * scale)),
        max(1, int(height * scale)),
    )

    return image.resize(new_size, Image.LANCZOS)


def run_ocr_on_image(image) -> str:
    """
    Run PaddleOCR on a PIL image.

    Wrapped in try/except with a full traceback print, because a
    bare/uncaught exception here previously bubbled up as an
    opaque 500 with no diagnostic info. Now, if PaddleOCR itself
    fails (e.g. on an unusually large or malformed page image),
    we log exactly what happened and re-raise a clear error
    instead of a silent crash.
    """

    try:

        image = image.convert("RGB")

        image = _downscale_for_ocr(image)

        image_array = np.array(image)

        print(f"Running OCR on image of size {image.size}...")
        _start = time.perf_counter()

        result = ocr.ocr(
            image_array
        )

        _elapsed = time.perf_counter() - _start
        print(f"OCR inference took {_elapsed:.2f} seconds.")

    except Exception as e:

        print(
            "PaddleOCR failed while processing an image "
            f"(size={getattr(image, 'size', 'unknown')}): {e}"
        )
        traceback.print_exc()

        raise RuntimeError(
            f"PaddleOCR failed on image size={getattr(image, 'size', 'unknown')}: {e}"
        ) from e

    lines = []

    if not result:
        return ""

    for page in result:

        if not page:
            continue

        # ----------------------------------------------------
        # New PaddleOCR (3.x / PaddleX-based) result format:
        # each "page" is a dict-like OCRResult object with a
        # "rec_texts" key holding the recognized strings.
        # ----------------------------------------------------

        try:
            has_rec_texts = "rec_texts" in page
        except TypeError:
            has_rec_texts = False

        if has_rec_texts:

            for text in page.get("rec_texts") or []:
                if text:
                    lines.append(str(text))

            continue

        # ----------------------------------------------------
        # Old PaddleOCR (<3.0) result format: a list of
        # [box, (text, score)] entries.
        # ----------------------------------------------------

        for line in page:

            if len(line) < 2:
                continue

            text_info = line[1]

            if not text_info:
                continue

            text = text_info[0]

            if text:
                lines.append(str(text))

    return "\n".join(lines)


# ============================================================
# IMAGE EXTRACTION
# ============================================================

def extract_text_from_image(file_path: str) -> str:
    """
    Extract text from PNG/JPG/JPEG using PaddleOCR.
    """

    image = Image.open(file_path)

    text = run_ocr_on_image(image)

    return normalize_resume_text(text)


# ============================================================
# PDF PAGES -> IMAGES (no poppler / no system binary required)
# ============================================================

def render_pdf_pages_to_images(file_path: str, dpi: int = 300) -> list:
    """
    Render every page of a PDF to a PIL image using PyMuPDF.

    This replaces pdf2image/poppler on purpose: pdf2image shells
    out to the poppler-utils system binaries (pdftoppm/pdftocairo),
    which must be separately installed at the OS level and were
    missing on the server ("Unable to get page count. Is poppler
    installed and in PATH?"). PyMuPDF is a normal pip package
    (`pip install PyMuPDF`) with the PDF renderer built into the
    wheel itself - nothing to install outside the Python venv.
    """

    doc = fitz.open(str(file_path))

    # PDF page coordinates are at 72 DPI by default, so scale by
    # the ratio to get the requested DPI.
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)

    images = []

    for page in doc:

        pixmap = page.get_pixmap(matrix=matrix)

        image = Image.frombytes(
            "RGB",
            [pixmap.width, pixmap.height],
            pixmap.samples,
        )

        images.append(image)

    doc.close()

    return images


# ============================================================
# SCANNED PDF OCR
# ============================================================

def extract_text_with_ocr(file_path: str) -> str:
    """
    Convert scanned PDF pages to images
    and extract text using PaddleOCR.

    Each page is processed independently: if OCR fails on one
    page, we log the full traceback and continue with the
    remaining pages instead of failing the entire request. We
    only raise if every single page failed (nothing to return).
    """

    try:
        images = render_pdf_pages_to_images(
            file_path,
            dpi=300
        )

    except Exception as e:
        print(f"PyMuPDF failed to render pages: {e}")
        traceback.print_exc()
        raise RuntimeError(
            f"Failed to render PDF pages for OCR: {e}"
        ) from e

    pages = []
    failed_pages = []

    for index, image in enumerate(images):

        print(
            f"OCR processing page {index + 1}/{len(images)}..."
        )

        try:
            page_text = run_ocr_on_image(image)

            if page_text:
                pages.append(page_text)

        except Exception as e:
            print(f"OCR failed on page {index + 1}: {e}")
            failed_pages.append(index + 1)

    if not pages:
        raise RuntimeError(
            "OCR failed on every page of the PDF "
            f"(pages: {failed_pages}). See server logs above "
            "for the underlying PaddleOCR traceback."
        )

    if failed_pages:
        print(
            f"Warning: OCR failed on pages {failed_pages}, "
            "continuing with the pages that succeeded."
        )

    text = "\n".join(pages)

    return normalize_resume_text(text)


# ============================================================
# MAIN EXTRACTION FUNCTION
# ============================================================

def extract_text_from_pdf(file_path: str) -> str:
    """
    Main resume extraction function.

    Supports:

        PDF
        PNG
        JPG
        JPEG
    """

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    extension = file_path.suffix.lower()

    # ========================================================
    # IMAGE
    # ========================================================

    if extension in [".png", ".jpg", ".jpeg"]:

        print("Image detected. Using PaddleOCR...")

        text = extract_text_from_image(
            file_path
        )

        return text

    # ========================================================
    # PDF
    # ========================================================

    if extension == ".pdf":

        print("PDF detected.")

        # ----------------------------------------------------
        # STEP 1: Extract RAW text with pypdf (no fixes applied)
        # ----------------------------------------------------

        raw_text = ""

        try:
            raw_text = extract_raw_text_with_pypdf(file_path)

        except Exception as e:
            print(f"pypdf failed: {e}")
            raw_text = ""

        raw_length = len(raw_text.strip())

        print(f"pypdf extracted {raw_length} raw characters.")

        # ----------------------------------------------------
        # STEP 2: Quality / broken-text check on the RAW text
        # ----------------------------------------------------

        use_pypdf = False

        if raw_length >= MIN_RAW_TEXT_LENGTH:

            quality = analyze_text_quality(raw_text)

            print(
                f"Text quality score: {quality['score']} "
                f"(broken={quality['is_broken']}) "
                f"reasons={quality['reasons']}"
            )

            if not quality["is_broken"]:
                use_pypdf = True
            else:
                print(
                    "Broken / character-spaced text detected "
                    "(e.g. 'Y O U S E F A H M E D' pattern). "
                    "Not trusting pypdf output."
                )

        else:
            print(
                "PDF contains little/no usable text "
                f"(< {MIN_RAW_TEXT_LENGTH} chars)."
            )

        # ----------------------------------------------------
        # STEP 3a: pypdf text is trustworthy -> normalize & use it
        # ----------------------------------------------------

        if use_pypdf:

            print(
                "Digital PDF detected. Using normalized pypdf text."
            )

            normalized = strip_print_artifacts(raw_text)
            normalized = clean_basic_text(normalized)
            normalized = fix_common_pdf_spacing(normalized)
            normalized = strip_print_artifacts(normalized)

            return normalized

        # ----------------------------------------------------
        # STEP 3b: pypdf text is missing/broken -> OCR fallback
        # ----------------------------------------------------

        print("Switching to PaddleOCR...")

        return extract_text_with_ocr(
            file_path
        )

    # ========================================================
    # Unsupported
    # ========================================================

    raise ValueError(
        f"Unsupported file type: {extension}"
    )