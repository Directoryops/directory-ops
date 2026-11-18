#!/usr/bin/env python3
"""Send (or save as a draft) one plain-text email from the site's own mailbox. No extra installs.

    python3 send_mail.py --slug example --host smtp.gmail.com --port 587 \
        --from-email leads@example.com --from-name "Sam at Example Directory" --password-env EXAMPLE_MAIL_PASSWORD \
        --to owner@sunrisecarwash.example --subject "New car wash request in Dayton" --body-file /tmp/email.txt \
        [--reply-to-id "<message-id of the email you're answering>"] [--draft] [--daily-cap 50]

--draft      saves the email to $DIROPS_REPO/notes/<slug>/drafts/<time>-<to>.txt instead of sending (use while auto_send is off).
--daily-cap  refuses to send once this many emails went out today (counted from the log).
--kind       lead (default: a lead email to a business), owner (test email to the site owner), reply (answering someone
             who wrote to us). For --kind lead, --routable-file is required and the To address must be in it.
--routable-file  the business emails that may receive leads: `db.py select` output of the email table filtered to
             is_routable (or the listings' email column), a JSON list of emails, or a text file with one per line.
Every kind refuses an address listed in $DIROPS_REPO/notes/<slug>/questionable-emails.txt (one per line, "# reason"
optional): addresses the agent is asking the owner about. Drafts are refused too, so nothing waits on a bad address.
Every send or draft appends one JSON line to $DIROPS_REPO/notes/<slug>/sent-mail.jsonl (default repo /data/workspace/directory-ops): time, to, subject, message_id, mode.
Refuses bodies with em dashes, an empty subject, or a missing "stop" line (business email rules).
--free       marks this as the business's ONE free lead (Template A). Refused if the log already has a free email,
             sent OR drafted, to that address: use the paid template instead (or hold the lead).
[NEEDED: ...] markers (missing sender name or postal address) are allowed in drafts and refused on a real send.
--lead-id    a lead never gets a second waiting draft (refused; --replace-draft after the owner says replace).
Prints JSON {"status": "sent"|"draft"|"error", ...}.
"""
import argparse
import datetime
import email.message
import email.utils
import json
import os
import re
import smtplib
import sys



def notes_dir(slug):
    """Absolute notes folder: $DIROPS_REPO/notes/<slug> (default /data/workspace/directory-ops), never the current folder."""
    return os.path.join(os.environ.get("DIROPS_REPO", "/data/workspace/directory-ops"), "notes", slug)

def log_path(slug):
    return os.path.join(notes_dir(slug), "sent-mail.jsonl")


def sent_today(slug):
    path = log_path(slug)
    if not os.path.exists(path):
        return 0
    today = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    n = 0
    with open(path) as f:
        for line in f:
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if e.get("mode") == "sent" and e.get("time", "").startswith(today):
                n += 1
    return n


def had_free(slug, to):
    """True when the log already has a free lead email (sent or draft) to this address."""
    path = log_path(slug)
    if not os.path.exists(path):
        return False
    with open(path) as f:
        for line in f:
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if e.get("free") and e.get("to", "").strip().lower() == to.strip().lower():
                return True
    return False


def waiting_draft(slug, lead_id):
    """The draft file still waiting for this lead (drafted, not sent or replaced since), else ''."""
    path = log_path(slug)
    if not lead_id or not os.path.exists(path):
        return ""
    waiting = ""
    with open(path) as f:
        for line in f:
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if str(e.get("lead_id", "")) != str(lead_id):
                continue
            if e.get("mode") == "draft":
                waiting = e.get("file", "") or "(draft)"
            elif e.get("mode") in ("sent", "draft_replaced"):
                waiting = ""
    return waiting


def _emails_in(obj, out):
    if isinstance(obj, str):
        for e in re.findall(r"[A-Za-z0-9._%+'-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", obj):
            out.add(e.lower())
    elif isinstance(obj, dict):
        for v in obj.values():
            _emails_in(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _emails_in(v, out)
    return out


def load_emails(path):
    raw = open(path, encoding="utf-8").read()
    try:
        return _emails_in(json.loads(raw), set())
    except json.JSONDecodeError:
        return _emails_in(raw, set())


def questionable(slug):
    path = os.path.join(notes_dir(slug), "questionable-emails.txt")
    if not os.path.exists(path):
        return set()
    return _emails_in("\n".join(l.split("#", 1)[0] for l in open(path, encoding="utf-8")), set())


def recipient_problem(slug, to, kind, routable_file):
    """None when the address may receive this email, else a plain reason."""
    addr = (email.utils.parseaddr(to)[1] or to).strip().lower()
    if addr in questionable(slug):
        return (f"{addr} is on the questionable list (notes/{slug}/questionable-emails.txt): you asked the owner about it. "
                "Wait for their answer, or route the lead to the next confirmed business.")
    if kind == "lead":
        if not routable_file:
            return "a lead email needs --routable-file (the business emails marked routable) so only confirmed addresses get leads"
        if addr not in load_emails(routable_file):
            return (f"{addr} is not a routable business email in {routable_file}. Only send leads to confirmed addresses "
                    "(saved with the owner's OK); otherwise pick the next business or hold the lead.")
    return None


def check_body(subject, body):
    problems = []
    if not subject.strip():
        problems.append("empty subject")
    if "—" in body or "—" in subject:
        problems.append("em dash in the email (write two sentences instead)")
    if not re.search(r"\bstop\b", body, re.I):
        problems.append('missing the "Reply stop" line')
    if re.search(r"\{[a-z_]+\}", body + subject):
        problems.append("a {placeholder} was not filled in: " + ", ".join(sorted(set(re.findall(r"\{[a-z_]+\}", body + subject)))))
    return problems


def hyphen_warnings(subject, body):
    """Ranges written with a hyphen ("$150-250", "8 - 10") break the no-hyphens copy rule. Warn, don't refuse:
    phone numbers, emails and links legitimately contain hyphens."""
    text = re.sub(r"\S+@\S+|https?://\S+|\(?\d{3}\)?[ .-]?\d{3}-\d{4}", " ", subject + "\n" + body)
    hits = re.findall(r"\$?\d[\d,.]*\s?-\s?\$?\d[\d,.]*|\s-\s", text)
    return [f'hyphen used as a range or dash: "{h.strip() or "-"}" (write "X to Y" or two sentences)' for h in hits[:3]]


def main():
    ap = argparse.ArgumentParser(description="Send or draft one plain-text email from the site mailbox.")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--host", default="")
    ap.add_argument("--port", type=int, default=587)
    ap.add_argument("--from-email", required=True)
    ap.add_argument("--from-name", default="")
    ap.add_argument("--password-env", default="")
    ap.add_argument("--to", default="")
    ap.add_argument("--subject", default="")
    ap.add_argument("--body-file", default="")
    ap.add_argument("--send-draft", default="", help="send a saved draft file exactly as approved (reads its To/Subject lines; the body is everything after the blank line)")
    ap.add_argument("--reply-to-id", default="", help="Message-ID being answered, keeps the same thread")
    ap.add_argument("--draft", action="store_true")
    ap.add_argument("--free", action="store_true", help="this is the business's one free lead (Template A)")
    ap.add_argument("--daily-cap", type=int, default=50)
    ap.add_argument("--kind", choices=["lead", "owner", "reply"], default="lead")
    ap.add_argument("--routable-file", default="", help="routable business emails (db.py select output, JSON list or one per line)")
    ap.add_argument("--lead-id", default="", help="the lead this email is about; a lead never gets a second waiting draft")
    ap.add_argument("--replace-draft", action="store_true", help="owner said replace: the lead's waiting draft is replaced by this one")
    a = ap.parse_args()

    def out(d, code=0):
        print(json.dumps(d))
        return code


    if a.send_draft:
        raw = open(a.send_draft, encoding="utf-8").read()
        head, _, rest = raw.partition("\n\n")
        hdr = dict(l.split(": ", 1) for l in head.splitlines() if ": " in l)
        a.to, a.subject = hdr.get("To", a.to), hdr.get("Subject", a.subject)
        body = rest.strip() + "\n"
        a.draft = False
    else:
        if not (a.to and a.subject and a.body_file):
            return out({"status": "error", "error": "give --to, --subject and --body-file (or --send-draft <file>)"}, 1)
        body = open(a.body_file, encoding="utf-8").read().strip() + "\n"
    bad_to = recipient_problem(a.slug, a.to, a.kind, a.routable_file)
    if bad_to:
        return out({"status": "error", "error": "not sent or drafted: " + bad_to}, 1)
    problems = check_body(a.subject, body)
    if a.free and a.kind == "lead" and not a.send_draft and had_free(a.slug, a.to):
        return out({"status": "error", "error": f"not sent or drafted: {a.to} already has its free lead (sent or waiting as a draft). "
                    "Use the paid template (B or B2) without --free, or hold the lead."}, 1)
    if a.kind == "lead" and a.lead_id and not a.send_draft:
        old = waiting_draft(a.slug, a.lead_id)
        if old and not a.replace_draft:
            return out({"status": "error", "error": f"not sent or drafted: lead {a.lead_id} already has 1 draft waiting "
                        f"({old}). Show the owner '1 draft already waiting' and offer to replace it (--replace-draft)."}, 1)
        if old and a.replace_draft:
            with open(log_path(a.slug), "a") as f:
                f.write(json.dumps({"time": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
                                    "lead_id": a.lead_id, "mode": "draft_replaced", "file": old}) + "\n")
            if os.path.isfile(old):
                os.remove(old)
    if not a.draft and re.search(r"\[NEEDED:", body + a.subject):
        problems.append("a [NEEDED: ...] detail (sender name or postal address) is still missing; ask the owner first")
    for w in hyphen_warnings(a.subject, body):
        print(json.dumps({"warning": w}), file=sys.stderr)
    if problems:
        return out({"status": "error", "error": "not sent: " + "; ".join(problems)}, 1)

    msg = email.message.EmailMessage()
    msg["From"] = email.utils.formataddr((a.from_name, a.from_email)) if a.from_name else a.from_email
    msg["To"] = a.to
    msg["Subject"] = a.subject
    msg["Date"] = email.utils.formatdate(localtime=False)
    msg["Message-ID"] = email.utils.make_msgid(domain=a.from_email.split("@")[-1])
    if a.reply_to_id:
        msg["In-Reply-To"] = a.reply_to_id
        msg["References"] = a.reply_to_id
    msg.set_content(body)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    os.makedirs(notes_dir(a.slug), exist_ok=True)

    if a.draft:
        d = os.path.join(notes_dir(a.slug), "drafts")
        os.makedirs(d, exist_ok=True)
        stem = f"{now[:19].replace(':', '')}-{re.sub(r'[^a-z0-9]+', '-', a.to.lower())}" + (f"-lead{a.lead_id}" if a.lead_id else "")
        path, n = os.path.join(d, stem + ".txt"), 2
        while os.path.exists(path):
            path, n = os.path.join(d, f"{stem}-{n}.txt"), n + 1
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"To: {a.to}\nSubject: {a.subject}\n\n{body}")
        mode, extra = "draft", {"file": path}
    else:
        if not a.host or not a.password_env:
            return out({"status": "error", "error": "sending needs --host and --password-env (or use --draft)"}, 1)
        if sent_today(a.slug) >= a.daily_cap:
            return out({"status": "error", "error": f"daily cap of {a.daily_cap} reached; the rest waits for tomorrow"}, 1)
        pw = os.environ.get(a.password_env, "").strip().strip("\"'").replace(" ", "")
        if not pw:
            return out({"status": "error", "error": f"env var {a.password_env} is not visible. Add it in hPanel → Environment, Restart, new chat."}, 1)
        try:
            with smtplib.SMTP(a.host, a.port, timeout=30) as s:
                s.starttls()
                s.login(a.from_email, pw)
                s.send_message(msg)
        except smtplib.SMTPAuthenticationError:
            return out({"status": "error", "error": "login failed. Check the from address is exactly the mailbox address first, then the app password."}, 1)
        except Exception as e:  # noqa: BLE001
            return out({"status": "error", "error": f"could not send: {str(e)[:200]}"}, 1)
        mode, extra = "sent", {}

    with open(log_path(a.slug), "a") as f:
        f.write(json.dumps({"time": now, "to": a.to, "subject": a.subject, "message_id": msg["Message-ID"], "mode": mode,
                            "free": bool(a.free), "lead_id": a.lead_id, **({"file": extra["file"]} if extra.get("file") else {})}) + "\n")
    return out({"status": mode, "to": a.to, "message_id": msg["Message-ID"], **extra})


if __name__ == "__main__":
    sys.exit(main())
