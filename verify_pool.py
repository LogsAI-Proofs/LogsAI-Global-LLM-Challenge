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
    identity_map = d.get('ticker_cik') if channel == 'us' else None
    companies = stratified_sample(d['pool'], seed, identity_map=identity_map)
    company_ids = [(identity_map or {}).get(c, c) for c in companies]
    print(f"{channel} seed={seed} selected={len(companies)} unique_companies={len(set(company_ids))}")
    for i, c in enumerate(companies, 1):
        print(f"  {i:02d}. {c}  ({company_ids[i-1]})")


def verify_manifest(channel: str):
    """校验 draw_manifest_{channel}.json：池/算法/清单哈希 + 用 seed 独立复算。"""
    mf = BASE / f'draw_manifest_{channel}.json'
    if not mf.exists():
        raise SystemExit(f"[FAIL] {channel}: manifest 不存在 ({mf.name})")
    m = json.loads(mf.read_text(encoding='utf-8'))
    d = load_pool(channel)
    identity_map = d.get('ticker_cik') if channel == 'us' else None
    errors = []

    if (m.get('pool') or {}).get('pool_sha256') != d['pool_sha256']:
        errors.append('pool_sha256 mismatch')
    algo = hashlib.sha256((BASE / 'sampling.py').read_bytes()).hexdigest()
    if (m.get('algorithm') or {}).get('sha256') != algo:
        errors.append('algorithm sha256 mismatch')

    companies = m.get('companies') or []
    if len(companies) != 12 or len(set(companies)) != 12:
        errors.append(f'companies 非 12 家唯一 (n={len(companies)})')
    if canonical_sha256(companies) != m.get('list_sha256'):
        errors.append('list_sha256 mismatch')

    company_ids = [(identity_map or {}).get(c, c) for c in companies]
    if len(set(company_ids)) != 12:
        errors.append('company_ids 非 12 个唯一企业')
    if company_ids != m.get('company_ids'):
        errors.append('company_ids 与 companies 的 CIK 映射不符')

    seed_string = (m.get('seed') or {}).get('seed_string', '')
    expected = stratified_sample(d['pool'], seed_string, identity_map=identity_map)
    if expected != companies:
        errors.append('按 seed 复算的清单与 manifest 不一致')

    if errors:
        print(f"[FAIL] {channel} manifest: " + '; '.join(errors))
        raise SystemExit(1)
    print(f"[OK] {channel} manifest: seed={seed_string} "
          f"list_sha256={m['list_sha256']} companies={len(companies)}")


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('action', choices=['verify', 'draw', 'verify-manifest'])
    ap.add_argument('channel', choices=['cn', 'us', 'all'])
    ap.add_argument('seed', nargs='?', default='')
    args = ap.parse_args()

    if args.action == 'verify':
        for ch in (['cn', 'us'] if args.channel == 'all' else [args.channel]):
            verify(ch)
    elif args.action == 'verify-manifest':
        for ch in (['cn', 'us'] if args.channel == 'all' else [args.channel]):
            verify_manifest(ch)
    else:
        if not args.seed:
            raise SystemExit("draw 需要 seed")
        for ch in (['cn', 'us'] if args.channel == 'all' else [args.channel]):
            draw(ch, args.seed)
