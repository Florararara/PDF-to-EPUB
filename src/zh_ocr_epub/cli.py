import argparse
from pathlib import Path
from .cleaner import clean_ocr_text
from .epub_writer import make_epub
from .pdf_ocr import ocr_pdf_to_text


def write_cleaned(input_txt, output_txt, target_chars=420, short_ratio=0.82):
    raw = Path(input_txt).read_text(encoding="utf-8", errors="ignore")
    cleaned = clean_ocr_text(raw, target_chars=target_chars, short_ratio=short_ratio)
    Path(output_txt).write_text(cleaned, encoding="utf-8")
    return len([p for p in cleaned.split("\n\n") if p.strip()])


def cmd_clean(args):
    count = write_cleaned(args.input, args.output, args.target_chars, args.short_ratio)
    print(f"清洗完成：{args.output}")
    print(f"段落数：{count}")


def cmd_epub(args):
    count = make_epub(args.input, args.output, args.title, args.author)
    print(f"EPUB 已生成：{args.output}")
    print(f"段落数：{count}")


def cmd_pdf(args):
    output = Path(args.output)
    raw_txt = Path(args.raw_txt) if args.raw_txt else output.with_suffix(".ocr.txt")
    clean_txt = Path(args.clean_txt) if args.clean_txt else output.with_suffix(".cleaned.txt")

    ocr_pdf_to_text(
        pdf_path=args.input,
        output_txt=str(raw_txt),
        lang=args.lang,
        dpi=args.dpi,
        start_page=args.start_page,
        end_page=args.end_page,
        keep_images=args.keep_images,
        image_dir=args.image_dir,
    )
    print(f"OCR 原始文本已生成：{raw_txt}")

    count = write_cleaned(raw_txt, clean_txt, args.target_chars, args.short_ratio)
    print(f"清洗文本已生成：{clean_txt}")
    print(f"段落数：{count}")

    epub_count = make_epub(str(clean_txt), args.output, args.title, args.author)
    print(f"EPUB 已生成：{args.output}")
    print(f"EPUB 段落数：{epub_count}")


def cmd_default_text_to_epub(args):
    output = Path(args.output)
    clean_txt = output.with_suffix(".cleaned.txt")
    count = write_cleaned(args.input, clean_txt, args.target_chars, args.short_ratio)
    print(f"清洗文本已生成：{clean_txt}")
    print(f"段落数：{count}")
    make_epub(str(clean_txt), args.output, args.title, args.author)
    print(f"EPUB 已生成：{args.output}")


def add_common_text_args(parser):
    parser.add_argument("--target-chars", type=int, default=420)
    parser.add_argument("--short-ratio", type=float, default=0.82)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Convert scanned Chinese PDFs or OCR text into clean EPUB files.")
    sub = parser.add_subparsers(dest="command")

    p_pdf = sub.add_parser("pdf", help="OCR a scanned PDF, clean text, then create EPUB")
    p_pdf.add_argument("--input", required=True, help="Input scanned PDF")
    p_pdf.add_argument("--output", required=True, help="Output EPUB")
    p_pdf.add_argument("--title", required=True)
    p_pdf.add_argument("--author", default="Unknown")
    p_pdf.add_argument("--raw-txt", help="Optional raw OCR text output")
    p_pdf.add_argument("--clean-txt", help="Optional cleaned text output")
    p_pdf.add_argument("--lang", default="ch", help="PaddleOCR language, default: ch")
    p_pdf.add_argument("--dpi", type=int, default=220)
    p_pdf.add_argument("--start-page", type=int)
    p_pdf.add_argument("--end-page", type=int)
    p_pdf.add_argument("--keep-images", action="store_true")
    p_pdf.add_argument("--image-dir", default="ocr_pages")
    add_common_text_args(p_pdf)
    p_pdf.set_defaults(func=cmd_pdf)

    p_clean = sub.add_parser("clean", help="Clean OCR text")
    p_clean.add_argument("--input", required=True)
    p_clean.add_argument("--output", required=True)
    add_common_text_args(p_clean)
    p_clean.set_defaults(func=cmd_clean)

    p_epub = sub.add_parser("epub", help="Create EPUB from cleaned text")
    p_epub.add_argument("--input", required=True)
    p_epub.add_argument("--output", required=True)
    p_epub.add_argument("--title", required=True)
    p_epub.add_argument("--author", default="Unknown")
    p_epub.set_defaults(func=cmd_epub)

    # Backward compatible: zh-ocr-epub --input text.txt --output book.epub ...
    parser.add_argument("--input")
    parser.add_argument("--output")
    parser.add_argument("--title")
    parser.add_argument("--author", default="Unknown")
    add_common_text_args(parser)

    args = parser.parse_args(argv)
    if hasattr(args, "func"):
        args.func(args)
    else:
        if not args.input or not args.output or not args.title:
            parser.print_help()
            raise SystemExit(2)
        cmd_default_text_to_epub(args)


if __name__ == "__main__":
    main()
