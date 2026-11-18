import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import chain_hours as ch  # noqa: E402


class T(unittest.TestCase):
    def test_osm_list_missing_day_is_closed(self):
        page = '<script type="application/ld+json">{"openingHours": ["Tu-Th 06:00-19:00", "Fr 06:00-18:30", "Sa-Su 07:00-15:00"]}</script>'
        h, src, _ = ch.parse(page)
        self.assertEqual(src, "schema openingHours")
        self.assertEqual(h["monday"], "Closed")
        self.assertEqual(h["friday"], "6AM-6:30PM")
        self.assertEqual(h["sunday"], "7AM-3PM")

    def test_escaped_in_script_data(self):
        page = r'<script>self.__next_f.push("{\"openingHours\":[\"Mo-Fr 07:00-19:00\"]}")</script>'
        h, _, _ = ch.parse(page)
        self.assertEqual(h["monday"], "7AM-7PM")
        self.assertEqual(h["saturday"], "Closed")

    def test_specification(self):
        page = ('{"openingHoursSpecification":[{"dayOfWeek":"https://schema.org/Monday","opens":"06:00","closes":"16:00"},'
                '{"dayOfWeek":["Saturday","Sunday"],"opens":"08:00","closes":"14:00"}]}')
        h, src, _ = ch.parse(page)
        self.assertEqual(src, "schema openingHoursSpecification")
        self.assertEqual(h["monday"], "6AM-4PM")
        self.assertEqual(h["sunday"], "8AM-2PM")
        self.assertEqual(h["tuesday"], "Closed")

    def test_index_dict_sunday_zero(self):
        page = ('{"openingHours":{"0":["0700","1500"],"1":["0600","1900"],"2":["0600","1900"],"3":["0600","1900"],'
                '"4":["0600","1900"],"5":["0600","1800"],"6":[]}}')
        h, src, _ = ch.parse(page)
        self.assertEqual(src, "page data")
        self.assertEqual(h["sunday"], "7AM-3PM")
        self.assertEqual(h["monday"], "6AM-7PM")
        self.assertEqual(h["saturday"], "Closed")

    def test_visible_text(self):
        page = ("<div>Monday: 6:00 AM - 7:00 PM</div><div>Tuesday: 6:00 AM - 7:00 PM</div><div>Wednesday: 6:00 AM - 7:00 PM</div>"
                "<div>Thursday: 6:00 AM - 7:00 PM</div><div>Friday: 6:00 AM - 6:00 PM</div><div>Saturday Closed</div>")
        h, src, quote = ch.parse(page)
        self.assertEqual(src, "page text")
        self.assertEqual(h["monday"], "6AM-7PM")
        self.assertEqual(h["saturday"], "Closed")
        self.assertIn("Monday", quote)

    def test_nothing_found(self):
        self.assertEqual(ch.parse("<p>Visit us soon</p>"), (None, None, None))


if __name__ == "__main__":
    unittest.main()
