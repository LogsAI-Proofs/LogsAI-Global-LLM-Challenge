# LogsAI Global LLM Challenge — 存证仓库

本仓库存放 LogsAI 全球大模型挑战赛（泛化性与确定性基准测试）的审计输出哈希存证，以及公开行业池快照。

## 行业池快照（冻结）

| 文件 | 说明 |
|---|---|
| `pool_cn.json` | A 股行业池快照：5,223 家，11 个 GICS Sector |
| `pool_us.json` | 美股行业池快照：6,506 家，仅纳入 SEC 10-K 公司 |
| `pool_manifest.json` | 冻结清单：算法哈希、GICS 哈希、两份池哈希 |
| `sampling.py` | 盲抽算法：11 个分类各 1 家 + 补充抽取 1 家 = 12 家 |
| `verify_pool.py` | 公开校验/复算脚本 |
| `POOL_BUILD.md` | 池构建口径与复算说明 |

```bash
# 校验两份池的哈希
python verify_pool.py verify all

# 用给定 seed 复算 12 家
python verify_pool.py draw cn "上证指数收盘价-20261127"
python verify_pool.py draw us "标普500收盘价-20261127"
```

## 完成判定与存证机制

### 完成信号契约

参赛系统对每个标的企业，输出一个 JSON 文件，**必含 `status` 完成信号字段**：

- `"status": "completed"` — 任务完成
- `"status": "failed"` — 任务失败

只有 `status == "completed"` 才判定完成，并对输出做哈希存证。缺 status 字段或非 completed 一律判未完成（防模型在长任务中遗忘完成信号）。

### 输出 7 项结论（对应挑战赛手册 11.2 输出标准）

1. 三年期三表（资产负债表/利润表/现金流量表）全部科目总数
2. 勾稽组清单：每个「父项 = Σ子项」带符号公式 + 平衡/不平衡标注
3. 平衡科目数量
4. 不平衡科目数量
5. 不平衡科目清单
6. 按重要性水平划分的重要不平衡科目数量
7. 各勾稽不平组的缺口金额

### 判定与存证脚本

`verify.py` — 公开判定脚本，所有参赛模型可复用：

```bash
python verify.py <模型输出JSON> <stock_code> <company_name>
```

- 判定 `status` 字段是否 completed
- 对输出文件做 SHA256 哈希
- 生成存证 manifest（含哈希 + 状态 + 时间戳）

## 公开透明

- 每个标的企业完成 → 哈希存证 → git commit/push 到本仓库
- 全程无人工干预（比赛期间不通过 CLI 调度）
- 任何第三方可复核：谁完成了、何时完成、输出哈希值多少
