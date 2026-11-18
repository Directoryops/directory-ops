#!/usr/bin/env python3
"""Read-only inbox reader for inbox-triage (IMAP, no browser).

    python3 read_inbox.py --host imap.gmail.com --user you@gmail.com --password-env SLUG_MAIL_PASSWORD \
        --since-days 8 --max 150

Opens the mailbox READ ONLY: nothing is marked read, moved, labeled or deleted, and nothing is sent.
Prints JSON: {status, count, messages: [{message_id, date, from, subject, text, links}]}

- text is plain text (HTML stripped), cut to 3,000 characters.
- links are the first 15 http(s) links found (useful for Google Alerts).
- Skip messages you already handled: compare message_id with your log table.
"""
import argparse
import email
import email.header
import email.utils
import html
import imaplib
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone


def decode(value) -> str:
    if not value:
        return ""
    parts = []
    for text, enc in email.header.decode_header(value):
        parts.append(text.decode(enc or "utf-8", "ignore") if isinstance(text, bytes) else text)
    return "".join(parts).strip()


def body_text(msg) -> str:
    plain, rich = [], []
    for part in msg.walk() if msg.is_multipart() else [msg]:
        if part.get_content_maintype() == "multipart" or part.get_filename():
            continue
        try:
            payload = part.get_payload(decode=True) or b""
            text = payload.decode(part.get_content_charset() or "utf-8", "ignore")
        except Exception:  # noqa: BLE001
            continue
        (plain if part.get_content_type() == "text/plain" else rich).append(text)
    if plain:
        return "\n".join(plain)
    raw = "\n".join(rich)
    raw = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw)
    raw = re.sub(r'(?i)<a [^>]*href="([^"]+)"[^>]*>', r" \1 ", raw)
    return html.unescape(re.sub(r"<[^>]+>", " ", raw))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", required=True)
    ap.add_argument("--user", required=True)
    ap.add_argument("--password-env", required=True)
    ap.add_argument("--since-days", type=int, default=8)
    ap.add_argument("--max", type=int, default=150)
    ap.add_argument("--folder", default="INBOX")
    a = ap.parse_args()

    # App passwords are shown as "abcd efgh ijkl mnop"; the spaces and stray quotes aren't part of it.
    password = (os.environ.get(a.password_env) or "").strip().strip('"\'').replace(" ", "")
    if not password:
        print(json.dumps({"status": "error", "error": f"env var {a.password_env} is not set"}))
        return 1
    try:
        box = imaplib.IMAP4_SSL(a.host)
        box.login(a.user, password)
        box.select(f'"{a.folder}"', readonly=True)
        since = (datetime.now(timezone.utc) - timedelta(days=a.since_days)).strftime("%d-%b-%Y")
        _, data = box.search(None, "SINCE", since)
        ids = data[0].split()[-a.max:]
        messages = []
        for i in reversed(ids):
            _, parts = box.fetch(i, "(BODY.PEEK[])")
            msg = email.message_from_bytes(parts[0][1])
            text = re.sub(r"[ \t\r\f\v]+", " ", body_text(msg))
            text = re.sub(r"\n\s*\n+", "\n", text).strip()
            links = list(dict.fromkeys(re.findall(r"https?://[^\s\"'<>)]+", text)))[:15]
            messages.append({
                "message_id": decode(msg.get("Message-ID")) or f"uid-{i.decode()}",
                "date": decode(msg.get("Date")),
                "from": decode(msg.get("From")),
                "subject": decode(msg.get("Subject")),
                "text": text[:3000],
                "links": links,
            })
        box.logout()
    except imaplib.IMAP4.error as e:
        hint = ""
        if "AUTHENTICATIONFAILED" in str(e).upper() or "credentials" in str(e).lower():
            hint = (f" The password was read from {a.password_env} ({len(password)} characters; a Gmail app password"
                    f" is 16). Usual causes: it was made while signed in to a different Google account than"
                    f" {a.user}, it's the normal Gmail password instead of an app password, or it was revoked.")
        print(json.dumps({"status": "error", "error": f"login failed: {e}{hint}"[:600]}))
        return 1
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"status": "error", "error": str(e)[:300]}))
        return 1
    print(json.dumps({"status": "ok", "count": len(messages), "messages": messages}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
