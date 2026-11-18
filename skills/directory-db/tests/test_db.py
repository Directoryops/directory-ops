import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import db

def args(*a):
    return db.build_parser().parse_args(list(a))

BASE = ["--site-url", "https://fake-project.supabase.co", "--key-env", "TEST_DB_KEY"]

class TestArgs(unittest.TestCase):
    def test_write_needs_allowed_tables(self):
        a = args("update", *BASE, "--table", "listings", "--match", "id=eq.1", "--set", '{"phone":"1"}')
        with self.assertRaisesRegex(db.DbError, "allowed-tables"):
            db.check_args(a)

    def test_write_refuses_other_table(self):
        a = args("insert", *BASE, "--table", "users", "--allowed-tables", "listings", "--row", '{"a":1}')
        with self.assertRaisesRegex(db.DbError, "not in this job"):
            db.check_args(a)

    def test_update_needs_match(self):
        a = args("update", *BASE, "--table", "listings", "--allowed-tables", "listings", "--set", '{"a":1}')
        with self.assertRaisesRegex(db.DbError, "needs --match"):
            db.check_args(a)

    def test_bad_filter(self):
        a = args("select", *BASE, "--table", "listings", "--where", "state Ohio")
        with self.assertRaisesRegex(db.DbError, "column=op.value"):
            db.check_args(a)

    def test_bad_json(self):
        a = args("update", *BASE, "--table", "l", "--allowed-tables", "l", "--match", "id=eq.1", "--set", "{phone:1}")
        with self.assertRaisesRegex(db.DbError, "not valid JSON"):
            db.check_args(a)

    def test_row_list_ok(self):
        a = args("insert", *BASE, "--table", "l", "--allowed-tables", "l", "--row", '[{"a":1},{"a":2}]')
        _, payload = db.check_args(a)
        self.assertEqual(len(payload), 2)

    def test_no_delete_command(self):
        with self.assertRaises(SystemExit):
            args("delete", *BASE, "--table", "l")

    def test_log_path_default(self):
        os.environ["DIROPS_REPO"] = "/data/workspace/directory-ops"
        a = args("insert", *BASE, "--table", "l", "--allowed-tables", "l", "--row", '{"a":1}', "--slug", "ex")
        self.assertEqual(db.log_path(a), "/data/workspace/directory-ops/notes/ex/db-changes.jsonl")

    def test_expect_must_be_object(self):
        a = args("update", *BASE, "--table", "l", "--allowed-tables", "l", "--match", "id=eq.1",
                 "--set", '{"a":1}', "--expect", "[1]")
        with self.assertRaisesRegex(db.DbError, "--expect must be"):
            db.check_args(a)

    def test_count_and_select_all_parse(self):
        a = args("count", *BASE, "--table", "l", "--where", "state=eq.Ohio")
        f, _ = db.check_args(a)
        self.assertEqual(f, [("state", "eq.Ohio")])
        b = args("select", *BASE, "--table", "l", "--all")
        self.assertTrue(b.all)

    def test_total_from_header(self):
        self.assertEqual(db.total_from({"Content-Range": "0-99/1234"}), 1234)
        self.assertIsNone(db.total_from({}))

    def test_touch_and_expect_args(self):
        a = args("update", *BASE, "--table", "l", "--allowed-tables", "l", "--match", "id=eq.1",
                 "--set", '{"a":1}', "--expect", '{"a":0}', "--touch", "updated_at")
        db.check_args(a)
        self.assertEqual(a.touch, "updated_at")

    def test_missing_env(self):
        os.environ.pop("TEST_DB_KEY", None)
        a = args("select", *BASE, "--table", "l")
        with self.assertRaisesRegex(db.DbError, "not visible"):
            db.run(a)

if __name__ == "__main__":
    unittest.main()
