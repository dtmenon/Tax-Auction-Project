import unittest

from tax_auction.pipeline import _build_change_events


class PipelineTests(unittest.TestCase):
    def test_build_change_events_has_all_states(self):
        events = _build_change_events(
            current_apns={"001-001-001", "003-003-003"},
            previous_apns={"002-002-002", "003-003-003"},
        )

        self.assertIn(("001-001-001", "newly_listed"), events)
        self.assertIn(("002-002-002", "removed_since_last_snapshot"), events)
        self.assertIn(("003-003-003", "still_listed"), events)


if __name__ == "__main__":
    unittest.main()
