import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import link_check as lc  # noqa: E402


class T(unittest.TestCase):
    def test_glued_tracking_is_cut(self):
        u = "https://brand.example/locations/texas/springfield-northutm_sourcegoogleutm_mediumorganic:04012020"
        clean, glued = lc.strip_tracking(u)
        self.assertTrue(glued)
        self.assertEqual(clean, "https://brand.example/locations/texas/springfield-north")

    def test_query_tracking_removed_other_params_kept(self):
        clean, glued = lc.strip_tracking("https://brand.example/loc/a?utm_source=google&id=7&gclid=x")
        self.assertFalse(glued)
        self.assertEqual(clean, "https://brand.example/loc/a?id=7")

    def test_index_page(self):
        s = lc.where_it_lands("https://b.example/locations/florida/jacksonville",
                              "https://b.example/locations/florida", 200, "<html>ok</html>", {})
        self.assertEqual(s, "index_page")

    def test_homepage_only_flagged_for_chains(self):
        self.assertEqual(lc.where_it_lands("https://b.example/", "https://b.example/", 200, "x", {}), "ok")
        self.assertEqual(lc.where_it_lands("https://b.example/", "https://b.example/", 200, "x", {}, chain=True),
                         "homepage")
        self.assertEqual(lc.where_it_lands("https://b.example/loc/a", "https://b.example/", 200, "x", {}), "homepage")

    def test_broken_and_blocked(self):
        self.assertEqual(lc.where_it_lands("https://b.example/a", "https://b.example/a", 404, "", {}), "broken")
        self.assertEqual(lc.where_it_lands("https://b.example/a", "https://b.example/a", 429, "Vercel Security Checkpoint",
                                           {}), "blocked_by_security")
        self.assertEqual(lc.where_it_lands("https://b.example/a", "https://b.example/a", 200,
                                           "<h1>Page not found</h1>", {}), "broken")


if __name__ == "__main__":
    unittest.main()
