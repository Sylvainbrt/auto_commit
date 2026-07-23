from __future__ import annotations

import json
import random
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

from scripts.generate_activity import (
    choose_commit_count,
    generate_events,
    generate_timestamps,
    parse_date,
    write_jsonl,
)

UTC = timezone.utc
TARGET_DATE = date(2026, 7, 22)
NOW = datetime(2026, 7, 23, 0, 17, tzinfo=UTC)


class GenerateActivityTests(unittest.TestCase):
    def test_commit_count_boundaries_are_inclusive(self) -> None:
        self.assertEqual(choose_commit_count(0, 0, rng=random.Random(1)), 0)
        self.assertEqual(choose_commit_count(10, 10, rng=random.Random(1)), 10)

        observed = {
            choose_commit_count(0, 10, rng=random.Random(seed))
            for seed in range(200)
        }
        self.assertIn(0, observed)
        self.assertIn(10, observed)
        self.assertTrue(observed.issubset(set(range(11))))

    def test_invalid_commit_boundaries_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            choose_commit_count(-1, 10, rng=random.Random(1))
        with self.assertRaises(ValueError):
            choose_commit_count(5, 4, rng=random.Random(1))

    def test_zero_commit_day_returns_no_events(self) -> None:
        events = generate_events(
            TARGET_DATE, 0, 0, rng=random.Random(1), now=NOW
        )
        self.assertEqual(events, [])

    def test_timestamps_are_ordered_and_valid(self) -> None:
        timestamps = generate_timestamps(
            TARGET_DATE, 10, rng=random.Random(2), now=NOW
        )
        parsed = [datetime.fromisoformat(value.replace("Z", "+00:00")) for value in timestamps]

        self.assertEqual(timestamps, sorted(timestamps))
        self.assertEqual(len(timestamps), len(set(timestamps)))
        self.assertTrue(all(value.tzinfo == UTC for value in parsed))

    def test_timestamps_stay_within_requested_date(self) -> None:
        timestamps = generate_timestamps(
            TARGET_DATE, 10, rng=random.Random(3), now=NOW
        )
        parsed = [datetime.fromisoformat(value.replace("Z", "+00:00")) for value in timestamps]

        self.assertTrue(all(value.date() == TARGET_DATE for value in parsed))
        self.assertTrue(all(value <= NOW for value in parsed))

    def test_current_day_timestamps_do_not_enter_the_future(self) -> None:
        current_now = datetime(2026, 7, 23, 0, 0, 5, tzinfo=UTC)
        timestamps = generate_timestamps(
            current_now.date(), 6, rng=random.Random(4), now=current_now
        )
        parsed = [datetime.fromisoformat(value.replace("Z", "+00:00")) for value in timestamps]

        self.assertTrue(all(value <= current_now for value in parsed))

    def test_jsonl_output_is_valid(self) -> None:
        events = generate_events(
            TARGET_DATE, 4, 4, rng=random.Random(5), now=NOW
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "events.jsonl"
            write_jsonl(output, events)
            decoded = [
                json.loads(line)
                for line in output.read_text(encoding="utf-8").splitlines()
            ]

        self.assertEqual(decoded, events)
        self.assertTrue(all(event["synthetic"] is True for event in decoded))

    def test_event_ids_are_unique(self) -> None:
        events = generate_events(
            TARGET_DATE, 10, 10, rng=random.Random(6), now=NOW
        )
        event_ids = [event["event_id"] for event in events]
        self.assertEqual(len(event_ids), len(set(event_ids)))
        self.assertTrue(all(value.startswith("synthetic-") for value in event_ids))

    def test_date_parser_rejects_non_iso_input(self) -> None:
        self.assertEqual(parse_date("2026-07-22"), TARGET_DATE)
        with self.assertRaises(ValueError):
            parse_date("22/07/2026")


if __name__ == "__main__":
    unittest.main()
