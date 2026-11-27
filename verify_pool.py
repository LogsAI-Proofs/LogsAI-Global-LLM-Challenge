#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""公开行业池校验与复算。

用法：
    python verify_pool.py verify all
    python verify_pool.py verify cn
    python verify_pool.py draw cn "上证指数收盘价-20261127"
    python verify_pool.py draw us "标普500收盘价-20261127"
"""
import argparse
import hashlib
import json
from pathlib import Path

from sampling import stratified_sample

BASE = Path(__file__).resolve().parent


def canonical_sha256(pool: dict) -> str:
    s = json.dumps(pool, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def load_pool(channel: str) -> dict:
    f = BASE / f'pool_{channel}.json'
    d = json.loads(f.read_text(encoding='utf-8'))
    calc = canonical_sha256(d['pool'])
    if calc != d.get('pool_sha256'):
        raise SystemExit(f"[FAIL] {f.name}: pool_sha256 mismatch\n  file={d.get('pool_sha256')}\n  calc={calc}")
    return d


def verify(channel: str):
    d = load_pool(channel)
    print(f"[OK] {channel}: total={d['total_companies']} pool_sha256={d['pool_sha256']}")
    print(f"     sectors={d['sector_counts']}")


def draw(channel: str, seed: str):
    d = load_pool(channel)
    companies = stratified_sample(d['pool'], seed)
    print(f"{channel} seed={seed} selected={len(companies)}")
    for i, c in enumerate(companies, 1):
        print(f"  {i:02d}. {c}")


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('action', choices=['verify', 'draw'])
    ap.add_argument('channel', choices=['cn', 'us', 'all'])
    ap.add_argument('seed', nargs='?', default='')
    args = ap.parse_args()

    if args.action == 'verify':
        for ch in (['cn', 'us'] if args.channel == 'all' else [args.channel]):
            verify(ch)
    else:
        if not args.seed:
            raise SystemExit("draw 需要 seed")
        for ch in (['cn', 'us'] if args.channel == 'all' else [args.channel]):
            draw(ch, args.seed)
