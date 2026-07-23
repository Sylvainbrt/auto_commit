#!/usr/bin/env python3
"""Generate transparent, synthetic activity records for a completed UTC day."""

from __future__ import annotations

import argparse
import json
import random
import sys
import uuid
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Dict, Sequence

UTC = timezone.utc
SYNTHETIC_MESSAGE = (
    "Synthetic activity generated for the contribution graph experiment"
)
COMMIT_MESSAGES = (
    "experiment: generate synthetic activity",
    "data: add automated test event",
    "chore: update contribution experiment log",
    "experiment: record simulated commit",
    "test: add synthetic activity sample",
)

Event = Dict[str, object]


def parse_date(value: str) -> date:
    """Parse an ISO 8601 calendar date."""
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"invalid date {value!r}; expected YYYY-MM-DD") from exc


def utc_now() -> datetime:
    """Return the current timezone-aware UTC time."""
    return datetime.now(UTC)


def resolve_target_date(value: str | None, *, now: datetime) -> date:
    """Resolve an explicit date or default to the previous completed UTC day."""
    now_utc = _as_utc(now)
    if value is None:
        return now_utc.date() - timedelta(days=1)
    return parse_date(value)


def validate_commit_bounds(min_commits: int, max_commits: int) -> None:
    """Validate inclusive commit-count bounds."""
    if min_commits < 0 or max_commits < 0:
        raise ValueError("commit counts must be non-negative")
    if min_commits > max_commits:
        raise ValueError("min-commits cannot be greater than max-commits")


def choose_commit_count(
    min_commits: int, max_commits: int, *, rng: random.Random
) -> int:
    """Choose an inclusive random commit count."""
    validate_commit_bounds(min_commits, max_commits)
    return rng.randint(min_commits, max_commits)


def generate_timestamps(
    target_date: date,
    count: int,
    *,
    rng: random.Random,
    now: datetime,
) -> list[str]:
    """Generate unique, sorted UTC timestamps that are never in the future."""
    if count < 0:
        raise ValueError("timestamp count must be non-negative")

    now_utc = _as_utc(now).replace(microsecond=0)
    day_start = datetime.combine(target_date, time.min, tzinfo=UTC)
    if day_start > now_utc:
        raise ValueError("target date cannot be in the future")

    day_end = day_start + timedelta(days=1)
    latest_allowed = min(day_end - timedelta(seconds=1), now_utc)
    available_seconds = int((latest_allowed - day_start).total_seconds()) + 1
    if count > available_seconds:
        raise ValueError(
            f"cannot generate {count} unique timestamps; only "
            f"{available_seconds} non-future seconds are available"
        )

    offsets = sorted(rng.sample(range(available_seconds), count))
    return [
        (day_start + timedelta(seconds=offset)).strftime("%Y-%m-%dT%H:%M:%SZ")
        for offset in offsets
    ]


def generate_events(
    target_date: date,
    min_commits: int,
    max_commits: int,
    *,
    rng: random.Random,
    now: datetime,
) -> list[Event]:
    """Generate synthetic event metadata for one day."""
    count = choose_commit_count(min_commits, max_commits, rng=rng)
    timestamps = generate_timestamps(target_date, count, rng=rng, now=now)
    event_ids: set[str] = set()
    events: list[Event] = []

    for timestamp in timestamps:
        event_id = _unique_event_id(rng, event_ids)
        event_ids.add(event_id)
        events.append(
            {
                "timestamp": timestamp,
                "event_id": event_id,
                "message": SYNTHETIC_MESSAGE,
                "commit_message": rng.choice(COMMIT_MESSAGES),
                "synthetic": True,
            }
        )

    return events


def write_jsonl(output: Path, events: Sequence[Event]) -> None:
    """Write one JSON object per event, replacing any previous output."""
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as stream:
        for event in events:
            stream.write(json.dumps(event, sort_keys=True))
            stream.write("\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate explicitly synthetic GitHub activity metadata as JSONL. "
            "The default target is the previous completed UTC day."
        )
    )
    parser.add_argument(
        "--date",
        help="target UTC date in YYYY-MM-DD format (default: previous UTC day)",
    )
    parser.add_argument("--min-commits", type=int, default=0)
    parser.add_argument("--max-commits", type=int, default=10)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--seed",
        type=int,
        help="optional deterministic random seed for testing",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    now = utc_now()

    try:
        target_date = resolve_target_date(args.date, now=now)
        rng = random.Random(args.seed)
        events = generate_events(
            target_date,
            args.min_commits,
            args.max_commits,
            rng=rng,
            now=now,
        )
        write_jsonl(args.output, events)
    except (OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2

    print(
        json.dumps(
            {
                "commit_count": len(events),
                "date": target_date.isoformat(),
                "output": str(args.output),
                "synthetic": True,
            },
            sort_keys=True,
        )
    )
    return 0


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    return value.astimezone(UTC)


def _unique_event_id(rng: random.Random, existing: set[str]) -> str:
    while True:
        candidate = f"synthetic-{uuid.UUID(int=rng.getrandbits(128), version=4)}"
        if candidate not in existing:
            return candidate


if __name__ == "__main__":
    raise SystemExit(main())
