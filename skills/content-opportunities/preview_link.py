#!/usr/bin/env python3
"""Turn a local preview file (an article mockup, a page mockup) into a link the owner can CLICK. Free, no account.

  python3 preview_link.py <file.html or file.md> [--title "Article title"] [--style-from <URL of one of the site's own articles>]
  -> {"url": "https://litter.catbox.moe/abc123.html", "expires": "in 72 hours", "file": "..."}

- .md files are turned into a simple, readable HTML page first (headings, lists, links, bold, tables).
- --style-from (use it whenever the site has any article or guide page): the preview is built INSIDE that real page,
  so it has the site's own header, menu, fonts, colors, sidebar and footer. The new article replaces that page's
  text area (the block holding its paragraphs), which styles the new headings, lists and tables like its own.
  Scripts are removed so the page can't redraw itself. If no text area is found, it falls back to the plain page.
- Every page gets <meta name="robots" content="noindex,nofollow"> so search engines don't list the draft.
- The link is private-by-obscurity (random address, not listed anywhere) and deletes itself after 72 hours.
  Tell the owner that in one line. Never put customer emails, phone numbers of private people or keys in a preview.
- If the upload fails, say so plainly and show the article right in the chat instead. Never send the owner a
  server file path (/data/...): they can't open it.
Uses litterbox.catbox.moe (temporary file host). Stdlib only."""
import argparse
import html
import json
import os
import re
import sys
import urllib.request
import uuid

HOST = "https://litterbox.catbox.moe/resources/internals/api.php"
NOINDEX = '<meta name="robots" content="noindex,nofollow">'


def md_to_html(md: str, title: str) -> str:
    out, in_list, in_table = [], False, False
    def inline(t):
        t = html.escape(t)
        t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
        t = re.sub(r"(?<!\*)\*(?!\s)(.+?)\*", r"<em>\1</em>", t)
        t = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+|/[^)\s]*)\)", r'<a href="\2">\1</a>', t)
        return t
    for line in md.splitlines():
        s = line.rstrip()
        if s.startswith("|") and s.endswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                continue
            if not in_table:
                out.append("<table>"); in_table = True
                out.append("<tr>" + "".join(f"<th>{inline(c)}</th>" for c in cells) + "</tr>")
            else:
                out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in cells) + "</tr>")
            continue
        if in_table:
            out.append("</table>"); in_table = False
        m = re.match(r"^(#{1,4})\s+(.*)", s)
        if m:
            if in_list: out.append("</ul>"); in_list = False
            n = len(m.group(1)); out.append(f"<h{n}>{inline(m.group(2))}</h{n}>"); continue
        m = re.match(r"^\s*([-*]|\d+\.)\s+(.*)", s)
        if m:
            if not in_list: out.append("<ul>"); in_list = True
            out.append(f"<li>{inline(m.group(2))}</li>"); continue
        if in_list and not s:
            out.append("</ul>"); in_list = False
        if s:
            out.append(f"<p>{inline(s)}</p>")
    if in_list: out.append("</ul>")
    if in_table: out.append("</table>")
    body = "\n".join(out)
    return (f"<!doctype html><html><head><meta charset='utf-8'>{NOINDEX}"
            f"<meta name='viewport' content='width=device-width,initial-scale=1'><title>{html.escape(title)}</title>"
            "<style>body{font-family:-apple-system,Segoe UI,Roboto,sans-serif;max-width:760px;margin:40px auto;"
            "padding:0 18px;line-height:1.65;color:#1d1d1f}h1{font-size:2em;line-height:1.2}table{border-collapse:collapse;"
            "width:100%;margin:1em 0}td,th{border:1px solid #ddd;padding:8px;text-align:left}th{background:#f5f5f7}"
            ".draft{background:#fff4d6;padding:8px 12px;border-radius:6px;font-size:.9em}</style></head><body>"
            "<p class='draft'>Draft preview, not published. This link deletes itself in 72 hours.</p>"
            f"{body}</body></html>")


def _block_end(page: str, start: int, tag: str):
    """End index of the balanced <tag> block that opens at start, or None."""
    depth = 0
    for m in re.finditer(rf"<(/?){tag}\b[^>]*?(/?)>", page[start:], re.I):
        if m.group(2):
            continue
        depth += -1 if m.group(1) else 1
        if depth == 0:
            return start + m.end()
    return None


def _direct_text(inner: str) -> str:
    """inner HTML with nested <div>/<section>/<article> blocks cut out (what sits directly in this box)."""
    out, i = [], 0
    for m in re.finditer(r"<(div|section|article)\b[^>]*>", inner, re.I):
        if m.start() < i:
            continue
        end = _block_end(inner, m.start(), m.group(1).lower())
        if not end:
            break
        out.append(inner[i:m.start()])
        i = end
    out.append(inner[i:])
    return "".join(out)


def _body_container(page: str):
    """The box that DIRECTLY holds the most paragraphs and headings: the site's article text area
    (not the outer layout, not a 'related articles' strip). Returns (inner_start, inner_end) or None."""
    best = None
    for m in re.finditer(r"<(div|article|section)\b[^>]*>", page, re.I):
        tag = m.group(1).lower()
        end = _block_end(page, m.start(), tag)
        if not end:
            continue
        direct = _direct_text(page[m.end():end])
        n = len(re.findall(r"<(p|h2|h3|ul|ol|table)[\s>]", direct, re.I))
        if n >= 4 and (best is None or n > best[0]):
            best = (n, m.end(), end - len(f"</{tag}>"))
    return (best[1], best[2]) if best else None


def style_from(url: str, body_html: str, title: str) -> str:
    """Put the draft inside one of the site's own article pages: same header, menu, fonts, colors, footer.
    The site's text area styles the new headings, paragraphs, lists and tables the same way it styles its own."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; directory-ops/1.0)"})
    page = urllib.request.urlopen(req, timeout=20).read(3_000_000).decode("utf8", "ignore")
    page = re.sub(r"<script\b[^>]*>.*?</script>", "", page, flags=re.I | re.S)
    page = re.sub(r"<script\b[^>]*/>", "", page, flags=re.I)
    site_h1 = re.search(r"<h1\b[^>]*>", page, re.I)
    h1_open = site_h1.group(0) if site_h1 else "<h1>"
    box = _body_container(page)
    if not box:
        raise ValueError("couldn't find the article text area on the style page")
    body_html = re.sub(r"<h1\b[^>]*>.*?</h1>", "", body_html, count=1, flags=re.I | re.S)
    banner = ("<div style=\"background:#fff4d6;color:#5c4400;padding:10px 14px;border-radius:8px;margin:12px 0;"
              "font:14px/1.4 sans-serif\">Draft preview, not published. Deletes itself in 72 hours.</div>")
    # Give the new headings ids, and build a table of contents from them (replaces the template's own).
    heads = []
    def _id(m):
        i = len(heads); heads.append(re.sub(r"<[^>]+>", "", m.group(2)))
        return f'<h2{m.group(1)} id="part-{i}">{m.group(2)}</h2>'
    body_html = re.sub(r"<h2([^>]*)>(.*?)</h2>", _id, body_html, flags=re.I | re.S)
    first_p = re.search(r"<p[^>]*>(.*?)</p>", body_html, re.I | re.S)
    summary = re.sub(r"<[^>]+>", "", first_p.group(1)).strip()[:220] if first_p else ""
    head, tail = page[:box[0]], page[box[1]:]
    h1m = re.search(r"</h1>", head, re.I)
    if h1m:   # only touch what sits between the page title and the text area (hero area, table of contents)
        pre, mid = head[:h1m.end()], head[h1m.end():]
        mid = re.sub(r"<p\b([^>]*)>.*?</p>", lambda m: f"<p{m.group(1)}>{html.escape(summary)}</p>", mid, count=1, flags=re.I | re.S)
        mid = re.sub(r"<(picture|figure)\b.*?</\1>", "", mid, flags=re.I | re.S)
        mid = re.sub(r"<img\b[^>]*>", "", mid, flags=re.I)
        # Table of contents: copy one whole entry (its <li>/<div> wrapper included) per new heading.
        A = r"<a\b[^>]*href=\"#[^\"]*\"[^>]*>.*?</a>"
        toc = re.findall(rf"<(li|div|p)\b[^>]*>\s*{A}\s*</\1>", mid, re.I | re.S)
        entries = [m.group(0) for m in re.finditer(rf"<(li|div|p)\b[^>]*>\s*{A}\s*</\1>", mid, re.I | re.S)]
        if not entries:
            entries = re.findall(A, mid, re.I | re.S)
        if entries:
            tmpl = entries[0]
            def entry(i, h):
                e = re.sub(r'href="#[^"]*"', f'href="#part-{i}"', tmpl, count=1)
                return re.sub(r"(<a\b[^>]*>).*?(</a>)", lambda m: m.group(1) + html.escape(h) + m.group(2), e, count=1, flags=re.S)
            mid = mid.replace(tmpl, "".join(entry(i, h) for i, h in enumerate(heads)), 1)
            for extra in entries[1:]:
                mid = mid.replace(extra, "", 1)
        head = pre + mid
    page = head + banner + body_html + tail
    h1 = re.search(r"(<h1\b[^>]*>)(.*?)(</h1>)", page, re.I | re.S)
    if h1:
        page = page[:h1.start()] + h1.group(1) + html.escape(title) + h1.group(3) + page[h1.end():]
    else:
        page = page.replace(banner, banner + f"{h1_open}{html.escape(title)}</h1>", 1)
    origin = re.match(r"https?://[^/]+", url).group(0)
    page = re.sub(r"(<head[^>]*>)", lambda m: m.group(1) + f'<base href="{origin}/">' + NOINDEX, page, count=1, flags=re.I)
    page = re.sub(r"<title>.*?</title>", f"<title>{html.escape(title)} (draft)</title>", page, count=1, flags=re.I | re.S)
    return page


def ensure_noindex(page: str) -> str:
    if "noindex" in page.lower():
        return page
    if re.search(r"<head[^>]*>", page, re.I):
        return re.sub(r"(<head[^>]*>)", r"\1" + NOINDEX, page, count=1, flags=re.I)
    return NOINDEX + page


def upload(data: bytes, name: str) -> str:
    boundary = uuid.uuid4().hex
    parts = []
    for k, v in (("reqtype", "fileupload"), ("time", "72h")):
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode())
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"fileToUpload\"; filename=\"{name}\"\r\n"
                 "Content-Type: text/html\r\n\r\n".encode() + data + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    req = urllib.request.Request(HOST, data=b"".join(parts), method="POST",
                                 headers={"Content-Type": f"multipart/form-data; boundary={boundary}",
                                          "User-Agent": "directory-ops/1.0"})
    url = urllib.request.urlopen(req, timeout=60).read().decode().strip()
    if not url.startswith("https://"):
        raise RuntimeError(url[:200])
    return url


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--title", default="Draft preview")
    ap.add_argument("--style-from", default="", help="URL of one of the site's own article pages to use as the design")
    a = ap.parse_args()
    raw = open(a.file, encoding="utf-8").read()
    is_md = a.file.lower().endswith((".md", ".markdown", ".txt"))
    if is_md:   # working notes are not part of the article readers see
        raw = re.sub(r"(?im)^\s*[-*]?\s*\**(target (phrase|keyword)|intent|suggested url|slug|url|meta title|meta description|"
                     r"keywords?|search intent|word count|status|internal links?|sources? checked)\**\s*:.*$\n?", "", raw)
        raw = re.sub(r"^\s*---\s*\n.*?\n---\s*\n", "", raw, count=1, flags=re.S)   # front matter
    page = md_to_html(raw, a.title) if is_md else ensure_noindex(raw)
    styled_note = ""
    if a.style_from:
        body = re.search(r"<body[^>]*>(.*)</body>", page, re.I | re.S)
        body_html = body.group(1) if body else page
        body_html = re.sub(r"<p class='draft'>.*?</p>", "", body_html, flags=re.S)
        try:
            page = style_from(a.style_from, body_html, a.title)
            styled_note = "in your site's own design"
        except Exception as e:
            styled_note = f"plain design (couldn't use the site's design: {type(e).__name__})"
    name = re.sub(r"[^a-z0-9-]+", "-", os.path.splitext(os.path.basename(a.file))[0].lower()).strip("-")[:60] or "preview"
    try:
        url = upload(page.encode("utf-8"), name + ".html")
    except Exception as e:
        print(json.dumps({"url": None, "error": f"{type(e).__name__}: {e}",
                          "say": "I couldn't make a preview link right now, so here's the article in the chat."}))
        return 1
    print(json.dumps({"url": url, "expires": "in 72 hours", "file": a.file, "design": styled_note or "plain",
                      "say": f"Preview (click to open, deletes itself in 72 hours, hidden from Google): {url}"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
