# GICS 行业归并映射说明

## 背景

《全球大模型挑战赛》执行章程第十六章规定，行业基准池的**行业分类标准为 GICS**（Global Industry Classification Standard，全球行业分类标准）。

但两个通道的实际财报数据源并非 GICS 标准：

| 通道 | 数据源 | 原生行业分类 |
|------|--------|-------------|
| 美股（SEC 通道） | SEC EDGAR / company tickers | SIC（美国标准行业分类，4 位码） |
| A股（中国通道） | 新浪财经 | 新浪行业板块（约 50 个行业） |

因此需将 SIC 与新浪行业**统一归并到 GICS 的 11 个 Sector**，作为行业基准池的分层依据。

## GICS 行业分类（11 个 Sector）

| 中文 | 英文（GICS Sector） |
|------|---------------------|
| 能源 | Energy |
| 材料 | Materials |
| 工业 | Industrials |
| 可选消费 | Consumer Discretionary |
| 必需消费 | Consumer Staples |
| 医疗保健 | Health Care |
| 金融 | Financials |
| 信息技术 | Information Technology |
| 通信服务 | Communication Services |
| 公用事业 | Utilities |
| 房地产 | Real Estate |

> 说明：GICS 标准为 11 个 Sector。执行章程所称「分为 12 类」按本 11 Sector 口径执行（11 类），如需严格 12 类，可将「通信服务」拆分为「电信服务 + 媒体娱乐」两类，本映射未拆分，保持 GICS 官方 11 Sector 口径。

## 归并规则

### 美股：SIC → GICS

按 SIC 的**前 2 位大类码**归并到 GICS Sector。映射表见 `gics_mapping.json` 的 `sic_to_gics`。

- 归并原则：SIC 2 位大类对应 GICS Sector 的标准对应关系；
- 示例：`13`（油气开采）→ 能源；`36`（电子设备）→ 信息技术；`60-67`（金融）→ 金融；`80-89`（医疗）→ 医疗保健。

### A股：申万一级行业 → GICS

按申万一级行业（31 个）归并到 GICS Sector。映射表见 `gics_mapping.json` 的 `sw_industry_to_gics`。

- 归并原则：按行业的经济实质归属 GICS Sector；
- 示例：电子/计算机 → 信息技术；医药生物 → 医疗保健；银行/非银金融 → 金融；食品饮料/农林牧渔 → 必需消费；煤炭/石油石化 → 能源。
- 覆盖范围：申万一级行业成分股覆盖约 5223 家 A股（约 94% 全 A股），较新浪行业成分股（2941 家）覆盖更全。

## 局限性说明

1. **SIC 是近似**：SIC 并非 GICS 的严格子集，个别 SIC 大类与 GICS Sector 存在边界交叉（如 SIC `38` 医疗仪器归医疗保健、SIC `36` 电子设备归信息技术），本映射取主归属，可能存在边界企业的个别误差；
2. **新浪行业为手工归并**：新浪行业板块是新浪自有分类（非 GICS），归并到 GICS Sector 采用人工映射，主观边界（如「印刷包装」归可选消费）可能存在可争议之处，欢迎第三方复核并提出修正；
3. **归并映射公开可复算**：本映射表 + 盲抽算法 + 企业名单三要素公开于 GitHub，任何第三方可依据公开原始数据复核行业归属与盲抽结果。

## 文件

- `gics_mapping.json`：GICS Sector 定义 + SIC→GICS + 新浪行业→GICS 归并映射表
- `sampling.py`：分层盲抽算法（按行业分层，每类抽 1 家）
- `industry_pool`：行业基准池 = 全部企业（美股 us_listings 10399 家 / A股新浪成分股）按上述归并映射分层
