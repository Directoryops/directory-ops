import io
import json
import os
import sys
import unittest
from contextlib import redirect_stdout

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, ".."))
import db  # noqa: E402
import repo_backend as rb  # noqa: E402

FIX = os.path.join(HERE, "fixtures")


def read(name):
    with open(os.path.join(FIX, name), encoding="utf-8", newline="") as f:
        return f.read()


def run_cli(*argv):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = db.main(list(argv))
    return code, json.loads(buf.getvalue())


LOCAL = ["--backend", "repo", "--local-dir", FIX]


class TestFormats(unittest.TestCase):
    def test_json_roundtrip_and_single_line_change(self):
        text = read("listings.json")
        t = rb.JsonTable("listings.json", text)
        self.assertEqual(t.text(), text)
        t.update(1, {"phone": "(555) 010-2000"})
        diff = [l for l in t.text().splitlines() if l not in text.splitlines()]
        self.assertEqual(diff, ['    "phone": "(555) 010-2000",'])

    def test_json_refuses_odd_format(self):
        with self.assertRaisesRegex(rb.RepoError, "unusual JSON formatting"):
            rb.JsonTable("x.json", '[{"id": 1,   "name": "A"}]\n')

    def test_csv_keeps_quotes_crlf_and_columns(self):
        text = read("listings.csv")
        t = rb.CsvTable("listings.csv", text)
        self.assertEqual(t.text(), text)
        t.update(1, {"phone": "(555) 010-3000"})
        out = t.text()
        self.assertIn("\r\n2,Bubbles Express,(555) 010-3000,Daily 7AM-7PM\r\n", out)
        self.assertIn('"Mon-Sat 8AM-6PM, Sun 9AM-5PM"', out)
        with self.assertRaisesRegex(rb.RepoError, "does not exist"):
            t.update(0, {"website": "x"})

    def test_yaml_list_edits_only_that_line(self):
        text = read("listings.yaml")
        t = rb.YamlListTable("listings.yaml", text)
        rows = t.rows()
        self.assertEqual(rows[0]["phone"], "(555) 010-1000")
        self.assertIsNone(rows[1]["phone"])
        t.update(0, {"phone": "(555) 010-4000"})
        t.update(1, {"phone": "(555) 010-5000", "website": "https://bubbles.example"})
        new = t.text()
        self.assertIn('  phone: "(555) 010-4000"', new)   # kept the double quotes
        self.assertIn("  phone: (555) 010-5000", new)
        self.assertIn("  website: https://bubbles.example", new)
        self.assertIn("# car washes", new)
        with self.assertRaisesRegex(rb.RepoError, "change it by hand"):
            t.update(0, {"tags": "x"})

    def test_markdown_front_matter_only(self):
        text = read("content/listings/sunrise-car-wash.md")
        md = rb.MarkdownFile("s.md", text)
        self.assertEqual(md.values()["phone"], "(555) 010-1000")
        md.set({"phone": "(555) 010-6000", "hours": "Daily 8AM-6PM"})
        new = md.text()
        self.assertIn("phone: (555) 010-6000", new)
        self.assertIn("hours: Daily 8AM-6PM\n---", new)
        self.assertTrue(new.endswith("Sunrise is a family car wash.\n"))
        with self.assertRaisesRegex(rb.RepoError, "change it by hand"):
            md.set({"services": "x"})

    def test_scalar_quoting(self):
        self.assertEqual(rb.fmt_scalar("yes"), '"yes"')
        self.assertEqual(rb.fmt_scalar("a: b"), '"a: b"')
        self.assertEqual(rb.fmt_scalar("12"), '"12"')
        self.assertEqual(rb.fmt_scalar("Mon-Sat 7AM-7PM"), "Mon-Sat 7AM-7PM")
        self.assertEqual(rb.fmt_scalar("it's", "'x'"), "'it''s'")


class TestCli(unittest.TestCase):
    def test_select_and_count_json(self):
        code, out = run_cli("select", *LOCAL, "--table", "listings.json", "--where", "id=eq.2", "--columns", "id,name")
        self.assertEqual(code, 0)
        self.assertEqual(out["rows"], [{"id": 2, "name": "Bubbles Express"}])
        code, out = run_cli("count", *LOCAL, "--table", "listings.csv", "--where", "phone=is.null")
        self.assertEqual(out["total"], 1)

    def test_folder_of_markdown(self):
        code, out = run_cli("select", *LOCAL, "--table", "content/listings/*.md", "--order", "id.asc")
        self.assertEqual([r["id"] for r in out["rows"]], [1, 2, 3])
        self.assertEqual(out["rows"][0]["_slug"], "sunrise-car-wash")

    def test_dry_run_update_shows_diff_and_writes_nothing(self):
        before = read("listings.json")
        code, out = run_cli("update", *LOCAL, "--table", "listings.json", "--allowed-tables", "listings.json",
                            "--match", "id=eq.2", "--set", '{"phone": "(555) 010-2000"}', "--slug", "demo", "--dry-run")
        self.assertEqual(code, 0, out)
        self.assertEqual(out["status"], "dry_run")
        self.assertIn('+    "phone": "(555) 010-2000",', out["diff"])
        self.assertEqual(read("listings.json"), before)

    def test_dry_run_markdown_update(self):
        code, out = run_cli("update", *LOCAL, "--table", "content/listings/*.md", "--allowed-tables", "content/listings/*.md",
                            "--match", "_slug=eq.bubbles-express", "--set", '{"phone": "(555) 010-7000"}', "--slug", "demo", "--dry-run")
        self.assertEqual(code, 0, out)
        self.assertIn("+phone: (555) 010-7000", out["diff"])

    def test_real_write_refused_in_local_mode(self):
        code, out = run_cli("update", *LOCAL, "--table", "listings.json", "--allowed-tables", "listings.json",
                            "--match", "id=eq.2", "--set", '{"phone": "1"}', "--slug", "demo")
        self.assertEqual(code, 1)
        self.assertIn("--local-dir is read only", out["error"])

    def test_local_write_goes_to_out_dir_only(self):
        import tempfile, json as _j
        out_dir = tempfile.mkdtemp()
        before = read("listings.json")
        code, out = run_cli("update", *LOCAL, "--out-dir", out_dir, "--table", "listings.json", "--allowed-tables", "listings.json",
                            "--match", "id=eq.2", "--set", '{"phone": "(555) 010-2000"}', "--slug", "demo")
        self.assertEqual(code, 0, out)
        self.assertEqual(read("listings.json"), before)  # the owner's copy is untouched
        saved = open(out["saved_files"][0]).read()
        self.assertIn('"phone": "(555) 010-2000"', saved)

    def test_safety_rules_still_apply(self):
        code, out = run_cli("update", *LOCAL, "--table", "listings.json", "--allowed-tables", "other.json",
                            "--match", "id=eq.2", "--set", '{"phone": "1"}', "--slug", "demo", "--dry-run")
        self.assertIn("not in this job", out["error"])
        code, out = run_cli("update", *LOCAL, "--table", "listings.json", "--allowed-tables", "listings.json",
                            "--match", "open=eq.true", "--set", '{"phone": "1"}', "--slug", "demo", "--dry-run")
        self.assertIn("hits 2 listings", out["error"])
        code, out = run_cli("update", *LOCAL, "--table", "listings.json", "--allowed-tables", "listings.json",
                            "--match", "id=eq.1", "--set", '{"phone": "1"}', "--expect", '{"phone": "nope"}',
                            "--slug", "demo", "--dry-run")
        self.assertIn("changed since", out["error"])

    def test_insert_duplicate_id_refused(self):
        code, out = run_cli("insert", *LOCAL, "--table", "listings.json", "--allowed-tables", "listings.json",
                            "--row", '{"id": 2, "name": "Dup"}', "--slug", "demo", "--dry-run")
        self.assertIn("already exists", out["error"])

    def test_tables_lists_data_files(self):
        code, out = run_cli("tables", *LOCAL)
        names = [t["table"] for t in out["tables"]]
        self.assertIn("listings.json", names)
        self.assertIn("content/listings/*.md", names)

    def test_repo_mode_needs_repo_and_token(self):
        code, out = run_cli("select", "--backend", "repo", "--table", "x.json")
        self.assertIn("needs --repo", out["error"])


if __name__ == "__main__":
    unittest.main()
