# 🗺️ POI 精确地图（poi-precision-map）

> 把「**找出某地区所有 X，一家家精确标到地图上**」变成一份**逐点核实过的交互式 HTML 地图** —— 无 API 密钥、无代理、无运行时地理编码。一个独立文件，随时打开、永久保存、随意分享。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![地图引擎](https://img.shields.io/badge/%E5%9C%B0%E5%9B%BE%E5%BC%95%E6%93%8E-Leaflet%201.9-199900.svg)](https://leafletjs.com/)
[![免密钥](https://img.shields.io/badge/API%20%E5%AF%86%E9%92%A5-%E4%B8%8D%E9%9C%80%E8%A6%81-success.svg)](#为什么不需要密钥)
[![坐标系](https://img.shields.io/badge/%E5%9D%90%E6%A0%87-GCJ--02%20%E9%93%81%E5%BE%8B-red.svg)](#坐标系铁律)

**[English](README.md)** · [示例地图：深圳高校分布](examples/shenzhen-universities.html) · [Skill 规范（SKILL.md）](SKILL.md)

---

## 这是什么

一个 **Agent Skill**（`SKILL.md` + 模板，即拷即用，兼容 Claude Code、TRAE、WorkBuddy 等所有支持 Agent Skills 约定的智能体），把一句自然语言变成一份真实可交付的地图：

> *「标出深圳所有的大学，一家家精确到地址」* → 一份自包含的 HTML 文件：每所高校都按真实地址单独地理编码、编号、标注置信度与来源、交叉核实，交付前经脚本自动校验。

| | |
|---|---|
| **输入** | 「把深圳所有高校一家家标到地图上」 |
| **输出** | [`examples/shenzhen-universities.html`](examples/shenzhen-universities.html) —— 13 个编号坐标点、4 个分类图例，每点含地址、GCJ-02 坐标、办学状态、置信度、来源；侧边列表可搜索、可一键导出 CSV、`file://` 双击即开。另有 2 所高校**未上图、只在交付说明中列明**（1 所在建无确定校址、1 所已停止招生）——这正是 skill「零编造」规则的体现。 |

## 为什么会有这个 Skill（真实翻车现场）

大多数 AI 生成的地图**离开聊天窗口就死**。一次典型的生成会手写一个腾讯地图 SDK 页面：`serviceHost: 'http://127.0.0.1:…'`，再在**运行时**调 `geocoder.getLocation()`。在宿主 App 里，本地代理让它看起来能跑；文件一旦被拿到外部浏览器打开 → 所有地理编码请求被拒 → **一个坐标点都渲染不出来，一张空白图**。

这个 Skill 从结构上让这种翻车**不可能发生**：

1. **所有坐标在生成期就解析完毕**，以静态 JSON 块烤进 HTML；
2. **Leaflet + 高德公开瓦片** —— 不要 SDK、不要密钥、不要代理、不要账号；
3. 交付物必须能在 `file://` 下运行，配套 [校验脚本](references/validate.py) 机械式强制检查。

## 特性

- **逐点精确** —— 每个地点按真实街道门牌单独地理编码，绝不用「区中心大差不差」的近似坐标，也不做气泡聚合糊弄
- **免密钥、可携带** —— 单个 HTML 文件，双击就能在任何浏览器打开，永久有效
- **数据可信**
  - 每点带 `conf`（高/中/低）置信度和 `src` 来源标签
  - 交叉验证规则写死在 skill 里：优先官方名录，非官方信息必须在 ≥2 个独立来源间反复核实
  - 页眉显示 `asof` 数据采集日期，数据新鲜度一目了然
- **Top-N 可复现** —— 「前 30」必须先说清排序口径（`META.rankedBy`）和收录边界（`META.catDef`），两者渲染在页眉；同一份需求跑两遍，得到同一份名单
- **坐标系铁律（GCJ-02）** —— 高德/腾讯坐标直接用；WGS-84、BD-09 先转换；绝不混用
- **零编造** —— 无法精确定位的地点不上图、在交付说明中列明原因，绝不瞎编坐标
- **脚本校验** —— 条数、ID 连续性、重复检测（连锁店感知）、弹窗字段完整性、违禁模式（原生对话框、厂商 SDK、运行时地理编码、代理依赖）
- **实用 UI** —— 编号图钉、富信息弹窗、可搜索侧栏点击飞行、一键适配全图、CSV 导出、多分类图例、手机响应式布局、界面语言跟随对话

## 安装

把本仓库拷进你的智能体技能目录：

```bash
# Claude Code
git clone https://github.com/delicious-hml/poi-precision-map.git \
  ~/.claude/skills/poi-precision-map

# TRAE / WorkBuddy —— 放到你的 agent 技能目录，例如
# C:\Users\<你>\.workbuddy\skills\poi-precision-map
```

自动生效，无需构建、无任何依赖 —— 只有 `SKILL.md`、HTML 模板、提示词模板和一个 Python 校验脚本。

## 使用

对支持技能的智能体说任意「**某地区所有 X，逐点上图**」类需求：

- 「标出深圳南山区所有的三甲医院，一家家精确到地址」
- 「上海市浦东新区所有充电站分布图，逐点标注」
- 「深圳前 30 大消费电子企业分布图」（skill 会先追问排序口径，再开始生成）
- 「画出广东省所有 5A 景区分布图」

也可以直接用这份填空式[提示词模板](references/prompt_template.md)启动批量任务。

## 工作流程

```
你：「把某地区所有 X 一家家标上图」
      │
      ▼
[1] 确认 地区 / 类目 / 数量 N / 排序口径 / 收录边界
      │
      ▼
[2] 调研 —— 按类目选权威来源
    （工商名录、官网、卫健委名录…），交叉核实
      │
      ▼
[3] 逐点地理编码到 GCJ-02，真实地址 → 经纬度
    （定位不了的点：剔除并说明，绝不瞎编）
      │
      ▼
[4] 数据注入冻结模板 —— 只替换 JSON 数据块，
    不改 HTML 结构
      │
      ▼
[5] validate.py —— 条数 / ID / 坐标 / 重复 /
    弹窗占位符 / 违禁模式 / META 完整性
      │
      ▼
[6] 肉眼终检 → 交付单个独立 HTML 文件
```

## 数据模型

每个地点是一个 JSON 对象，注入模板的 `<script id="places-data">` 块：

```json
{
  "id": 1,
  "name": "南方科技大学",
  "cat": "本地高校",
  "addr": "广东省深圳市南山区学苑大道1088号",
  "lat": 22.595xxx,
  "lng": 113.974xxx,
  "conf": "高",
  "status": "办学中",
  "desc": "2011年创办的新型研究型大学",
  "src": "官网"
}
```

`id`/`name`/`cat`/`addr`/`lat`/`lng`/`conf` 必填；`desc`/`status`/`src` 可选。`META.asof`（采集日期）、`META.rankedBy`（排序口径）、`META.catDef`（收录边界）渲染在页眉。

## 坐标系铁律（不可协商）

底图用高德瓦片 → **所有上图坐标必须是 GCJ-02（火星坐标）**：

| 来源 | 坐标系 | 处理 |
|---|---|---|
| 高德 / 腾讯地理编码 | GCJ-02 | 直接使用 |
| 百度 | BD-09 | 先转换 → GCJ-02 |
| Nominatim / OSM / 原始 GPS | WGS-84 | 先转换 → GCJ-02 |

混用坐标系会让每个点**偏移几百米**，而且能骗过朴素的数值校验——地图「看起来没问题」，实际上全站错位。这是 AI 生成中国地图的头号无声杀手，本 skill 把它定为铁律。

## 仓库结构

```
poi-precision-map/
├── SKILL.md                      # skill 本体：规则、流程、踩坑记录
├── README.md                     # English
├── README.zh-CN.md               # 你在这里
├── LICENSE                       # MIT
├── references/
│   ├── map_template.html         # 冻结的 HTML 模板（Leaflet + 高德瓦片）
│   ├── prompt_template.md        # 填空式启动提示词
│   └── validate.py               # 生成后校验脚本
└── examples/
    └── shenzhen-universities.html  # 示例：深圳高校分布图
```

## 局限与说明

- 高德瓦片为公开栅格服务、Leaflet 从 unpkg CDN 加载 —— 地图需要联网出图，但不需要任何密钥或账号
- 核实质量受检索能力约束；skill 用强制交叉验证 + 可见的置信度标签来弥补，而不是假装确定
- 不适用于「区级聚合气泡图」—— 它刻意只做逐点精确这件事

## 许可证

[MIT](LICENSE) © 2026 delicious-hml
