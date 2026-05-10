import html
import re
import uuid
import zipfile
from pathlib import Path
from datetime import datetime, timezone


def split_paragraphs(text: str):
    blocks = re.split(r"\n\s*\n", text.strip())
    return [re.sub(r"\s*\n\s*", "", b).strip() for b in blocks if b.strip()]


def make_epub(input_txt: str, output_epub: str, title: str, author: str):
    text = Path(input_txt).read_text(encoding="utf-8", errors="ignore")
    paragraphs = split_paragraphs(text)
    if not paragraphs:
        raise ValueError("输入文本没有可用段落。")

    book_id = f"urn:uuid:{uuid.uuid4()}"
    modified = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    chapter = f'''<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="zh" lang="zh">
<head><title>{html.escape(title)}</title><link rel="stylesheet" type="text/css" href="style.css"/></head>
<body><h1>{html.escape(title)}</h1>{''.join(f'<p>{html.escape(p)}</p>' for p in paragraphs)}</body>
</html>'''

    nav = f'''<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="zh" lang="zh">
<head><title>目录</title></head><body><nav epub:type="toc" id="toc"><h1>目录</h1><ol><li><a href="chapter_001.xhtml">{html.escape(title)}</a></li></ol></nav></body></html>'''

    ncx = f'''<?xml version="1.0" encoding="utf-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1"><head><meta name="dtb:uid" content="{book_id}"/><meta name="dtb:depth" content="1"/><meta name="dtb:totalPageCount" content="0"/><meta name="dtb:maxPageNumber" content="0"/></head><docTitle><text>{html.escape(title)}</text></docTitle><docAuthor><text>{html.escape(author)}</text></docAuthor><navMap><navPoint id="chapter_001" playOrder="1"><navLabel><text>{html.escape(title)}</text></navLabel><content src="chapter_001.xhtml"/></navPoint></navMap></ncx>'''

    opf = f'''<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="BookId" xml:lang="zh"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="BookId">{book_id}</dc:identifier><dc:title>{html.escape(title)}</dc:title><dc:creator>{html.escape(author)}</dc:creator><dc:language>zh</dc:language><meta property="dcterms:modified">{modified}</meta></metadata><manifest><item id="chapter_001" href="chapter_001.xhtml" media-type="application/xhtml+xml"/><item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/><item id="toc" href="toc.ncx" media-type="application/x-dtbncx+xml"/><item id="style" href="style.css" media-type="text/css"/></manifest><spine toc="toc"><itemref idref="chapter_001"/></spine></package>'''

    css = '''body{font-family:serif;line-height:1.8;margin:5%;}p{text-indent:2em;margin-top:0;margin-bottom:.9em;}h1{text-align:center;font-size:1.4em;margin:2em 0;}'''

    with zipfile.ZipFile(output_epub, "w") as z:
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        z.writestr("META-INF/container.xml", '''<?xml version="1.0" encoding="utf-8"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>''')
        z.writestr("OEBPS/content.opf", opf)
        z.writestr("OEBPS/toc.ncx", ncx)
        z.writestr("OEBPS/nav.xhtml", nav)
        z.writestr("OEBPS/chapter_001.xhtml", chapter)
        z.writestr("OEBPS/style.css", css)
    return len(paragraphs)
