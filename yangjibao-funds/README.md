# 养基宝（YangJiBao）基金查询工具

> 作者：Douyin [@kangkangyubo](https://www.douyin.com/user/kangkangyubo)

> 通过微信扫码登录养基宝 API，批量查询个人基金持仓、盘中估值、指数行情。

---

## 功能特性

- 🔐 **微信扫码登录**，Token 自动保存，无需重复登录
- 📊 **个人持仓查询**：账户汇总、持仓明细、盈亏分析
- 📈 **盘中估值**：白天实时估值，收盘后切换净值
- 🌍 **指数行情**：A股/港股/美股主要指数实时涨跌
- 📁 **导出支持**：JSON / CSV 格式导出
- 🤖 **OpenClaw Skill**：可作为 AI Agent 工具接入

---

## 环境要求

- Python 3.8+
- `requests` 库
- `qrcode[pil]` 库（可选，用于终端内显示二维码）

```bash
pip install requests qrcode[pil]
```

---

## 快速开始

### 1. 微信扫码登录

```bash
python scripts/yjb_login.py
```

脚本会：
1. 请求养基宝服务器生成登录二维码
2. 在终端打印 ASCII 二维码（若 `qrcode` 已安装）
3. 同时输出在线二维码链接（可复制到浏览器打开）
4. 轮询扫码状态，扫码成功后 Token 自动保存到 `~/.yjb_token.json`

> Token 默认有效期较长，日常使用无需重复登录。

### 2. 查询持仓数据

```bash
python scripts/yjb_fetch.py          # 打印分析结果
python scripts/yjb_fetch.py --json    # 导出 JSON
python scripts/yjb_fetch.py --csv     # 导出 CSV
```

---

## API 说明

本工具使用养基宝两类 API：

### 数据源 A：公网行情（无需登录）

| Base URL | 用途 |
|----------|------|
| `https://app-api.yangjibao.com` | 基金净值、指数行情、板块排行 |

### 数据源 B：个人持仓（需微信扫码登录）

| Base URL | 用途 |
|----------|------|
| `http://browser-plug-api.yangjibao.com` | 个人持仓、账户汇总、收益分析 |

---

## 净值日期规则

| 基金类型 | 说明 |
|----------|------|
| A股基金 | 净值日 = 最近交易日，当日 19:00~22:00 发布 |
| QDII 基金 | 净值滞后 2~3 个交易日，以 `true_valuation_date` 为准 |
| 盘中估值 | `vgsz`/`vgszzl` 为当日盘中估算，收盘后更新为真实净值 |

> 💡 建议 **20:00 后** 查询，可获取完整当日净值。

---

## 已知问题

| 问题 | 原因 | 解决 |
|------|------|------|
| API 返回 404 | 缺少签名 Header | 确保 `Request-Time`、`Request-Sign`、`Authorization` 三个 Header 齐全 |
| Token 失效 | Token 过期 | 重新运行 `yjb_login.py` 扫码 |
| 签名错误 | 签名 path 含 query string | 签名时 path 去掉 `?` 及之后部分 |

---

## OpenClaw Agent 接入

本项目同时是一个 **OpenClaw Skill**。

将本目录配置为 Agent 的工具 Skill 后，可以直接用自然语言查询基金：

- "查一下我的基金"
- "今天基金涨跌"
- "我的持仓怎么样了"

具体配置方式参考 [OpenClaw 文档](https://docs.openclaw.ai)。

---

## 免责声明

本工具仅供个人学习与研究使用，请遵守养基宝服务条款。持仓数据仅在本地处理，不会上传到任何第三方服务器。
