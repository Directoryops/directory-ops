import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import find_emails as fe  # noqa: E402


class T(unittest.TestCase):
    def test_deobfuscate(self):
        self.assertIn("info@sunrisewash.com", fe.deobfuscate("write to info [at] sunrisewash [dot] com today"))
        self.assertIn("hello@abc-wash.com", fe.deobfuscate("hello(at)abc-wash.com"))
        self.assertIn("team@x-y.co", fe.deobfuscate("team {at} x-y {dot} co"))

    def test_cloudflare(self):
        # "a@b.co" encoded with key 0x42
        enc = "42" + "".join("%02x" % (ord(c) ^ 0x42) for c in "a@b.co")
        self.assertEqual(fe.cf_decode(enc), "a@b.co")

    def test_junk(self):
        for e in ["logo@2x.png", "abc@sentry.io", "12ab34cd56ef7890ab@sentry-next.wixpress.com", "noreply@shop.com",
                  "you@example.com", "user@domain.com", "name@email.com"]:
            self.assertTrue(fe.is_junk(e), e)
        self.assertFalse(fe.is_junk("info@sunrisewash.com"))

    def test_html_entities_and_mailto(self):
        html = '<a href="mailto:Info@SunriseWash.com?subject=hi">Email</a> or &#105;nfo2@sunrisewash.com'
        _, found, _ = fe.scan_html(html)
        self.assertIn("info@sunrisewash.com", found)
        self.assertIn("info2@sunrisewash.com", found)

    def test_rank(self):
        r = lambda e: fe.rank(e, "sunrisewash.com", "Sunrise Car Wash")  # noqa: E731
        self.assertGreater(r("info@sunrisewash.com"), r("maria@sunrisewash.com"))
        self.assertGreater(r("maria@sunrisewash.com"), r("sunrise@gmail.com"))
        self.assertGreater(r("sunrise@gmail.com"), r("privacy@sunrisewash.com"))
        self.assertEqual(r("hi@coolwebdesign.com"), 0)
        self.assertEqual(fe.base_domain("www.shop.co.uk"), "shop.co.uk")


if __name__ == "__main__":
    unittest.main()
