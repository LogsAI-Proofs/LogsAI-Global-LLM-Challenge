#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""赛事日公开抽签：取当日指数收盘价 → 调用冻结算法/池 → 生成 draw manifest。

用法：
    python draw_event_day.py --channel cn --draw-date 2026-11-27
    python draw_event_day.py --channel us --draw-date 2026-11-25
    python draw_event_day.py --channel all --draw-date 2026-11-27 --allow-mismatch
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from index_seed_fetcher import fetch_seed_manifest
from sampling import stratified_sample, get_algorithm_sha256

BASE = Path(__file__).resolve().parent


def canonical_sha(obj) -> str:
    s = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def load_pool(channel: str) -> dict:
    f = BASE / f'pool_{channel}.json'
    d = json.loads(f.read_text(encoding='utf-8'))
    calc = canonical_sha(d['pool'])
    if calc != d.get('pool_sha256'):
        raise SystemExit(f"[FAIL] {f.name} pool_sha256 mismatch")
    return d


def draw(channel: str, draw_date: str, allow_mismatch: bool):
    seed = fetch_seed_manifest()[channel]
    qd = seed.get('quote_date')
    if draw_date and qd != draw_date:
        msg = f"{channel} 指数日期={qd}，要求 draw_date={draw_date}"
        if not allow_mismatch:
            raise SystemExit(f"[FAIL] {msg}（休市/跨日，拒绝抽签）")
        print(f"[WARN] {msg}，允许 mismatch 继续（仅测试用）")

    pool_doc = load_pool(channel)
    companies = stratified_sample(pool_doc['pool'], seed['seed_string'])
    if len(companies) != 12 or len(set(companies)) != 12:
        raise SystemExit(f"[FAIL] {channel} 选出 {len(companies)} 家，非 12 家唯一")

    code2sec = {c: s for s, arr in pool_doc['pool'].items() for c in arr}
    sectors = [code2sec.get(c) for c in companies[:11]]
    if len(set(sectors)) != 11:
        raise SystemExit(f"[FAIL] {channel} 前 11 家未覆盖 11 个分类: {sectors}")

    manifest = {
        'channel': channel,
        'draw_date': qd,
        'seed': {
            'value': seed['value'],
            'raw_value': seed['raw_value'],
            'seed_string': seed['seed_string'],
            'quote_date': qd,
            'sources': [
                {k: s.get(k) for k in ('source', 'value', 'quote_date', 'quote_time', 'raw_sha256')}
                for s in seed['sources']
            ],
            'fetched_at': seed['fetched_at'],
        },
        'pool': {
            'file': f'pool_{channel}.json',
            'total': pool_doc['total_companies'],
            'pool_sha256': pool_doc['pool_sha256'],
        },
        'algorithm': {'file': 'sampling.py', 'sha256': get_algorithm_sha256()},
        'companies': companies,
        'sectors_first_11': sectors,
        'list_sha256': canonical_sha(companies),
        'created_at': datetime.now(timezone.utc).isoformat(),
    }
    out = BASE / f'draw_manifest_{channel}.json'
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"[OK] {channel} manifest: {out}")
    print(f"     seed={seed['seed_string']} list_sha256={manifest['list_sha256']}")
    print(f"     companies={companies}")
    return manifest


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--channel', choices=['cn', 'us', 'all'], default='all')
    ap.add_argument('--draw-date', default='', help='YYYY-MM-DD；为空则不校验')
    ap.add_argument('--allow-mismatch', action='store_true')
    args = ap.parse_args()
    for ch in (['cn', 'us'] if args.channel == 'all' else [args.channel]):
        draw(ch, args.draw_date, args.allow_mismatch)
