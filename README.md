# 电商订单管理系统

> 四川大学《数据库系统原理》课程设计（2026）· 给定方案一  
> 仓库：<https://github.com/Danielliu1219/scu-db-ecommerce-order-system>（Private）

面向中小电商场景，围绕 **商品 → 购物车 → 订单 → 支付 → 库存 → 统计** 主链路构建的 B/S 订单管理系统。项目重点不是营销功能，而是订单与库存的一致性、订单状态机、支付幂等、重复提交防护和多表统计查询。

## 当前进度

| 阶段 | 内容 | 状态 |
|---|---|---|
| M1 | 立项材料：项目名称、项目描述、功能清单、Word/Excel、项目日志、GitHub 仓库 | ✅ 已完成（组号待确认） |
| M2 | 数据库详细设计：ER 图、字段类型、DDL、初始化数据 | ⬜ 待开始 |
| M3 | 后端基础框架、认证、商品/分类/购物车 | ⬜ 待开始 |
| M4 | 订单—支付—库存事务闭环、管理端订单 | ⬜ 待开始 |
| M5 | 库存预警、用户管理、销售统计与前端联调 | ⬜ 待开始 |
| M6 | 测试、课程报告、PPT、答辩演示 | ⬜ 待开始 |

## 交付物

| 文件 | 说明 |
|---|---|
| [`deliverables/第X组_电商订单管理系统.docx`](deliverables/第X组_电商订单管理系统.docx) | **本次任务的 Word 立项材料**：项目名称、项目描述、功能清单（含 Excel 截图）、核心表规划、SQL 任务规划 |
| [`deliverables/软件功能清单.xlsx`](deliverables/软件功能清单.xlsx) | 可编辑功能清单，含“功能清单”“打印1”“打印2”“核心数据表”“SQL任务”工作表 |
| [`assets/功能清单-1.png`](assets/功能清单-1.png) | Word 中嵌入的功能清单截图（1/2） |
| [`assets/功能清单-2.png`](assets/功能清单-2.png) | Word 中嵌入的功能清单截图（2/2） |
| [`docs/01-requirements.md`](docs/01-requirements.md) | 需求与 9 项功能的完整文字版（由脚本生成） |
| [`docs/02-database-design.md`](docs/02-database-design.md) | 11 张表的初步设计、约束、索引、状态枚举、事务规则 |
| [`PROJECT_LOG.md`](PROJECT_LOG.md) | 项目日志：决策、时间线、当前状态、下一步、复现方式 |
| [`AGENTS.md`](AGENTS.md) | 给后续 Agent / 组员的交接说明 |

> **组号说明**：课程要求文件名为 `第x组_电商订单管理系统.docx`。目前未提供实际组号，因此文件名、封面和页脚使用 `第 X 组` 占位。确认组号后运行 `python scripts/build_deliverables.py --group 7`（把 7 换成实际组号）即可重新生成；成员姓名/学号需要在 Word 封面手工补填，或修改 `scripts/build_word.py` 中的封面信息。

## 功能一览

| 编号 | 功能 | 角色 | 一句话描述 |
|---|---|---|---|
| FR-01 | 用户注册与登录 | 游客 / 用户 / 管理员 | 注册、登录、退出、账号状态控制，按角色进入前台或后台 |
| FR-02 | 商品浏览与检索 | 游客 / 用户 | 按名称、分类、价格区间组合检索，查看详情与可售库存 |
| FR-03 | 购物车管理 | 用户 | 加购、改数量、删除、勾选结算，实时计算小计与合计 |
| FR-04 | 订单提交与库存扣减 | 用户 | 多商品下单，保存价格快照，事务内校验并扣减库存 |
| FR-05 | 订单支付与状态管理 | 用户 / 管理员 | 模拟支付、取消、发货、收货，按状态机约束流转 |
| FR-06 | 商品与分类管理 | 管理员 | 分类与商品的新增、编辑、上下架、软删除及多条件查询 |
| FR-07 | 库存与预警管理 | 管理员 | 入库、出库、盘点调整、预警阈值与库存流水查询 |
| FR-08 | 订单查询与销售统计 | 用户 / 管理员 | 订单多维查询，以及月度销售、Top10、分类占比等统计 |
| FR-09 | 用户与地址管理 | 用户 / 管理员 | 个人资料、密码、收货地址维护，以及后台用户状态管理 |

## 数据库规划

共 11 张表：`users`、`address`、`category`、`product`、`inventory`、`inventory_log`、`cart`、`cart_item`、`orders`、`order_item`、`payment`。

关键设计：

- `cart_item(cart_id, product_id)` 唯一，重复加购合并数量。
- `payment.order_id` 唯一，数据库层兜底支付幂等。
- `orders.idempotency_key` 唯一，防止重复提交。
- `inventory.stock >= 0` 的 CHECK 约束 + 行锁，防止超卖。
- `order_item` 保存商品名称、下单单价、数量、小计快照，历史订单不受调价影响。
- 订单状态机：`UNPAID → PAID → SHIPPED → COMPLETED`，以及 `UNPAID → CANCELLED`。

## 技术路线（建议，详细设计时确认）

| 层次 | 技术 |
|---|---|
| 前端 | Vue 3 + Vite + Element Plus + ECharts |
| 后端 | Python 3.12 + FastAPI + SQLAlchemy 2.0 + Pydantic v2 |
| 数据库 | MySQL 8.0（InnoDB / utf8mb4） |
| 认证 | JWT + bcrypt |
| 测试 | pytest + httpx + Postman/Apifox |
| 部署 | 本地运行；可选 Docker Compose |

不引入 Redis、消息队列、微服务、真实支付和真实物流，保持单机可演示。

## 目录结构

```text
.
├── deliverables/                 # Word / Excel 交付物
├── assets/                       # 功能清单截图（Word 中嵌入）
│   └── preview/                  # 本地 PDF/PNG 预览（不提交）
├── docs/                         # 课程要求、需求、数据库设计
├── references/                   # 课程原始文件（大作业说明、封面模板、功能清单模板）
├── scripts/                      # 统一数据源与生成脚本
│   ├── data.py                   # ★ 单一数据源：项目、功能、表、SQL、规则
│   ├── build_excel.py            # 生成 Excel
│   ├── export_images.py          # Excel → PDF → PNG（需要 Office）
│   ├── build_word.py             # 生成 Word
│   ├── build_docs.py             # 生成 Markdown 文档
│   ├── export_word_preview.py    # Word → PDF/PNG 预览（需要 Office）
│   └── build_deliverables.py     # 一键构建
├── PROJECT_LOG.md                # 项目日志
├── AGENTS.md                     # Agent 交接说明
└── README.md
```

## 重新生成

环境：Python 3.11+、Microsoft Office（仅导出 Excel 截图和 Word 预览时需要）。

```bash
# 完整构建（Excel → 截图 → Word → Markdown → PDF 预览）
python scripts/build_deliverables.py

# 组号确定后
python scripts/build_deliverables.py --group 7

# 没有 Office 时：复用已提交的截图，只重建 Word/Markdown
python scripts/build_deliverables.py --skip-images --no-preview
```

依赖：

```bash
pip install python-docx openpyxl pymupdf pillow pywin32
```

## 文档

- [课程要求整理](docs/00-course-requirements.md)
- [需求与功能清单](docs/01-requirements.md)
- [数据库设计初稿](docs/02-database-design.md)
- [项目日志](PROJECT_LOG.md)
- [Agent 交接说明](AGENTS.md)

## 说明

- 本项目仅用于四川大学《数据库系统原理》课程设计。
- 组号、成员姓名、学号目前为占位信息，提交前请补全。
- 课程原始文件保留在 `references/`，不要随意修改。
- 所有交付物由 `scripts/data.py` 生成，修改内容后请重新运行构建脚本，不要直接手改 docx/xlsx。
