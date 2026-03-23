"""
Starter fusion script for TOP + SIDE camera events.

Purpose
- Read placeholder events from a top camera detector and a side camera detector
- Fuse them into shot-centric records
- Validate against JSON schema later if you want
- Save line-delimited JSON for downstream stats / overlays

This is deliberately simple. It is scaffolding, not magic.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
import json
import uuid


@dataclass
class TopState:
    ts_ms: int
    balls_remaining: int
    balls: list
    confidence: float


@dataclass
class SideEvent:
    ts_ms: int
    event_type: str
    confidence: float


@dataclass
class FusedShot:
    event_id: str
    timestamp_utc: str
    table_id: str
    camera_sources: dict
    phase: str
    side_events: list
    table_state_before: dict
    table_state_after: dict
    confidence: float


def nearest_top_state(states: List[TopState], ts_ms: int, window_ms: int) -> Optional[TopState]:
    candidates = [s for s in states if abs(s.ts_ms - ts_ms) <= window_ms]
    if not candidates:
        return None
    return sorted(candidates, key=lambda s: abs(s.ts_ms - ts_ms))[0]


def group_side_events_into_shots(events: List[SideEvent], max_gap_ms: int = 2000) -> List[List[SideEvent]]:
    if not events:
        return []

    events = sorted(events, key=lambda e: e.ts_ms)
    groups = [[events[0]]]

    for ev in events[1:]:
        if ev.ts_ms - groups[-1][-1].ts_ms <= max_gap_ms:
            groups[-1].append(ev)
        else:
            groups.append([ev])

    return groups


def build_fused_records(
    top_states: List[TopState],
    side_events: List[SideEvent],
    table_id: str = "mesa_1",
    top_source: str = "top_cam",
    side_source: str = "side_cam",
    top_window_ms: int = 1000,
) -> List[FusedShot]:
    shot_groups = group_side_events_into_shots(side_events)
    fused: List[FusedShot] = []

    for group in shot_groups:
        shot_ts = group[0].ts_ms
        before_state = nearest_top_state(top_states, shot_ts - 500, top_window_ms)
        after_state = nearest_top_state(top_states, shot_ts + 500, top_window_ms)

        if not before_state or not after_state:
            continue

        conf = min(
            [before_state.confidence, after_state.confidence] + [ev.confidence for ev in group]
        )

        fused.append(
            FusedShot(
                event_id=str(uuid.uuid4()),
                timestamp_utc=datetime.now(timezone.utc).isoformat(),
                table_id=table_id,
                camera_sources={"top": top_source, "side": side_source},
                phase="shot",
                side_events=[ev.event_type for ev in group],
                table_state_before={
                    "balls_remaining": before_state.balls_remaining,
                    "balls": before_state.balls,
                    "turn_player_id": None,
                    "rule_mode": None,
                },
                table_state_after={
                    "balls_remaining": after_state.balls_remaining,
                    "balls": after_state.balls,
                    "turn_player_id": None,
                    "rule_mode": None,
                },
                confidence=conf,
            )
        )

    return fused


def save_jsonl(records: List[FusedShot], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(asdict(rec), ensure_ascii=False) + "\n")


def demo() -> None:
    # Fake top-camera states
    top_states = [
        TopState(ts_ms=1000, balls_remaining=10, balls=[{"id": "cue", "x": 0.5, "y": 0.5, "visible": True, "confidence": 0.98}], confidence=0.95),
        TopState(ts_ms=2000, balls_remaining=9,  balls=[{"id": "cue", "x": 0.55, "y": 0.52, "visible": True, "confidence": 0.98}], confidence=0.94),
        TopState(ts_ms=4000, balls_remaining=9,  balls=[{"id": "cue", "x": 0.57, "y": 0.50, "visible": True, "confidence": 0.97}], confidence=0.96),
    ]

    # Fake side-camera events
    side_events = [
        SideEvent(ts_ms=1500, event_type="player_addressing_shot", confidence=0.91),
        SideEvent(ts_ms=1700, event_type="cue_forward_motion", confidence=0.88),
        SideEvent(ts_ms=1800, event_type="ball_contact_likely", confidence=0.86),
    ]

    fused = build_fused_records(top_states, side_events)
    save_jsonl(fused, Path("data/processed/events.jsonl"))
    print(f"Saved {len(fused)} fused shot records to data/processed/events.jsonl")


if __name__ == "__main__":
    demo()
