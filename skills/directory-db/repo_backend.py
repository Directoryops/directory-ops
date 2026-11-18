"""GitHub repo backend for db.py (--backend repo). Standard library only.

For directories whose listings live in files inside a code repo (common for Next.js / Astro sites):
  - one JSON file: a list of objects, or an object holding one list of objects   e.g. data/listings.json
  - one CSV file with a header row                                               e.g. data/listings.csv
  - one YAML file that is a list of flat "key: value" items                      e.g. data/listings.yaml
  - a folder of Markdown files with front matter, one file per listing           e.g. content/listings/*.md

Reads go through the GitHub REST API (no git needed). Writes NEVER touch the main branch: each day's
changes go to a branch "directory-ops/<slug>-<date>" with ONE pull request. The pull request is the
approval: the owner merges it and the site rebuilds; closing it rejects the changes.

Files are edited in place so the pull request shows only the changed values: JSON keeps its indent and
key order, CSV keeps its columns, quoting and line endings, YAML and front matter change only the lines of
the keys being set. A file that can't be edited without rewriting it (unusual formatting, nested values,
comments on a line) is refused with a plain message instead of being reformatted.
"""
import base64
import csv
import datetime
import difflib
import fnmatch
import io
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.github.com"
DATA_EXT = (".json", ".csv", ".yaml", ".yml")
MD_EXT = (".md", ".mdx")
SKIP_DIRS = ("node_modules/", ".next/", "dist/", "build/", ".github/", ".vercel/", "coverage/", ".git/", "out/")
SKIP_FILES = ("package.json", "package-lock.json", "composer.json", "vercel.json", "components.json", "manifest.json",
              "renovate.json", "turbo.json", "deno.json", "jsconfig.json", "pnpm-lock.yaml", ".eslintrc.json",
              "netlify.toml", "docker-compose.yml", "docker-compose.yaml", ".prettierrc.json")


class RepoError(Exception):
    pass


# ---------------------------------------------------------------- values and filters

def same(a, b):
    """Loose equality that works across file types (CSV holds text, JSON holds numbers and booleans)."""
    if a == b:
        return True
    if a in (None, "") and b in (None, ""):
        return True
    if a is None or b is None:
        return False
    if isinstance(a, bool) or isinstance(b, bool):
        return str(a).lower() == str(b).lower()
    return str(a).strip() == str(b).strip()


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def match_filter(row, col, expr):
    op, _, val = expr.partition(".")
    v = row.get(col)
    if op == "eq":
        return same(v, val)
    if op == "neq":
        return not same(v, val)
    if op == "is":
        if val.lower() == "null":
            return v in (None, "")
        return same(v, val)
    if op == "in":
        opts = [o.strip().strip('"') for o in val.strip("()").split(",")]
        return any(same(v, o) for o in opts)
    if op in ("lt", "lte", "gt", "gte"):
        if v in (None, ""):
            return False
        a, b = _num(v), _num(val)
        a, b = (a, b) if a is not None and b is not None else (str(v), val)
        return {"lt": a < b, "lte": a <= b, "gt": a > b, "gte": a >= b}[op]
    if op in ("like", "ilike"):
        pat = val.replace("*", "%")
        rx = "^" + re.escape(pat).replace("%", ".*") + "$"
        return bool(re.match(rx, "" if v is None else str(v), re.I if op == "ilike" else 0))
    raise RepoError(f'filter operator "{op}" is not supported in repo mode (use eq, neq, is, in, lt, gt, lte, gte, like, ilike)')


def filter_rows(rows, filters):
    return [r for r in rows if all(match_filter(r, c, e) for c, e in filters)]


# ---------------------------------------------------------------- scalar YAML (front matter and flat lists)

KEY_LINE = re.compile(r"^(?P<prefix>(?P<indent>[ ]*)(?:- )?)(?P<key>[A-Za-z_][\w\-]*):(?:[ ]+(?P<val>.*?))?[ ]*$")
SPECIAL_START = ("[", "{", "|", ">", "&", "*", "!", "%", "@", "`")


def parse_scalar(raw):
    """Returns (value, simple). simple=False means the value is something we won't edit safely."""
    raw = raw if raw is not None else ""
    if raw == "":
        return None, True
    if raw.startswith(SPECIAL_START):
        return raw, False
    if raw[0] in "\"'":
        q = raw[0]
        if len(raw) < 2 or raw[-1] != q:
            return raw, False
        inner = raw[1:-1]
        if q == '"':
            try:
                return json.loads(raw), True
            except ValueError:
                return inner, True
        return inner.replace("''", "'"), True
    if re.search(r"\s#", raw):
        return raw, False  # inline comment: rewriting would drop it
    low = raw.lower()
    if low in ("null", "~"):
        return None, True
    if low in ("true", "false"):
        return low == "true", True
    if re.fullmatch(r"-?\d+", raw):
        return int(raw), True
    if re.fullmatch(r"-?\d+\.\d+", raw):
        return float(raw), True
    return raw, True


def fmt_scalar(v, old_raw=None):
    if v is None:
        return "" if old_raw in (None, "") else "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, (list, dict)):
        raise RepoError("repo mode only writes plain values (text, numbers, true/false), not lists or objects")
    s = str(v)
    if old_raw and old_raw.startswith("'"):
        return "'" + s.replace("'", "''") + "'"
    if old_raw and old_raw.startswith('"'):
        return json.dumps(s, ensure_ascii=False)
    needs_quotes = (s == "" or s != s.strip() or s.startswith(SPECIAL_START + ("-", "?", ":", "#", "'", '"'))
                    or ": " in s or " #" in s or "\n" in s or s.lower() in ("null", "~", "true", "false", "yes", "no", "on", "off")
                    or re.fullmatch(r"-?\d+(\.\d+)?", s) is not None)
    return json.dumps(s, ensure_ascii=False) if needs_quotes else s


class Mapping:
    """One flat mapping inside a list of lines (a front matter block or one YAML list item)."""

    def __init__(self, lines, start, end, key_indent, first_prefix):
        self.lines, self.start, self.end = lines, start, end  # [start, end) line indexes
        self.key_indent, self.first_prefix = key_indent, first_prefix
        self.keys = {}  # key -> (line index, raw value, simple)
        i = start
        while i < end:
            m = KEY_LINE.match(lines[i])
            if m and (len(m.group("prefix")) == key_indent or (i == start and m.group("prefix") == first_prefix)):
                raw = m.group("val") or ""
                val, simple = parse_scalar(raw)
                j = i + 1
                while j < end and lines[j].strip() and (len(lines[j]) - len(lines[j].lstrip(" "))) > key_indent:
                    j += 1  # an indented block under this key (list, nested map, multi-line text)
                if j > i + 1 or (raw == "" and j < end and lines[j].lstrip().startswith("- ")):
                    simple = False
                self.keys[m.group("key")] = (i, raw, simple, val)
                i = j
            else:
                i += 1

    def values(self):
        return {k: (v[3] if v[2] else v[1]) for k, v in self.keys.items()}

    def complex_keys(self):
        return [k for k, v in self.keys.items() if not v[2]]

    def set(self, key, value):
        """Change one key in place, or add it after the mapping's last line. Returns a line offset."""
        if key in self.keys:
            idx, raw, simple, _ = self.keys[key]
            if not simple:
                raise RepoError(f'"{key}" holds a list, nested value or comment in this file; change it by hand')
            m = KEY_LINE.match(self.lines[idx])
            new = fmt_scalar(value, raw)
            self.lines[idx] = f"{m.group('prefix')}{key}:" + (f" {new}" if new != "" else "")
            return 0
        new = fmt_scalar(value)
        line = " " * self.key_indent + f"{key}:" + (f" {new}" if new != "" else "")
        self.lines.insert(self.end, line)
        self.end += 1
        return 1


# ---------------------------------------------------------------- file formats

def _json_variants(data, text):
    """Find the dump settings that reproduce the original file exactly, so edits change only edited lines."""
    second = next((l for l in text.splitlines()[1:] if l.strip()), "")
    det = "\t" if second.startswith("\t") else (len(second) - len(second.lstrip(" ")) or 2)
    trailing = "\n" if text.endswith("\n") else ""
    for ind in dict.fromkeys([det, 2, 4, "\t"]):
        for asc in (False, True):
            if json.dumps(data, indent=ind, ensure_ascii=asc) + trailing == text:
                return {"indent": ind, "ensure_ascii": asc, "trailing": trailing}
    return None


class JsonTable:
    kind = "json"

    def __init__(self, path, text, allow_reformat=False):
        self.path = path
        try:
            self.data = json.loads(text)
        except ValueError as e:
            raise RepoError(f"{path} is not valid JSON ({e})") from None
        self.style = _json_variants(self.data, text)
        if self.style is None:
            if not allow_reformat:
                raise RepoError(f"{path} uses unusual JSON formatting, so any edit would rewrite the whole file. "
                                "Ask the site's developer to format it with 2-space indents, or pass --allow-reformat.")
            self.style = {"indent": 2, "ensure_ascii": False, "trailing": "\n" if text.endswith("\n") else ""}
        if isinstance(self.data, list):
            self.container = self.data
        elif isinstance(self.data, dict):
            lists = [k for k, v in self.data.items() if isinstance(v, list) and (not v or isinstance(v[0], dict))]
            if len(lists) != 1:
                raise RepoError(f"{path} must be a list of listings, or an object holding exactly one list of listings")
            self.container = self.data[lists[0]]
        else:
            raise RepoError(f"{path} must be a list of listings")
        if not all(isinstance(r, dict) for r in self.container):
            raise RepoError(f"{path}: every listing must be an object with fields")

    def rows(self):
        return [dict(r) for r in self.container]

    def update(self, index, changes):
        for k, v in changes.items():
            self.container[index][k] = v

    def insert(self, row):
        self.container.append(dict(row))

    def text(self):
        s = self.style
        return json.dumps(self.data, indent=s["indent"], ensure_ascii=s["ensure_ascii"]) + s["trailing"]


class CsvTable:
    kind = "csv"

    def __init__(self, path, text, allow_reformat=False):
        self.path = path
        self.nl = "\r\n" if "\r\n" in text else "\n"
        self.trailing = text.endswith(("\n", "\r\n"))
        rows = list(csv.reader(io.StringIO(text, newline="")))
        if not rows:
            raise RepoError(f"{path} is empty")
        self.header, self.body = rows[0], rows[1:]
        if len(set(self.header)) != len(self.header):
            raise RepoError(f"{path} has two columns with the same name; fix the header first")
        self.quoting = None
        for q in (csv.QUOTE_MINIMAL, csv.QUOTE_ALL):
            if self._render(rows, q) == text:
                self.quoting = q
                break
        if self.quoting is None:
            if not allow_reformat:
                raise RepoError(f"{path} uses unusual CSV quoting, so any edit would rewrite the whole file. Pass --allow-reformat to accept that.")
            self.quoting = csv.QUOTE_MINIMAL

    def _render(self, rows, quoting):
        buf = io.StringIO()
        csv.writer(buf, lineterminator=self.nl, quoting=quoting).writerows(rows)
        out = buf.getvalue()
        return out if self.trailing else out[: -len(self.nl)] if out.endswith(self.nl) else out

    def rows(self):
        return [dict(zip(self.header, r + [""] * (len(self.header) - len(r)))) for r in self.body]

    def _cell(self, v):
        if v is None:
            return ""
        if isinstance(v, bool):
            return "true" if v else "false"
        return str(v)

    def update(self, index, changes):
        for k, v in changes.items():
            if k not in self.header:
                raise RepoError(f'column "{k}" does not exist in {self.path}; adding a column changes every row, so ask the developer first')
            row = self.body[index] + [""] * (len(self.header) - len(self.body[index]))
            row[self.header.index(k)] = self._cell(v)
            self.body[index] = row

    def insert(self, row):
        extra = [k for k in row if k not in self.header]
        if extra:
            raise RepoError(f"columns not in {self.path}: {', '.join(extra)}")
        self.body.append([self._cell(row.get(h)) for h in self.header])

    def text(self):
        return self._render([self.header] + self.body, self.quoting)


class YamlListTable:
    kind = "yaml"

    def __init__(self, path, text, allow_reformat=False):
        self.path = path
        self.trailing = text.endswith("\n")
        self.lines = text.split("\n")
        if self.trailing:
            self.lines = self.lines[:-1]
        self.items = []
        self._scan()

    def _scan(self):
        self.items = []
        starts = [i for i, l in enumerate(self.lines) if re.match(r"^[ ]*- [A-Za-z_][\w\-]*:", l)]
        if not starts:
            raise RepoError(f"{self.path} isn't a simple list of listings (\"- name: ...\" items); change it by hand or ask the developer")
        item_indent = len(self.lines[starts[0]]) - len(self.lines[starts[0]].lstrip(" "))
        starts = [i for i in starts if len(self.lines[i]) - len(self.lines[i].lstrip(" ")) == item_indent]
        for n, s in enumerate(starts):
            e = starts[n + 1] if n + 1 < len(starts) else len(self.lines)
            while e > s + 1 and not self.lines[e - 1].strip():
                e -= 1
            self.items.append(Mapping(self.lines, s, e, item_indent + 2, " " * item_indent + "- "))
        self.item_indent = item_indent

    def rows(self):
        return [m.values() for m in self.items]

    def update(self, index, changes):
        for k, v in changes.items():
            if self.items[index].set(k, v):
                self._scan()

    def insert(self, row):
        last = self.items[-1]
        new = []
        for n, (k, v) in enumerate(row.items()):
            pre = " " * self.item_indent + ("- " if n == 0 else "  ")
            val = fmt_scalar(v)
            new.append(f"{pre}{k}:" + (f" {val}" if val != "" else ""))
        self.lines[last.end:last.end] = new
        self._scan()

    def text(self):
        return "\n".join(self.lines) + ("\n" if self.trailing else "")


class MarkdownFile:
    """One listing = one Markdown file; only its front matter is ever edited."""

    def __init__(self, path, text):
        self.path = path
        self.trailing = text.endswith("\n")
        self.lines = text.split("\n")
        if self.trailing:
            self.lines = self.lines[:-1]
        if not self.lines or self.lines[0].strip() != "---":
            raise RepoError(f"{path} has no front matter (the --- block at the top); change it by hand")
        try:
            close = next(i for i in range(1, len(self.lines)) if self.lines[i].strip() == "---")
        except StopIteration:
            raise RepoError(f"{path}: the front matter is never closed with ---") from None
        self.fm = Mapping(self.lines, 1, close, 0, "")

    def values(self):
        return self.fm.values()

    def set(self, changes):
        for k, v in changes.items():
            self.fm.set(k, v)

    def text(self):
        return "\n".join(self.lines) + ("\n" if self.trailing else "")


def slugify(s):
    s = re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-")
    return s or "listing"


def open_table(path, text, allow_reformat=False):
    low = path.lower()
    if low.endswith(".json"):
        return JsonTable(path, text, allow_reformat)
    if low.endswith(".csv"):
        return CsvTable(path, text, allow_reformat)
    if low.endswith((".yaml", ".yml")):
        return YamlListTable(path, text, allow_reformat)
    raise RepoError(f"{path}: repo mode reads .json, .csv, .yaml/.yml files, or a folder of .md files (write it as folder/*.md)")


def is_folder_spec(table):
    return table.endswith("/") or table.endswith(("*.md", "*.mdx")) or not os.path.splitext(table)[1]


def folder_parts(table):
    if table.endswith(("*.md", "*.mdx")):
        return table.rsplit("/", 1)[0] if "/" in table else "", table.rsplit("/", 1)[-1]
    return table.rstrip("/"), "*.md*"


# ---------------------------------------------------------------- where the files come from

class LocalStore:
    """Reads files from a local folder. For previews and tests: real writes are refused."""

    def __init__(self, root):
        self.root = root

    def get(self, path, ref=None):
        p = os.path.join(self.root, path)
        if not os.path.isfile(p):
            return None
        with open(p, encoding="utf-8", newline="") as f:
            return f.read(), "local"

    def list_dir(self, folder, ref=None):
        p = os.path.join(self.root, folder)
        if not os.path.isdir(p):
            raise RepoError(f"folder {folder} not found")
        return sorted((folder + "/" + n).lstrip("/") for n in os.listdir(p) if os.path.isfile(os.path.join(p, n)))

    def tree(self, ref=None):
        out = []
        for d, _, files in os.walk(self.root):
            for n in files:
                rel = os.path.relpath(os.path.join(d, n), self.root)
                out.append({"path": rel, "size": os.path.getsize(os.path.join(d, n))})
        return out


class GitHubStore:
    def __init__(self, repo, token_env, base):
        if not re.fullmatch(r"[\w.\-]+/[\w.\-]+", repo or ""):
            raise RepoError('--repo must look like "owner/name", e.g. "sunrise/car-wash-site"')
        token = os.environ.get(token_env or "", "").strip().strip("\"'")
        if not token:
            raise RepoError(f"env var {token_env} is not visible. Add the GitHub token on your host (hPanel → Environment) "
                            "under that name, restart, start a new chat. See 'Listings in a GitHub repo' in the directory-db skill.")
        self.repo, self.base, self._token, self.token_env = repo, base, token, token_env

    def api(self, method, path, body=None, ok404=False, need="Contents: Read"):
        url = API + path
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method, headers={
            "Authorization": f"Bearer {self._token}", "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "directory-ops"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                txt = r.read().decode("utf-8", "ignore")
                return json.loads(txt) if txt.strip() else {}
        except urllib.error.HTTPError as e:
            msg = e.read()[:300].decode("utf-8", "ignore")
            if e.code == 404 and ok404:
                return None
            if e.code == 401:
                raise RepoError(f"GitHub said 401: the token in {self.token_env} is wrong or expired. Make a new "
                                "fine-grained token and update it in hPanel → Environment.") from None
            if e.code == 403 and "rate limit" in msg.lower():
                raise RepoError("GitHub's rate limit was hit. Wait an hour and run the same command again.") from None
            if e.code == 403:
                raise RepoError(f"GitHub said 403: the token can't do this. It needs \"{need}\" for {self.repo}. "
                                "Edit the token on GitHub (Settings → Developer settings → Fine-grained tokens) and add that permission.") from None
            if e.code == 404:
                raise RepoError(f"GitHub said 404: {self.repo} or that file wasn't found, or the token can't see this repo "
                                "(a fine-grained token must list this repo under Repository access).") from None
            raise RepoError(f"GitHub said {e.code}: {msg}") from None
        except urllib.error.URLError as e:
            raise RepoError(f"can't reach GitHub ({e.reason}). Check the internet connection and try again.") from None

    def _repo(self, p):
        return f"/repos/{self.repo}{p}"

    def get(self, path, ref=None):
        ref = ref or self.base
        d = self.api("GET", self._repo(f"/contents/{urllib.parse.quote(path)}?ref={urllib.parse.quote(ref)}"), ok404=True)
        if d is None:
            return None
        if isinstance(d, list):
            raise RepoError(f"{path} is a folder; for a folder of Markdown files write it as {path.rstrip('/')}/*.md")
        if d.get("encoding") == "base64" and d.get("content"):
            raw = base64.b64decode(d["content"])
        else:  # files over 1 MB: the contents API returns no body, the blob API does
            blob = self.api("GET", self._repo(f"/git/blobs/{d['sha']}"))
            raw = base64.b64decode(blob.get("content", ""))
        return raw.decode("utf-8"), d["sha"]

    def list_dir(self, folder, ref=None):
        ref = ref or self.base
        d = self.api("GET", self._repo(f"/contents/{urllib.parse.quote(folder)}?ref={urllib.parse.quote(ref)}"))
        if not isinstance(d, list):
            raise RepoError(f"{folder} is a file, not a folder")
        return sorted(x["path"] for x in d if x.get("type") == "file")

    def tree(self, ref=None):
        d = self.api("GET", self._repo(f"/git/trees/{urllib.parse.quote(ref or self.base)}?recursive=1"))
        return [{"path": t["path"], "size": t.get("size", 0)} for t in d.get("tree", []) if t.get("type") == "blob"]

    def branch_sha(self, name):
        d = self.api("GET", self._repo(f"/git/ref/heads/{urllib.parse.quote(name)}"), ok404=True)
        return d["object"]["sha"] if d else None

    def create_branch(self, name):
        base_sha = self.branch_sha(self.base)
        if not base_sha:
            raise RepoError(f'branch "{self.base}" not found in {self.repo}; pass the right --branch (often main or master)')
        self.api("POST", self._repo("/git/refs"), {"ref": f"refs/heads/{name}", "sha": base_sha}, need="Contents: Read and write")

    def put(self, path, text, sha, branch, message):
        body = {"message": message, "content": base64.b64encode(text.encode("utf-8")).decode(), "branch": branch}
        if sha:
            body["sha"] = sha
        self.api("PUT", self._repo(f"/contents/{urllib.parse.quote(path)}"), body, need="Contents: Read and write")

    def prs(self, branch):
        owner = self.repo.split("/")[0]
        return self.api("GET", self._repo(f"/pulls?state=all&head={urllib.parse.quote(owner + ':' + branch)}"),
                        need="Pull requests: Read") or []

    def open_pr(self, branch, title, body):
        d = self.api("POST", self._repo("/pulls"), {"title": title, "head": branch, "base": self.base, "body": body},
                     need="Pull requests: Read and write")
        return d

    def edit_pr(self, number, body):
        self.api("PATCH", self._repo(f"/pulls/{number}"), {"body": body}, need="Pull requests: Read and write")


# ---------------------------------------------------------------- loading a "table"

class Table:
    """Rows from one data file, or from a folder of Markdown files (one file per row)."""

    def __init__(self, store, spec, ref, allow_reformat=False):
        self.store, self.spec, self.ref = store, spec, ref
        self.files = {}  # path -> (original text, sha, parsed)
        if is_folder_spec(spec):
            self.folder, pattern = folder_parts(spec)
            paths = [p for p in store.list_dir(self.folder, ref) if fnmatch.fnmatch(os.path.basename(p), pattern)
                     and p.lower().endswith(MD_EXT)]
            self.mode = "folder"
            self.row_files = []
            for p in paths:
                got = store.get(p, ref)
                md = MarkdownFile(p, got[0])
                self.files[p] = (got[0], got[1], md)
                self.row_files.append(p)
            self.ext = os.path.splitext(paths[0])[1] if paths else ".md"
        else:
            got = store.get(spec, ref)
            if got is None:
                if isinstance(store, GitHubStore) and store.api("GET", f"/repos/{store.repo}", ok404=True) is None:
                    raise RepoError(f"GitHub can't find the repo {store.repo}, or the token can't see it. Check the name "
                                    "(owner/name, as in the repo's web address) and that the token lists this repo under Repository access.")
                raise RepoError(f"file {spec} not found on branch {ref}. Run the tables command to see the data files.")
            self.mode = "file"
            self.files[spec] = (got[0], got[1], open_table(spec, got[0], allow_reformat))

    def rows(self):
        if self.mode == "folder":
            out = []
            for p in self.row_files:
                r = self.files[p][2].values()
                r["_file"], r["_slug"] = p, os.path.splitext(os.path.basename(p))[0]
                out.append(r)
            return out
        return self.files[self.spec][2].rows()

    def update(self, index, changes):
        if self.mode == "folder":
            self.files[self.row_files[index]][2].set(changes)
        else:
            self.files[self.spec][2].update(index, changes)

    def insert(self, row, id_field):
        if self.mode == "folder":
            name = row.get("slug") or row.get(id_field) or row.get("name")
            if not name:
                raise RepoError("a new Markdown listing needs a slug, id or name to make its file name")
            p = f"{self.folder}/{slugify(name)}{self.ext}".lstrip("/")
            if p in self.files or self.store.get(p, self.ref) is not None:
                raise RepoError(f"{p} already exists; use upsert or update instead")
            lines = ["---"] + [f"{k}:" + ((" " + fmt_scalar(v)) if fmt_scalar(v) != "" else "") for k, v in row.items()] + ["---", ""]
            text = "\n".join(lines)
            self.files[p] = ("", None, MarkdownFile(p, text))
            self.row_files.append(p)
        else:
            self.files[self.spec][2].insert(row)

    def changed_files(self):
        """[(path, old text, new text, sha)] for files whose text changed."""
        out = []
        for p, (old, sha, parsed) in self.files.items():
            new = parsed.text()
            if new != old:
                out.append((p, old, new, sha))
        return out


# ---------------------------------------------------------------- commands

def _store(a):
    if getattr(a, "local_dir", ""):
        return LocalStore(a.local_dir)
    return GitHubStore(a.repo, a.token_env, a.branch)


def _project(rows, columns):
    if columns in ("", "*", None):
        return rows
    cols = [c.strip() for c in columns.split(",") if c.strip()]
    return [{c: r.get(c) for c in cols} for r in rows]


def _order(rows, order):
    if not order:
        return rows
    col, _, direction = order.partition(".")
    key = lambda r: (r.get(col) in (None, ""), _num(r.get(col)) if _num(r.get(col)) is not None else str(r.get(col) or ""))  # noqa: E731
    try:
        return sorted(rows, key=key, reverse=(direction == "desc"))
    except TypeError:
        return sorted(rows, key=lambda r: str(r.get(col) or ""), reverse=(direction == "desc"))


def list_tables(a):
    store = _store(a)
    files = store.tree(getattr(a, "branch", None))
    data, md = [], {}
    for f in files:
        p = f["path"]
        low = p.lower()
        if any(low.startswith(d) or ("/" + d) in low for d in SKIP_DIRS) or os.path.basename(low) in SKIP_FILES:
            continue
        if re.search(r"(tsconfig|\.config)\.[a-z]+$|lock\.(json|yaml)$|\.eslintrc|\.prettierrc", low):
            continue
        if low.endswith(DATA_EXT):
            data.append({"table": p, "size_kb": round(f["size"] / 1024, 1)})
        elif low.endswith(MD_EXT):
            folder = p.rsplit("/", 1)[0] if "/" in p else ""
            md.setdefault(folder, 0)
            md[folder] += 1
    folders = [{"table": f"{d}/*.md".lstrip("/"), "files": n} for d, n in md.items() if n >= 3 and d]
    rank = lambda t: (0 if re.search(r"(^|/)(data|content|src/data|src/content|lib/data)(/|$)", t["table"]) else 1, t["table"])  # noqa: E731
    return {"status": "ok", "how": "data files in the repo", "tables": sorted(data, key=rank)[:40] + sorted(folders, key=rank)[:20],
            "note": "Pick the file (or folder of .md files) that holds the listings, then use it as --table."}


def session_branch(store, slug, today):
    """Today's branch for this site, plus its open pull request (if any). A branch whose pull request was
    already merged or closed is never reused: the next one gets -2, -3, ..."""
    name = f"directory-ops/{slug}-{today}"
    for n in range(1, 30):
        cand = name if n == 1 else f"{name}-{n}"
        if store.branch_sha(cand) is None:
            return cand, None, False
        prs = store.prs(cand)
        open_ = [p for p in prs if p.get("state") == "open"]
        if open_:
            return cand, open_[0], True
        if not prs:
            return cand, None, True  # branch exists, no PR yet (an earlier run stopped halfway): reuse it
    raise RepoError("too many directory-ops branches today; merge or close the open pull requests first")


def _diff(changed):
    out = []
    for p, old, new, _ in changed:
        out += list(difflib.unified_diff(old.splitlines(), new.splitlines(), f"a/{p}", f"b/{p}", n=1, lineterm=""))
    text = "\n".join(out)
    return text if len(text) < 6000 else text[:6000] + "\n... (diff cut)"


def _pr_lines(entries):
    lines = []
    for e in entries:
        who = e.get("id")
        for k, ch in e["changes"].items():
            show = lambda v: "(empty)" if v in (None, "") else v  # noqa: E731
            lines.append(f"- `{e['file']}` · {who}: **{k}** `{show(ch['old'])}` → `{show(ch['new'])}`"
                         + (f" ({e['why']}" + (f"; {e['source']}" if e.get("source") else "") + ")" if e.get("why") else ""))
    return lines


PR_INTRO = ("Changes proposed by directory-ops (your Hermes agent).\n\n"
            "**Merge** this pull request to publish them; your site rebuilds as usual. **Close** it to reject them.\n\n")


def run(a, filters, payload, now, write_log):
    allow = getattr(a, "allow_reformat", False)
    id_field = getattr(a, "id_field", "id") or "id"
    store = _store(a)
    write = a.action in ("insert", "update", "upsert")
    is_local = isinstance(store, LocalStore)
    if write and not a.slug:
        raise RepoError("writes in repo mode need --slug (it names the branch and the log)")
    out_dir = getattr(a, "out_dir", "")
    if write and is_local and not a.dry_run and not out_dir:
        raise RepoError("--local-dir is read only; add --out-dir <folder> to save the updated file there "
                        "(the owner puts it back in their project), or use --repo for a pull request")

    today = now[:10]
    branch, pr, exists = (a.branch, None, True)
    if write and not is_local:
        branch, pr, exists = session_branch(store, a.slug, today)
    ref = branch if (write and exists and not is_local) else a.branch
    table = Table(store, a.table, ref, allow)
    rows = table.rows()

    if a.action == "count":
        return {"status": "ok", "table": a.table, "total": len(filter_rows(rows, filters))}
    if a.action == "select":
        hit = _order(filter_rows(rows, filters), getattr(a, "order", ""))
        out = hit if a.all else hit[: a.limit]
        res = {"status": "ok", "rows": _project(out, a.columns), "count": len(out), "total": len(hit)}
        if len(hit) > len(out):
            res["warning"] = f"showing {len(out)} of {len(hit)} rows; use --all (or a higher --limit) to get every row"
        return res

    entries = []
    if a.action == "update":
        idx = [i for i, r in enumerate(rows) if all(match_filter(r, c, e) for c, e in filters)]
        if not idx:
            raise RepoError("no listing matches; nothing changed. Check the --match filter.")
        if len(idx) > a.max_rows:
            raise RepoError(f"the match hits {len(idx)} listings (limit {a.max_rows}). Match on the listing's id, or raise --max-rows on purpose.")
        if a.expect:
            exp = json.loads(a.expect)
            stale = [{k: {"expected": v, "now": rows[i].get(k)}} for i in idx for k, v in exp.items() if not same(rows[i].get(k), v)]
            if stale:
                raise RepoError("the listing changed since this was proposed, so nothing was written. "
                                f"Re-check it: {json.dumps(stale, default=str)[:300]}")
        bad = [k for k in payload if k.startswith("_")]
        if bad:
            raise RepoError(f"{', '.join(bad)} are helper fields (the file name), not data; they can't be changed")
        for i in idx:
            ch = {k: {"old": rows[i].get(k), "new": v} for k, v in payload.items() if not same(rows[i].get(k), v)}
            if ch:
                sets = {k: c["new"] for k, c in ch.items()}
                if getattr(a, "touch", ""):
                    sets[a.touch] = now
                table.update(i, sets)
                entries.append({"file": rows[i].get("_file", a.table), "id": f"{id_field}={rows[i].get(id_field, rows[i].get('_slug'))}",
                                "changes": ch, "why": a.why, "source": a.source})
        if not entries:
            return {"status": "unchanged", "note": "the listing already has these values"}
    else:  # insert / upsert
        key = getattr(a, "on_conflict", None)
        for row in payload:
            bad = [k for k in row if k.startswith("_")]
            if bad:
                raise RepoError(f"{', '.join(bad)} are helper fields, not data")
            hit = [i for i, r in enumerate(rows) if key and row.get(key) is not None and same(r.get(key), row.get(key))]
            if a.action == "insert" and id_field in row and any(same(r.get(id_field), row[id_field]) for r in rows):
                raise RepoError(f"a listing with {id_field}={row[id_field]} already exists; use update or upsert")
            if hit:
                i = hit[0]
                ch = {k: {"old": rows[i].get(k), "new": v} for k, v in row.items() if not same(rows[i].get(k), v)}
                if ch:
                    table.update(i, {k: c["new"] for k, c in ch.items()})
                    entries.append({"file": rows[i].get("_file", a.table), "id": f"{key}={row.get(key)}", "changes": ch,
                                    "why": a.why, "source": a.source})
            else:
                table.insert(row, id_field)
                entries.append({"file": a.table, "id": f"{id_field}={row.get(id_field, row.get('slug', row.get('name')))}",
                                "changes": {k: {"old": None, "new": v} for k, v in row.items()}, "why": a.why, "source": a.source})
        if not entries:
            return {"status": "unchanged", "note": "every row already has these values"}

    changed = table.changed_files()
    entry = {"time": now, "action": a.action, "backend": "repo", "repo": getattr(a, "repo", "") or a.local_dir,
             "table": a.table, "changes": entries, "why": a.why, "source": a.source}
    if a.dry_run:
        return {"status": "dry_run", "would_change": entries, "branch": branch if not is_local else "(preview)", "diff": _diff(changed)}

    if is_local:
        # Owner's copy of the file: write the updated file to out_dir, never touch the original copy.
        saved = []
        for p_, old_, new_, sha_ in changed:
            dest = os.path.join(out_dir, p_)
            os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
            with open(dest, "w", encoding="utf-8", newline="") as f:
                f.write(new_)
            saved.append(dest)
        entry["files"] = saved
        return {"status": "ok", "changes": entries, "saved_files": saved, "log": write_log(a, entry),
                "next": "Send the owner the updated file to put back in their project (or ask Claude Code to)."}

    if not exists:
        store.create_branch(branch)
    for p, old, new, sha in changed:
        store.put(p, new, sha, branch, f"directory-ops: {a.why or a.action} ({p})"[:120])
    lines = _pr_lines(entries)
    if pr:
        body = (pr.get("body") or PR_INTRO.rstrip()) + "\n" + "\n".join(lines)
        store.edit_pr(pr["number"], body)
        url = pr["html_url"]
    else:
        title = f"directory-ops: {a.why or a.action}"[:72]
        url = store.open_pr(branch, title, PR_INTRO + "\n".join(lines))["html_url"]
    entry["pull_request"], entry["branch"] = url, branch
    return {"status": "ok", "rows_changed": len(entries), "pull_request": url, "branch": branch,
            "log": write_log(a, entry), "changes": entries,
            "next": "Tell the owner: review and merge this pull request to publish (close it to reject)."}
