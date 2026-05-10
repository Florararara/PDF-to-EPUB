from pathlib import Path
from tempfile import TemporaryDirectory
from PIL import Image
import fitz  # PyMuPDF


def render_pdf_pages(pdf_path: str, out_dir: str, dpi: int = 220, start_page=None, end_page=None):
    pdf_path = Path(pdf_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(pdf_path))
    first = 1 if start_page is None else max(1, int(start_page))
    last = len(doc) if end_page is None else min(len(doc), int(end_page))
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)
    image_paths = []

    for page_no in range(first, last + 1):
        page = doc[page_no - 1]
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        img_path = out_dir / f"page_{page_no:04d}.png"
        pix.save(str(img_path))
        image_paths.append((page_no, img_path))

    return image_paths


class PaddleTextRecognizer:
    def __init__(self, lang: str = "ch"):
        try:
            from paddleocr import PaddleOCR
        except Exception as exc:
            raise RuntimeError(
                "没有安装 PaddleOCR。请先运行：python3 -m pip install -e '.[pdf]'"
            ) from exc

        constructors = [
            lambda: PaddleOCR(use_angle_cls=True, lang=lang, show_log=False),
            lambda: PaddleOCR(use_angle_cls=True, lang=lang),
            lambda: PaddleOCR(lang=lang),
            lambda: PaddleOCR(use_doc_orientation_classify=False, use_doc_unwarping=False, use_textline_orientation=True, lang=lang),
        ]
        last_error = None
        for maker in constructors:
            try:
                self.ocr = maker()
                return
            except TypeError as exc:
                last_error = exc
            except Exception as exc:
                last_error = exc
        raise RuntimeError(f"PaddleOCR 初始化失败：{last_error}")

    def image_to_lines(self, image_path: str):
        image_path = str(image_path)
        if hasattr(self.ocr, "ocr"):
            result = self.ocr.ocr(image_path, cls=True)
        elif hasattr(self.ocr, "predict"):
            result = self.ocr.predict(image_path)
        else:
            raise RuntimeError("无法识别当前 PaddleOCR API。")
        lines = _extract_text_lines(result)
        return [x.strip() for x in lines if x and x.strip()]


def _extract_text_lines(obj):
    """Best-effort parser for PaddleOCR 2.x and 3.x result formats."""
    lines = []

    def walk(x):
        if x is None:
            return
        if isinstance(x, str):
            if x.strip():
                lines.append(x.strip())
            return
        if isinstance(x, dict):
            for key in ("rec_texts", "texts"):
                val = x.get(key)
                if isinstance(val, list):
                    for item in val:
                        if isinstance(item, str) and item.strip():
                            lines.append(item.strip())
                    return
            for key in ("text", "transcription", "label"):
                val = x.get(key)
                if isinstance(val, str) and val.strip():
                    lines.append(val.strip())
                    return
            for val in x.values():
                walk(val)
            return
        if isinstance(x, (list, tuple)):
            # PaddleOCR 2.x line: [box, (text, score)]
            if len(x) >= 2 and isinstance(x[1], (list, tuple)) and x[1] and isinstance(x[1][0], str):
                if x[1][0].strip():
                    lines.append(x[1][0].strip())
                return
            for item in x:
                walk(item)

    walk(obj)
    # Remove accidental duplicates caused by recursive parsing.
    deduped = []
    for line in lines:
        if not deduped or deduped[-1] != line:
            deduped.append(line)
    return deduped


def ocr_pdf_to_text(pdf_path: str, output_txt: str, lang: str = "ch", dpi: int = 220, start_page=None, end_page=None, keep_images: bool = False, image_dir: str = "ocr_pages"):
    recognizer = PaddleTextRecognizer(lang=lang)
    output_txt = Path(output_txt)

    if keep_images:
        workdir = Path(image_dir)
        rendered = render_pdf_pages(pdf_path, workdir, dpi=dpi, start_page=start_page, end_page=end_page)
        temp_context = None
    else:
        temp_context = TemporaryDirectory()
        rendered = render_pdf_pages(pdf_path, temp_context.name, dpi=dpi, start_page=start_page, end_page=end_page)

    all_text = []
    total = len(rendered)
    for idx, (page_no, image_path) in enumerate(rendered, start=1):
        print(f"OCR page {idx}/{total}: PDF page {page_no}", flush=True)
        try:
            lines = recognizer.image_to_lines(str(image_path))
        except Exception as exc:
            print(f"WARNING: page {page_no} OCR failed: {exc}", flush=True)
            lines = []
        all_text.append(f"===== Page {page_no} =====")
        all_text.extend(lines)
        all_text.append("")

    output_txt.write_text("\n".join(all_text), encoding="utf-8")
    if temp_context:
        temp_context.cleanup()
    return output_txt
