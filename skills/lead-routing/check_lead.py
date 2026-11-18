#!/usr/bin/env python3
"""Hard checks for one lead before routing it (lead-routing Step 2). Standard library only. Free.

    python3 check_lead.py --email "dana@gmail.com" --phone "(512) 873-2290" [--needed-by 2026-12-01] [--phone-country US]
    python3 check_lead.py --leads-json leads.json      # db.py select output; checks every row
        [--email-col email --phone-col phone --needed-by-col preferred_date --id-col id]

Checks:
  email   valid format, and the domain can receive mail (MX record, looked up with DNS over HTTPS:
          dns.google, then cloudflare-dns.com). No MX = reject. Lookup failed both ways = review.
  phone   US: 10 digits after removing +1 and punctuation. Reject: the fiction range 555-0100 to 555-0199,
          all one digit, sequences like 1234567890 / 123-4567, or fewer/more digits. Empty phone = pass with a note
          (the email carries the lead; the agent holds it only if the request itself is vague).
          Other countries: only "has 7 to 15 digits".
  date    needed-by date in the past = skip (never route). More than 18 months away = review.
Prints JSON: {"verdict": "pass|review|reject|skip", "reasons": [...], ...} (one object, or a list for --leads-json).
The agent still judges name, spam, location and duplicates (Step 2); this script only does the mechanical checks.
"""
import argparse
import datetime
import json
import re
import sys
import urllib.parse
import urllib.request

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+'-]+@([A-Za-z0-9-]+\.)+[A-Za-z]{2,}$")
_mx_cache = {}


def has_mx(domain):
    """True / False, or None when DNS could not be asked."""
    if domain in _mx_cache:
        return _mx_cache[domain]
    urls = [("https://dns.google/resolve?name=%s&type=MX" % urllib.parse.quote(domain), {}),
            ("https://cloudflare-dns.com/dns-query?name=%s&type=MX" % urllib.parse.quote(domain),
             {"accept": "application/dns-json"})]
    result = None
    for url, headers in urls:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "directory-ops-check-lead", **headers})
            data = json.loads(urllib.request.urlopen(req, timeout=15).read().decode())
        except Exception:  # noqa: BLE001
            continue
        answers = [a for a in data.get("Answer", []) if a.get("type") == 15]
        # A "null MX" (RFC 7505: priority 0 and target ".") means the domain accepts no mail.
        real = [a for a in answers if not re.fullmatch(r"0\s+\.?", str(a.get("data", "")).strip())]
        result = bool(real)
        break
    _mx_cache[domain] = result
    return result


def check_phone(phone, country):
    raw = (phone or "").strip()
    if not raw:
        return "pass", "no phone number (route by email; the template drops the Phone line)"
    digits = re.sub(r"\D", "", raw)
    if country.upper() != "US":
        return ("pass", "") if 7 <= len(digits) <= 15 else ("reject", "phone has the wrong number of digits")
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10:
        return "reject", "phone is not 10 digits"
    if len(set(digits)) == 1:
        return "reject", "phone is one repeated digit"
    if digits in ("1234567890", "0123456789") or digits[3:] == "1234567":
        return "reject", "phone is a fake sequence"
    if digits[0] in "01" or digits[3] in "01":
        return "reject", "phone has an impossible area code or exchange"
    if digits[3:6] == "555" and 100 <= int(digits[6:]) <= 199:
        return "reject", "phone is in the 555-0100 to 0199 range reserved for fiction"
    return "pass", ""


def check(email, phone, needed_by, country):
    reasons, verdict = [], "pass"

    def worse(v, why):
        nonlocal verdict
        order = {"pass": 0, "review": 1, "skip": 2, "reject": 3}
        if order[v] > order[verdict]:
            verdict = v
        if why:
            reasons.append(why)

    em = (email or "").strip()
    if not EMAIL_RE.match(em):
        worse("reject", "email format is not valid")
    else:
        mx = has_mx(em.rsplit("@", 1)[1].lower())
        if mx is False:
            worse("reject", "email domain can't receive mail (no MX record)")
        elif mx is None:
            worse("review", "couldn't check the email domain (DNS lookup failed)")
    pv, why = check_phone(phone, country)
    worse(pv, why)
    if needed_by:
        try:
            d = datetime.date.fromisoformat(str(needed_by)[:10])
            today = datetime.date.today()
            if d < today:
                worse("skip", "needed-by date already passed")
            elif d > today + datetime.timedelta(days=548):
                worse("review", "needed-by date is more than 18 months away")
        except ValueError:
            worse("review", "needed-by date is not a date")
    return {"verdict": verdict, "reasons": reasons}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--email", default="")
    ap.add_argument("--phone", default="")
    ap.add_argument("--needed-by", default="")
    ap.add_argument("--phone-country", default="US")
    ap.add_argument("--leads-json", default="")
    ap.add_argument("--email-col", default="email")
    ap.add_argument("--phone-col", default="phone")
    ap.add_argument("--needed-by-col", default="")
    ap.add_argument("--id-col", default="id")
    a = ap.parse_args()
    if a.leads_json:
        data = json.load(open(a.leads_json))
        rows = data.get("rows", data) if isinstance(data, dict) else data
        out = []
        for r in rows:
            res = check(r.get(a.email_col), r.get(a.phone_col),
                        r.get(a.needed_by_col) if a.needed_by_col else "", a.phone_country)
            out.append({"id": r.get(a.id_col), **res})
        print(json.dumps(out, indent=1))
    else:
        print(json.dumps(check(a.email, a.phone, a.needed_by, a.phone_country)))


if __name__ == "__main__":
    sys.exit(main())
