# 行业池构建说明（冻结版）

> 版本：V1.0 ｜ 冻结日期：2026-11-27
> 用途：公开行业基准池的构建口径、文件清单与复算方式；赛事期间不再变更。

---

## 一、构建口径

### A 股通道

- 范围：全部 A 股；
- 分类：申万一级行业 → GICS Sector；
- 结果：**5,223 家**，11 个 GICS Sector 全部非空；
- 快照：`pool_cn.json`。

### 美股通道

- 范围：**仅 SEC 10-K 报表公司**；
- 分类：SIC 前缀 → GICS Sector；
- 结果：**6,506 家**，11 个 GICS Sector 全部非空；
- 快照：`pool_us.json`。

### 明确不纳入

- **20-F / 40-F 公司**：不属于 10-K 通道，不纳入；
- 无 SIC 的公司；
- SIC 无法映射到 GICS 的公司；
- 没有 10-K 的公司。

> 美股 10,400 家的拆分：6,506 保留；1,394 无 SIC；94 SIC 未映射（8880 外国 ADR / 0000 封闭式基金）；2,406 无 10-K（主要为 20-F/40-F 外国发行人、基金、以及少数 ticker 指向新控股实体的公司）。

---

## 二、文件清单

| 文件 | 说明 |
|---|---|
| `pool_cn.json` | A 股池快照（含 `pool_sha256`、`sector_counts`） |
| `pool_us.json` | 美股池快照（含 `pool_sha256`、`sector_counts`） |
| `pool_manifest.json` | 冻结清单：算法哈希、GICS 哈希、两份池哈希 |
| `sampling.py` | 盲抽算法（11 个分类各 1 家 + 补充抽取 1 家 = 12 家） |
| `verify_pool.py` | 公开校验脚本：验哈希、复算 12 家清单 |
| `gics_mapping.json` | SIC/申万 → GICS 映射 |

---

## 三、复算与校验

1. 加载 `pool_cn.json` / `pool_us.json` 的 `pool` 字段；
2. 对 `pool` 做规范 JSON 序列化（`sort_keys=True`、无空格），计算 SHA-256；
3. 与快照内的 `pool_sha256`、`pool_manifest.json` 中的对应值比对；
4. 用 `sampling.py` 的 `stratified_sample(pool, seed)` 复算 12 家清单；
5. 算法哈希与 `pool_manifest.json` 的 `algorithm.sha256` 比对。

---

## 四、冻结规则

- 赛事期间，`pool_cn.json`、`pool_us.json`、`sampling.py`、`gics_mapping.json` 不再变更；
- 如需变更，必须重新生成快照、更新 `pool_manifest.json`、重新公布，并说明旧快照作废；
- 公开仓库保存以上文件与哈希，任何第三方可下载复算。

---

## 五、已知边界

- 美股以“当前 ticker 对应的 CIK 是否有 10-K”为准；极少数 ticker 指向新控股实体、而 10-K 仍在旧运营 CIK 的公司（如 XOM），会被排除。这是当前口径的已知边界；
- 20-F/40-F 的 XBRL 数据抓取端点有数据，但现有解析层只支持 `us-gaap` + `form=10-K` + `USD`，因此暂不纳入；如需纳入，应另做 IFRS 适配层，而不是混入本池。
