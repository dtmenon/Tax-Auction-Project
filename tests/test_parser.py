import unittest

from tax_auction.parser import extract_listings_from_html


class ParserTests(unittest.TestCase):
    def test_extract_listings_from_html_table(self):
        html = """
        <table>
          <tr><th>APN</th><th>Address</th><th>Min Bid</th></tr>
          <tr><td>123-456-789</td><td>100 Main St</td><td>$12,345.00</td></tr>
        </table>
        """
        listings = extract_listings_from_html(html, source_artifact_url="https://example.com")
        self.assertEqual(len(listings), 1)
        self.assertEqual(listings[0].apn, "123-456-789")
        self.assertEqual(listings[0].minimum_bid, 12345.0)


if __name__ == "__main__":
    unittest.main()
