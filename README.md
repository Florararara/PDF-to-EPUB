# PDF-to-EPUB

Convert scanned Chinese PDFs into EPUBs:

1. Render scanned PDF pages into images.
2. OCR pages with PaddleOCR.
3. Clean OCR line breaks, page markers, and spacing.
4. Reconstruct readable paragraphs.
5. Write a valid EPUB without `ebooklib`.

The tool can also clean existing OCR `.txt` files and convert cleaned text into EPUB.

## Important Python version note

For PDF OCR with PaddleOCR, use Python 3.10, 3.11, or 3.12. Avoid Python 3.13/3.14 because PaddleOCR/PaddlePaddle may not support them yet.

## Install

```bash
cd PDF-to-EPUB

python3.12 -m venv .venv
source .venv/bin/activate

python3 -m pip install --upgrade pip
python3 -m pip install -e ".[pdf]"
```

If `python3.12` is unavailable, install Python 3.12 first, then recreate the virtual environment.

## From scanned PDF to EPUB

```bash
zh-ocr-epub pdf \
  --input ~/Desktop/book.pdf \
  --output ~/Desktop/book.epub \
  --title "Book Title" \
  --author "Author Name"
```

This creates:

```text
book.ocr.txt
book.cleaned.txt
book.epub
```

## Test only a few pages first

```bash
zh-ocr-epub pdf \
  --input ~/Desktop/book.pdf \
  --output ~/Desktop/test.epub \
  --title "Book Title" \
  --author "Author Name" \
  --start-page 1 \
  --end-page 10
```

## Adjust paragraph reconstruction

If paragraphs are too long:

```bash
zh-ocr-epub pdf \
  --input ~/Desktop/book.pdf \
  --output ~/Desktop/book.epub \
  --title "Book Title" \
  --author "Author Name" \
  --target-chars 320 \
  --short-ratio 0.9
```

If paragraphs are too fragmented:

```bash
zh-ocr-epub pdf \
  --input ~/Desktop/book.pdf \
  --output ~/Desktop/book.epub \
  --title "Book Title" \
  --author "Author Name" \
  --target-chars 560 \
  --short-ratio 0.7
```

Default values:

```text
--target-chars 420
--short-ratio 0.82
```

## Keep page images for debugging

```bash
zh-ocr-epub pdf \
  --input ~/Desktop/book.pdf \
  --output ~/Desktop/book.epub \
  --title "Book Title" \
  --author "Author Name" \
  --keep-images \
  --image-dir ~/Desktop/ocr_pages
```

## Existing OCR text to EPUB

```bash
zh-ocr-epub \
  --input ~/Desktop/book_ocr.txt \
  --output ~/Desktop/book.epub \
  --title "Book Title" \
  --author "Author Name"
```

## Clean text only

```bash
zh-ocr-epub clean \
  --input ~/Desktop/book_ocr.txt \
  --output ~/Desktop/book.cleaned.txt
```

## EPUB from cleaned text only

```bash
zh-ocr-epub epub \
  --input ~/Desktop/book.cleaned.txt \
  --output ~/Desktop/book.epub \
  --title "Book Title" \
  --author "Author Name"
```
