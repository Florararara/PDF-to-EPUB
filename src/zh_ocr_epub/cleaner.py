import re
from statistics import median

TERMINAL_PUNCT = "。！？!?；;"
CLOSING_PUNCT = "”’』」》）)]"


def visible_len(s: str) -> int:
    return len(re.sub(r"\s+", "", s))


def normalize_line(line: str) -> str:
    line = line.strip()
    line = re.sub(r"\s+", " ", line)
    line = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", line)
    line = re.sub(r"\s+([，。！？；：、）】》」』])", r"\1", line)
    line = re.sub(r"([（【《「『])\s+", r"\1", line)
    return line.strip()


def is_page_marker(line: str) -> bool:
    s = line.strip()
    patterns = [
        r"^=+\s*Page\s+\d+\s*=+$",
        r"^\[Page\s+\d+\]$",
        r"^Page\s+\d+$",
        r"^-?\s*\d+\s*-?$",
        r"^第\s*\d+\s*页$",
    ]
    return any(re.match(p, s, re.IGNORECASE) for p in patterns)


def is_noise_line(line: str) -> bool:
    s = line.strip()
    return s in {"-", "—", "_", "——"} or bool(re.match(r"^\d+$", s))


def ends_with_terminal(line: str) -> bool:
    s = line.rstrip()
    while s and s[-1] in CLOSING_PUNCT:
        s = s[:-1].rstrip()
    return bool(s and s[-1] in TERMINAL_PUNCT)


def looks_like_heading(line: str, normal_len: int) -> bool:
    s = line.strip()
    if not s:
        return False
    if re.match(r"^第[一二三四五六七八九十百零\d]+[章节部篇]", s):
        return True
    if re.match(r"^[一二三四五六七八九十]+[、.．]\s*", s):
        return True
    if visible_len(s) <= max(12, int(normal_len * 0.45)) and not ends_with_terminal(s):
        if not re.search(r"[，,：:；;]", s):
            return True
    return False


def starts_like_new_paragraph(line: str) -> bool:
    starters = (
        "但是", "然而", "因此", "所以", "可是", "于是", "那时", "此时", "后来", "同时", "总之", "换言之",
        "阿伦特", "布鲁希尔", "布吕歇", "海德格尔", "她", "他", "我", "我们", "这", "那", "在", "对", "作为", "如果", "当"
    )
    return line.strip().startswith(starters)


def join_lines(a: str, b: str) -> str:
    a, b = a.rstrip(), b.lstrip()
    if re.search(r"[A-Za-z0-9]$", a) and re.search(r"^[A-Za-z0-9]", b):
        return a + " " + b
    return a + b


def estimate_normal_line_len(lines) -> int:
    lens = [visible_len(x) for x in lines if x.strip() and not is_page_marker(x) and not is_noise_line(x) and 8 <= visible_len(x) <= 100]
    return int(median(lens)) if lens else 36


def clean_ocr_text(raw_text: str, target_chars: int = 420, short_ratio: float = 0.82) -> str:
    raw_lines = raw_text.splitlines()
    lines = []
    hard_breaks = set()

    for raw in raw_lines:
        line = normalize_line(raw)
        if not line:
            if lines:
                hard_breaks.add(len(lines) - 1)
            continue
        if is_page_marker(line) or is_noise_line(line):
            continue
        lines.append(line)

    normal_len = estimate_normal_line_len(lines)
    short_line_threshold = int(normal_len * short_ratio)
    paragraphs = []
    buf = ""

    for i, line in enumerate(lines):
        next_line = lines[i + 1] if i + 1 < len(lines) else ""
        if looks_like_heading(line, normal_len):
            if buf.strip():
                paragraphs.append(buf.strip())
                buf = ""
            paragraphs.append(line.strip())
            continue

        buf = line if not buf else join_lines(buf, line)
        line_is_short = visible_len(line) <= short_line_threshold
        line_ends = ends_with_terminal(line)
        reached_target = visible_len(buf) >= target_chars
        should_break = False

        if i in hard_breaks and line_ends:
            should_break = True
        if line_ends and line_is_short:
            should_break = True
        if line_ends and reached_target:
            should_break = True
        if line_ends and next_line and starts_like_new_paragraph(next_line) and visible_len(buf) >= 180:
            should_break = True

        if should_break:
            paragraphs.append(buf.strip())
            buf = ""

    if buf.strip():
        paragraphs.append(buf.strip())

    return re.sub(r"\n{3,}", "\n\n", "\n\n".join(p for p in paragraphs if p.strip())).strip() + "\n"
