# -*- coding: utf-8 -*-
"""赛事日指数种子双源取数。

CN：新浪 s_sh000001 + 腾讯 sh000001 + 东财 1.000001
US：腾讯 usINX + 东财 100.SPX
（新浪 int_sp500 实测与腾讯/东财严重不一致，不再作为美股种子源）

输出：每通道 {value, quote_date, sources, fetched_at}；多源不一致时抛错。
"""
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import requests

H = {'User-Agent': 'Mozilla/5.0'}
SINA_H = {**H, 'Referer': 'https://finance.sina.com.cn/'}


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def _sina_cn():
    r = requests.get('https://hq.sinajs.cn/list=s_sh000001', headers=SINA_H, timeout=20)
    r.encoding = 'gbk'
    m = re.search(r'="([^"]*)"', r.text)
    if not m:
        raise ValueError('新浪上证指数解析失败')
    parts = m.group(1).split(',')
    return {'source': 'sina', 'value': float(parts[1]), 'raw': r.text, 'raw_sha256': _sha(r.text),
            'quote_date': None, 'quote_time': None}


def _tencent(symbol: str, tz: str):
    r = requests.get(f'https://qt.gtimg.cn/q={symbol}', headers=H, timeout=20)
    r.encoding = 'gbk'
    m = re.search(r'v_[^=]+="([^"]*)"', r.text)
    if not m:
        raise ValueError(f'腾讯 {symbol} 解析失败')
    parts = m.group(1).split('~')
    value = float(parts[3])
    tm = re.search(r'(\d{4}-?\d{2}-?\d{2})[ T]?(\d{2}:?\d{2}:?\d{2})', m.group(1))
    quote_date = quote_time = None
    if tm:
        d, t = tm.group(1), tm.group(2)
        quote_date = f'{d[:4]}-{d[4:6]}-{d[6:]}' if '-' not in d else d
        quote_time = t if ':' in t else f'{t[:2]}:{t[2:4]}:{t[4:6]}'
    return {'source': f'tencent:{symbol}', 'value': value, 'raw': r.text, 'raw_sha256': _sha(r.text),
            'quote_date': quote_date, 'quote_time': quote_time}


def _eastmoney(secid: str, tz: str):
    url = ('https://push2.eastmoney.com/api/qt/stock/get?'
           f'secid={secid}&fields=f43,f57,f58,f86')
    r = requests.get(url, headers=H, timeout=20)
    d = r.json().get('data') or {}
    if 'f43' not in d:
        raise ValueError(f'东财 {secid} 解析失败')
    value = float(d['f43']) / 100.0
    dt = datetime.fromtimestamp(int(d['f86']), tz=timezone.utc).astimezone(ZoneInfo(tz))
    return {'source': f'eastmoney:{secid}', 'value': value, 'raw': r.text, 'raw_sha256': _sha(r.text),
            'quote_date': dt.date().isoformat(), 'quote_time': dt.strftime('%H:%M:%S')}


def _merge(channel: str, sources: list, tolerance: float = 0.05):
    vals = [s['value'] for s in sources]
    if max(vals) - min(vals) > max(tolerance, max(vals) * 1e-4):
        raise ValueError(f'{channel} 多源种子不一致: ' + ', '.join(f"{s['source']}={s['value']}" for s in sources))
    dated = [s for s in sources if s.get('quote_date')]
    dates = sorted({s['quote_date'] for s in dated})
    if len(dates) > 1:
        raise ValueError(f'{channel} 多源日期不一致: {dates}')
    # 多源取中位数，再统一到 2 位小数作为 canonical seed。
    # 原始值保留在 raw_value / sources 中，seed 字符串必须使用 canonical 值，
    # 否则 3606.4868（新浪）与 3606.49（腾讯/东财）会生成不同清单。
    vals_sorted = sorted(vals)
    raw_value = vals_sorted[len(vals_sorted) // 2]
    value = round(raw_value, 2)
    prefix = '上证指数收盘价' if channel == 'cn' else '标普500收盘价'
    return {
        'value': value,
        'raw_value': raw_value,
        'seed_string': f'{prefix}-{value:.2f}',
        'quote_date': dates[0] if dates else None,
        'sources': sources,
        'fetched_at': datetime.now(timezone.utc).isoformat(),
    }


def fetch_seed_manifest():
    cn = _merge('cn', [_sina_cn(), _tencent('sh000001', 'Asia/Shanghai'),
                       _eastmoney('1.000001', 'Asia/Shanghai')])
    us = _merge('us', [_tencent('usINX', 'America/New_York'),
                       _eastmoney('100.SPX', 'America/New_York')])
    return {'cn': cn, 'us': us}


if __name__ == '__main__':
    print(json.dumps(fetch_seed_manifest(), ensure_ascii=False, indent=2)[:4000])
