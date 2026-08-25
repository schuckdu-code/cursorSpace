#!/usr/bin/env python3
"""从 heroine-cards.md 随机抽卡。多人时尽量错开（处女+婚姻+单身）。用户筛选优先。"""

from __future__ import annotations

import argparse
import random
import re
from pathlib import Path

CARDS_PATH = Path(__file__).with_name("heroine-cards.md")
HEADING = re.compile(r"^##\s+(\d+)\.\s+(.+)$")
FIELD = re.compile(r"^-\s+\*\*(.+?)\*\*[：:]\s*(.+)$")


def parse_cards(text: str) -> list[dict]:
    cards: list[dict] = []
    current: dict | None = None
    for line in text.splitlines():
        m = HEADING.match(line.strip())
        if m:
            if current:
                cards.append(current)
            current = {
                "id": int(m.group(1)),
                "heading": m.group(2).strip(),
                "姓名": m.group(2).strip(),
            }
            continue
        if current is None:
            continue
        fm = FIELD.match(line.strip())
    if fm:
            current[fm.group(1)] = fm.group(2).strip()
            if fm.group(1) == "姓名":
                current["姓名"] = fm.group(2).split("（")[0].strip()
    if current:
        cards.append(current)
    return cards


def norm(value: str | None) -> str:
    if not value:
        return ""
    return value.replace(" ", "").strip()


def combo(card: dict) -> tuple[str, str, str]:
    return (
        norm(card.get("是否处女")),
        norm(card.get("婚姻状态")),
        norm(card.get("是否单身")),
    )


def yn_match(got: str, want: str) -> bool:
    want = norm(want)
    got = norm(got)
    yes = {"是", "处女", "true", "1", "yes"}
    no = {"否", "非处女", "false", "0", "no"}
    if want in yes:
        return got in yes or got.startswith("是")
    if want in no:
        return got in no or got.startswith("否")
    return want in got or got == want


def filter_cards(cards: list[dict], args: argparse.Namespace) -> list[dict]:
    out = cards
    if args.ids:
        want = {int(x) for x in args.ids.split(",") if x.strip()}
        out = [c for c in out if c["id"] in want]
    if args.exclude:
        ban = {int(x) for x in args.exclude.split(",") if x.strip()}
        out = [c for c in out if c["id"] not in ban]
    if args.virgin:
        out = [c for c in out if yn_match(c.get("是否处女", ""), args.virgin)]
    if args.marriage:
        key = norm(args.marriage)
        out = [c for c in out if key in norm(c.get("婚姻状态", ""))]
    if args.single:
        out = [c for c in out if yn_match(c.get("是否单身", ""), args.single)]
    return out


def pick_diverse(pool: list[dict], n: int) -> list[dict]:
    if n <= 0:
        return []
    remaining = pool[:]
    random.shuffle(remaining)
    chosen: list[dict] = []
    used: set[tuple[str, str, str]] = set()
    while remaining and len(chosen) < n:
        diverse = [c for c in remaining if combo(c) not in used]
        pick_from = diverse if diverse else remaining
        card = random.choice(pick_from)
        chosen.append(card)
        used.add(combo(card))
        remaining = [c for c in remaining if c["id"] != card["id"]]
    return chosen


def format_card(card: dict) -> str:
    cid = card["id"]
    name = card.get("姓名", card.get("heading", ""))
    v, m, s = combo(card)
    return f"{cid}\t{name}\t处女:{v}\t婚姻:{m}\t单身:{s}"


def main() -> None:
    parser = argparse.ArgumentParser(description="随机抽取女主人物卡")
    parser.add_argument("-n", "--count", type=int, default=1, help="抽取人数")
    parser.add_argument("--virgin", help="筛选是否处女：是/否")
    parser.add_argument("--marriage", help="筛选婚姻状态，如：未婚/已婚/恋爱中/订婚/离异")
    parser.add_argument("--single", help="筛选是否单身：是/否")
    parser.add_argument("--ids", help="仅从这些编号抽，逗号分隔")
    parser.add_argument("--exclude", help="排除编号，逗号分隔")
    args = parser.parse_args()

    cards = parse_cards(CARDS_PATH.read_text(encoding="utf-8"))
    pool = filter_cards(cards, args)
    if not pool:
        raise SystemExit("筛选后没有可用人物卡，放宽条件后再抽。")
    n = min(max(args.count, 1), len(pool))
    picked = pick_diverse(pool, n)
    for card in picked:
        print(format_card(card))


if __name__ == "__main__":
    main()
