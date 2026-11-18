import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import check_lead  # noqa: E402

SEND = os.path.join(HERE, "..", "send_mail.py")
BODY = "Hi Sunrise team,\n\nA customer asked for a quote.\n\nSam\n\nReply stop and I won't email you again.\n"


class Guards(unittest.TestCase):
    def setUp(self):
        self.repo = tempfile.mkdtemp()
        self.notes = os.path.join(self.repo, "notes", "exd")
        os.makedirs(self.notes)
        self.body = os.path.join(self.repo, "body.txt")
        open(self.body, "w").write(BODY)
        self.routable = os.path.join(self.repo, "routable.json")
        json.dump({"rows": [{"email": "info@sunrisewash.example", "is_routable": True},
                            {"email": "owner.maybe@gmail.example", "is_routable": True}]}, open(self.routable, "w"))
        open(os.path.join(self.notes, "questionable-emails.txt"), "w").write("owner.maybe@gmail.example  # not on their site\n")

    def run_send(self, to, *extra):
        env = dict(os.environ, DIROPS_REPO=self.repo)
        r = subprocess.run([sys.executable, SEND, "--slug", "exd", "--from-email", "sam@exd.example", "--to", to,
                            "--subject", "New car wash request", "--body-file", self.body, "--draft", *extra],
                           capture_output=True, text=True, env=env)
        return json.loads(r.stdout.strip().splitlines()[-1])

    def test_one_waiting_draft_per_lead(self):
        r1 = self.run_send("info@sunrisewash.example", "--routable-file", self.routable, "--lead-id", "42")
        self.assertEqual(r1["status"], "draft")
        r2 = self.run_send("info@sunrisewash.example", "--routable-file", self.routable, "--lead-id", "42")
        self.assertEqual(r2["status"], "error")
        self.assertIn("1 draft waiting", r2["error"])
        r3 = self.run_send("info@sunrisewash.example", "--routable-file", self.routable, "--lead-id", "42", "--replace-draft")
        self.assertEqual(r3["status"], "draft")
        drafts = [f for f in os.listdir(os.path.join(self.notes, "drafts")) if "lead42" in f]
        self.assertEqual(len(drafts), 1)  # the old draft was replaced, not kept beside the new one
        self.assertEqual(self.run_send("info@sunrisewash.example", "--routable-file", self.routable,
                                       "--lead-id", "43")["status"], "draft")

    def test_confirmed_address_drafts(self):
        self.assertEqual(self.run_send("info@sunrisewash.example", "--routable-file", self.routable)["status"], "draft")

    def test_questionable_address_refused(self):
        r = self.run_send("Owner.Maybe@gmail.example", "--routable-file", self.routable)
        self.assertEqual(r["status"], "error")
        self.assertIn("questionable", r["error"])

    def test_unknown_address_refused(self):
        r = self.run_send("someone@else.example", "--routable-file", self.routable)
        self.assertEqual(r["status"], "error")
        self.assertIn("not a routable", r["error"])

    def test_lead_needs_routable_file(self):
        self.assertEqual(self.run_send("info@sunrisewash.example")["status"], "error")

    def test_owner_kind_skips_routable_but_not_questionable(self):
        self.assertEqual(self.run_send("me@exd.example", "--kind", "owner")["status"], "draft")
        self.assertEqual(self.run_send("owner.maybe@gmail.example", "--kind", "owner")["status"], "error")

    def test_empty_phone_passes(self):
        v, why = check_lead.check_phone("", "US")
        self.assertEqual(v, "pass")
        self.assertIn("no phone", why)
        check_lead._mx_cache["gmail.com"] = True
        self.assertEqual(check_lead.check("dana@gmail.com", "", "2099-01-01", "US")["verdict"], "review")  # 18+ months
        self.assertEqual(check_lead.check("dana@gmail.com", "", "", "US")["verdict"], "pass")

    def test_one_free_lead_per_business_counts_drafts(self):
        self.assertEqual(self.run_send("info@sunrisewash.example", "--routable-file", self.routable, "--free")["status"], "draft")
        r = self.run_send("info@sunrisewash.example", "--routable-file", self.routable, "--free")
        self.assertEqual(r["status"], "error")
        self.assertIn("already has its free lead", r["error"])
        # the paid template (no --free) is still fine
        self.assertEqual(self.run_send("info@sunrisewash.example", "--routable-file", self.routable)["status"], "draft")

    def test_needed_marker_ok_in_draft_refused_on_send(self):
        open(self.body, "w").write(BODY.replace("Sam", "Sam\n[NEEDED: your postal address]"))
        self.assertEqual(self.run_send("info@sunrisewash.example", "--routable-file", self.routable)["status"], "draft")
        env = dict(os.environ, DIROPS_REPO=self.repo)
        r = subprocess.run([sys.executable, SEND, "--slug", "exd", "--from-email", "sam@exd.example", "--to", "info@sunrisewash.example",
                            "--subject", "New car wash request", "--body-file", self.body, "--routable-file", self.routable,
                            "--host", "smtp.example", "--password-env", "NOPE_PW"], capture_output=True, text=True, env=env)
        out = json.loads(r.stdout.strip().splitlines()[-1])
        self.assertEqual(out["status"], "error")
        self.assertIn("NEEDED", out["error"])

    def test_bad_phone_still_rejected(self):
        self.assertEqual(check_lead.check_phone("555-0123", "US")[0], "reject")


if __name__ == "__main__":
    unittest.main()
