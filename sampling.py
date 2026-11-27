# -*- coding: utf-8 -*-
"""
盲抽算法（开源实现）

分层抽样：11 个分类各抽 1 家，共 11 家；再补充抽取 1 家，共 12 家。
随机种子：A 股通道 = 上证指数收盘价；SEC 通道 = 标普 500 收盘价。

说明：
  - 用 sha256(种子) 初始化伪随机数发生器，保证可复现；
  - 行业按 GICS_SECTOR_ORDER 固定顺序，候选按代码字典序排序后再抽；
  - 公开「种子 + 算法 + 企业名单」三要素，任何人可复算得到一致清单。

使用方式：
    companies = stratified_sample(pool, seed)
"""

import hashlib
import random
from pathlib import Path

# GICS 官方 Sector 顺序。排序固定后，同一 seed 的抽样顺序固定。
# 当前 gics_mapping.json 有 11 个 Sector；第 12 家为补充抽取，不新增 Sector。
GICS_SECTOR_ORDER = [
    '能源', '材料', '工业', '可选消费', '必需消费', '医疗保健',
    '金融', '信息技术', '通信服务', '公用事业', '房地产',
]

ALGORITHM_VERSION = '1.0.0'


def _ordered_sectors(pool: dict) -> list:
    """按 GICS 固定顺序排列非空行业；未知行业按名称排序追加。"""
    ordered = [s for s in GICS_SECTOR_ORDER if pool.get(s)]
    extras = sorted(s for s in pool if s not in GICS_SECTOR_ORDER and pool.get(s))
    return ordered + extras


def _supplement_candidate(pool, selected, seed):
    """从全部未选企业中再抽 1 家，作为第 12 家补充企业。

    使用独立 RNG（seed + '|supplement'），与 11 个行业代表的抽取互不干扰；
    候选按行业固定顺序 + 代码字典序排列，保证可复现。
    """
    items = []
    for industry in _ordered_sectors(pool):
        for code in sorted(str(c) for c in pool[industry]):
            if code not in selected:
                items.append((industry, code))
    if not items:
        return None
    rng = random.Random(hashlib.sha256(f"{seed}|supplement".encode('utf-8')).hexdigest())
    return items[rng.randrange(len(items))][1]


def stratified_sample(pool, seed, include_supplement=True):
    """分层抽样：11 个 GICS 行业各抽 1 家，再抽 1 家补充企业，共 12 家。

    用 sha256(seed) 初始化随机数发生器，保证可复现。
    行业按 GICS_SECTOR_ORDER 固定顺序；候选先按代码字典序排序，
    再抽样——保证同一 seed + 同一池快照的输出完全一致。

    第 12 家是补充抽取：从全部未选企业中再抽 1 家，不要求来自第 12 个分类。
    """
    rng = random.Random(hashlib.sha256(str(seed).encode('utf-8')).hexdigest())
    selected = []
    for industry in _ordered_sectors(pool):
        candidates = sorted(str(c) for c in pool[industry])
        idx = rng.randrange(len(candidates))
        selected.append(candidates[idx])

    if include_supplement:
        supplement = _supplement_candidate(pool, set(selected), seed)
        if supplement is not None:
            selected.append(supplement)
    return selected


def get_algorithm_sha256() -> str:
    """返回当前 sampling.py 的 SHA-256，供 draw manifest 冻结算法版本。"""
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


if __name__ == '__main__':
    # 示例用法（占位数据，仅演示接口）
    pool = {f'行业{i:02d}': [f'{i:02d}-{j:03d}' for j in range(100)] for i in range(12)}
    print(stratified_sample(pool, seed='上证指数收盘价-20261118'))
