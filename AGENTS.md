# AGENTS.md

本文件面向后续接手本仓库的 Agent / 组员。先读 `PROJECT_LOG.md`，再读本文件。

## 1. 项目上下文

- 课程：四川大学《数据库系统原理》课程设计（2026）
- 选题：给定方案一，电商订单管理系统
- 当前阶段：M1 立项材料已完成；M2—M6 尚未开始
- 课程截止：2026-11-12 23:59（立项材料）
- 角色：游客、普通用户、管理员
- 功能：9 个（FR-01 ~ FR-09）
- 数据表：11 张（`users`、`address`、`category`、`product`、`inventory`、`inventory_log`、`cart`、`cart_item`、`orders`、`order_item`、`payment`）
- 技术路线（建议）：Vue 3 + Element Plus / FastAPI + SQLAlchemy 2.0 / MySQL 8.0 / JWT

## 2. 事实源（Source of Truth）

优先级从高到低：

1. `scripts/data.py`：项目、角色、功能、表、规则、SQL 任务、技术栈、计划。
2. `docs/00-course-requirements.md`：课程要求整理。
3. `PROJECT_LOG.md`：决策、时间线、当前状态。
4. `README.md`：对外说明。
5. `docs/01-requirements.md`、`docs/02-database-design.md`：由脚本生成，不要手改。

> 如果文档与 `scripts/data.py` 不一致，以 `scripts/data.py` 为准，并重新生成文档。

## 3. 生成物与脚本

| 脚本 | 作用 | 依赖 |
|---|---|---|
| `scripts/build_excel.py` | 生成 `deliverables/软件功能清单.xlsx` | openpyxl |
| `scripts/export_images.py` | Excel → PDF → PNG（`assets/功能清单-*.png`） | Excel COM、pymupdf、Pillow |
| `scripts/build_word.py` | 生成 `deliverables/第X组_电商订单管理系统.docx` | python-docx、Pillow |
| `scripts/build_docs.py` | 生成 `docs/01-requirements.md`、`docs/02-database-design.md` | 无 |
| `scripts/export_word_preview.py` | Word → PDF/PNG 预览 | Word COM、pymupdf |
| `scripts/build_deliverables.py` | 一键构建全部 | 以上 |

常用命令：

```bash
# 完整构建
python scripts/build_deliverables.py

# 组号确定后
python scripts/build_deliverables.py --group 7

# 没有 Office：复用已提交的截图
python scripts/build_deliverables.py --skip-images --no-preview
```

## 4. 必须遵守的约定

- **不要手改** `deliverables/*.docx`、`deliverables/*.xlsx`、`docs/01-requirements.md`、`docs/02-database-design.md`；改 `scripts/data.py` 后重新生成。
- 所有中文文档使用 UTF-8；Markdown 表格中的 `|` 要转义。
- 组号目前是 `X` 占位。不要猜测实际组号；等用户确认后使用 `--group`。
- 封面成员姓名/学号目前是占位下划线；提交前必须补全。
- 不引入真实支付、真实物流、优惠券、秒杀、评价、推荐、微服务、移动端 App。
- 不提交 `.env`、密钥、数据库密码、Office 临时文件 `~$*`。
- 数据库设计优先保证：主键、外键、唯一约束、CHECK、事务、行锁、索引；不要为了“功能多”牺牲一致性。
- 所有涉及库存、订单状态、支付的修改，必须同时考虑异常路径和回滚。

## 5. 目录说明

```text
deliverables/        Word / Excel 交付物
assets/              功能清单截图（Word 中嵌入）
assets/preview/      本地 PDF/PNG 预览（gitignore）
docs/                课程要求、需求、数据库设计
references/          课程原始文件，不要修改
scripts/             数据源与生成脚本
PROJECT_LOG.md       项目日志（每次变更追加）
README.md            对外说明
AGENTS.md            本文件
```

## 6. 当前已知问题 / 待办

1. **组号未确认**：文件名为 `第X组_电商订单管理系统.docx`，封面/页脚为 `第 X 组`。
2. **成员信息未填**：封面“小组成员”为下划线占位。
3. **M2 未开始**：ER 图、字段类型、DDL、初始化数据尚未完成。
4. **技术栈未最终确认**：FastAPI + Vue 3 是建议方案，可在 M2 调整。
5. **Word 预览依赖 Office**：无 Office 时用 `--skip-images --no-preview`，或直接打开已提交的 docx。

## 7. 验收清单（M1）

- [ ] `deliverables/第X组_电商订单管理系统.docx` 可打开，无修复提示。
- [ ] 封面有项目名称、方案类型、组号、成员、指导教师、日期。
- [ ] 正文含项目名称、项目描述、功能清单、课程要求对应。
- [ ] 功能清单截图清晰，包含 9 个功能，字段完整。
- [ ] Excel 可编辑，含“功能清单 / 打印1 / 打印2 / 核心数据表 / SQL任务”。
- [ ] 文档中的表名、字段名、状态值与 `scripts/data.py` 一致。
- [ ] `PROJECT_LOG.md` 已记录本次变更。
- [ ] 提交前补全组号、成员姓名/学号。

## 8. 建议的下一步

1. 等用户确认组号/成员信息，重新生成 Word。
2. 开始 M2：ER 图、关系模式、字段类型、DDL、样例数据。
3. 用 MySQL 8.0 实际跑通 DDL 与 4 条课程 SQL。
4. 再进入后端/前端实现，避免先写代码后改表。
