#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
比赛完成判定 + 哈希存证（公开，供所有参赛模型复用）

用法:
  python verify.py <模型输出JSON> <stock_code> <company_name>

输出契约 —— 模型对每个标的企业输出一个 JSON 文件，必含 status 完成信号字段：
  {
    "status": "completed",          # 完成信号，必填，"completed" 或 "failed"
    "stock_code": "AAPL",
    "company_name": "Apple Inc.",
    "1_total_accounts": {"bs": n, "pl": n, "cf": n, "total": n},
    "2_reconciliation_groups": [{"parent": ..., "children": [...], "balanced": bool, "gap": ...}],
    "3_balanced_count": n,
    "4_unbalanced_count": n,
    "5_unbalanced_list": [...],
    "6_important_unbalanced_count": n,
    "7_gap_amounts": [{"parent": ..., "gap": ...}]
  }

完成判定：status == "completed" 才判定完成；缺 status 字段或非 "completed" 判定未完成。
判定后：对输出文件做 SHA256 哈希，生成存证 manifest（含哈希 + 时间戳），供 git 公开存证。
"""
import hashlib
import json
import os
import sys
from datetime import datetime


def sha256_file(path: str) -> str:
    """计算文件 SHA256 哈希（十六进制）。"""
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def parse_output(output_path: str):
    """解析模型输出，返回 (status, data)。"""
    with open(output_path, encoding='utf-8') as f:
        data = json.load(f)
    status = str(data.get('status', '')).strip().lower()
    return status, data


def is_completed(output_path: str) -> bool:
    """判定任务是否完成（status == 'completed'）。"""
    status, _ = parse_output(output_path)
    return status == 'completed'


def generate_proof(output_path: str, stock_code: str, company_name: str) -> dict:
    """哈希存证：生成 manifest（含 SHA256 + status + 时间戳）。"""
    status, _ = parse_output(output_path)
    sha = sha256_file(output_path)
    return {
        'stock_code': stock_code,
        'company_name': company_name,
        'status': status,
        'output_sha256': sha,
        'timestamp': datetime.now().isoformat(),
    }


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print('用法: python verify.py <模型输出JSON> <stock_code> <company_name>')
        sys.exit(1)
    output_path, stock_code, company_name = sys.argv[1], sys.argv[2], sys.argv[3]
    status, _ = parse_output(output_path)
    completed = status == 'completed'
    print(f'完成判定: {"完成" if completed else "未完成"} (status={status!r})')
    if completed:
        proof = generate_proof(output_path, stock_code, company_name)
        print('存证 manifest:')
        print(json.dumps(proof, ensure_ascii=False, indent=2))
        proof_path = os.path.splitext(output_path)[0] + '_proof.json'
        with open(proof_path, 'w', encoding='utf-8') as f:
            json.dump(proof, f, ensure_ascii=False, indent=2)
        print(f'manifest 已落盘: {proof_path}')
    else:
        print('任务未完成，不生成存证。')
