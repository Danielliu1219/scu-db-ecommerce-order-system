# 项目日志 / PROJECT LOG

> **项目**：电商订单管理系统（课程给定方案一）  
> **课程**：四川大学《数据库系统原理》课程设计（2026）  
> **仓库**：<https://github.com/Danielliu1219/scu-db-ecommerce-order-system>（Private）  
> **最后更新**：2026-11-08  
> **当前阶段**：M1 立项材料已完成；组号、成员信息待补  
> **课程截止**：2026-11-12 23:59（立项材料提交）

---

## 0. 给接手的 Agent / 组员：先读这里

1. 先读本文件、[`AGENTS.md`](AGENTS.md)、[`docs/00-course-requirements.md`](docs/00-course-requirements.md)。
2. 当前仓库**只有立项材料和生成脚本**，业务代码尚未开始，不要假设已有后端/前端。
3. **单一数据源**是 `scripts/data.py`。Word、Excel、Markdown 都由它生成；不要直接手改生成物。
4. **组号是占位 `X`**。确认后运行 `python scripts/build_deliverables.py --group 7`，再补封面成员信息。
5. 生成 Word 前需要 `assets/功能清单-1.png`、`assets/功能清单-2.png`；没有 Office 时用 `--skip-images --no-preview` 复用已有图片。
6. 本次任务只要求 Word 立项材料；真实支付、物流、优惠券等明确不做，避免范围膨胀。

---

## 1. 项目概览

- **项目名称**：电商订单管理系统
- **英文名称**：E-Commerce Order Management System
- **项目代号**：SCU-DB-2026-EC-01
- **选题**：给定方案一
- **定位**：面向中小电商场景，围绕“商品—购物车—订单—支付—库存”主链路构建的 B/S 订单管理系统。
- **核心目标**：把订单、库存、支付和统计之间的数据一致性做扎实，覆盖课程要求的多表查询、增删改、事务、约束、异常处理和统计查询。
- **角色**：游客、普通用户、管理员。
- **功能**：9 个核心功能（FR-01 ~ FR-09）。
- **数据表**：11 张（`users`、`address`、`category`、`product`、`inventory`、`inventory_log`、`cart`、`cart_item`、`orders`、`order_item`、`payment`）。
- **技术路线（建议）**：Vue 3 + Element Plus / FastAPI + SQLAlchemy 2.0 / MySQL 8.0 / JWT。
- **范围边界**：不实现真实支付、真实物流、优惠券、秒杀、评价、推荐、微服务、移动端 App。

---

## 2. 已确认决策（Decision Log）

| ID | 日期 | 决策 | 理由 | 影响 |
|---|---|---|---|---|
| D-001 | 2026-11-08 | 选择给定方案一：电商订单管理系统 | 主链路清晰，订单/库存事务与多表统计最适合数据库课程评分点 | 项目名称、功能、表结构均围绕电商交易 |
| D-002 | 2026-11-08 | 设置游客、普通用户、管理员三类角色 | 覆盖“两个及以上角色 + 权限差异”要求，同时不过度增加角色复杂度 | 前台/后台菜单与接口双重鉴权 |
| D-003 | 2026-11-08 | 规划 9 个核心功能 | 落在课程 5—10 个功能区间，覆盖账号、商品、购物车、订单、支付、库存、统计、地址 | 功能清单 FR-01 ~ FR-09 |
| D-004 | 2026-11-08 | 在建议表基础上增加 `address`、`inventory_log` | 收货地址是下单必需；库存流水是库存审计与异常追踪的关键 | 总表数 11 张 |
| D-005 | 2026-11-08 | 技术栈建议 FastAPI + Vue 3 + MySQL 8.0 | Python 对 AI 系学生更友好；Vue 便于做出美观界面；MySQL 贴合课程 | 后续可在详细设计中调整，不影响数据库设计 |
| D-006 | 2026-11-08 | 支付只做模拟支付记录 | 真实支付接入涉及第三方、证书、回调，偏离数据库课程重点 | 支付表保留，状态机与幂等仍是重点 |
| D-007 | 2026-11-08 | 所有交付物由 `scripts/data.py` 生成 | 避免 Word、Excel、文档字段口径不一致，方便 Agent 接手 | 修改内容后必须重新运行构建脚本 |
| D-008 | 2026-11-08 | Excel 功能清单拆成“功能清单 / 打印1 / 打印2” | 完整表用于编辑筛选；两张打印页用于导出高清 Word 截图 | Word 中功能清单为 2 页横向图片 |
| D-009 | 2026-11-08 | 组号使用 `X` 占位 | 用户未提供实际组号；避免猜测错误 | 文件名、封面、页脚、Markdown 均为第 X 组；确认后一键替换 |

---

## 3. 时间线（Chronological Log）

### 2026-11-08

- **16:29** 读取课程文件夹中的 3 个原始文件：
  - `2026学年四川大学数据库课程设计大作业.docx`
  - `报告封面文档.doc`
  - `软件功能清单.xls`
- **16:30** 提取并梳理课程要求、评分标准、提交要求、方案一要求、SQL 任务示例。
- **16:34** 建立项目结构：`references/`、`docs/`、`deliverables/`、`assets/`、`scripts/`；原始课程文件移入 `references/`。
- **16:35** 建立单一数据源 `scripts/data.py`，定义项目、角色、9 个功能、11 张表、业务规则、课程对应关系、SQL 任务、技术栈、范围、计划。
- **16:35** 生成 `deliverables/软件功能清单.xlsx`（完整清单 + 两张打印页 + 核心数据表 + SQL 任务 + 说明）。
- **16:36** 用 Excel COM 导出“打印1 / 打印2”为 PDF，再以 300 DPI 渲染、裁剪为 `assets/功能清单-1.png`、`功能清单-2.png`。
- **16:38** 生成第一版 Word；检查发现封面溢出、分节首页页眉页脚被抑制、页码在分节处重置、表格跨页不美观。
- **16:42** 修正：压缩封面间距；对正文/横向/纵向分节设置 `different_first_page_header_footer = False`；移除分节继承的起始页码；调整表格字号、行距、列宽与分页。
- **16:43** 生成 `docs/00-course-requirements.md`（课程要求整理）。
- **16:44** 生成 `docs/01-requirements.md`、`docs/02-database-design.md`（由 `scripts/build_docs.py` 从 `data.py` 生成）。
- **16:45** 一键构建脚本 `scripts/build_deliverables.py` 跑通：Excel → 截图 → Word → Markdown → PDF 预览。
- **16:46** Word 最终版：11 页（封面 1 + 正文 10，含 2 页横向功能清单）；Word COM 可正常打开并导出 PDF，无修复提示。
- **16:47** 补充 `README.md`、`AGENTS.md`、`.gitignore`、`.gitattributes`；准备 GitHub 仓库。
- **16:50** 初始化 Git、提交初始版本、创建 Private GitHub 仓库并推送（见仓库地址）。
  - 远端仓库：<https://github.com/Danielliu1219/scu-db-ecommerce-order-system>
  - 初始提交：见仓库 `main` 分支最新提交（本地与远端一致）
  - 备注：本机 `git` HTTPS 访问 `github.com` 被重置，推送改用 GitHub Git Data API 完成；本地 `main` 与 `origin/main` 已对齐到同一提交。

> 说明：以上时间为本地构建时间，后续变更请在本节追加，不要覆盖历史记录。

---

## 4. 交付物与文件地图

| 路径 | 类型 | 说明 | 是否提交 |
|---|---|---|---|
| `deliverables/第X组_电商订单管理系统.docx` | Word | 本次任务的立项材料，11 页 | ✅ |
| `deliverables/软件功能清单.xlsx` | Excel | 可编辑功能清单、打印页、表规划、SQL 任务 | ✅ |
| `assets/功能清单-1.png` | PNG | Word 中功能清单截图 1/2（300 DPI） | ✅ |
| `assets/功能清单-2.png` | PNG | Word 中功能清单截图 2/2（300 DPI） | ✅ |
| `docs/00-course-requirements.md` | Markdown | 课程要求与选题依据 | ✅ |
| `docs/01-requirements.md` | Markdown | 需求与 9 项功能完整文字版（生成） | ✅ |
| `docs/02-database-design.md` | Markdown | 11 张表初稿、约束、索引、事务规则（生成） | ✅ |
| `references/` | 原始文件 | 课程大作业说明、封面模板、功能清单模板 | ✅ |
| `scripts/data.py` | Python | **单一数据源** | ✅ |
| `scripts/build_excel.py` | Python | 生成 Excel | ✅ |
| `scripts/export_images.py` | Python | Excel → PDF → PNG（Office COM） | ✅ |
| `scripts/build_word.py` | Python | 生成 Word | ✅ |
| `scripts/build_docs.py` | Python | 生成 Markdown 文档 | ✅ |
| `scripts/export_word_preview.py` | Python | Word → PDF/PNG 预览（Office COM） | ✅ |
| `scripts/build_deliverables.py` | Python | 一键构建 | ✅ |
| `assets/preview/` | 本地预览 | PDF/PNG，用于本地检查排版 | ❌（gitignore） |

---

## 5. 当前状态

- [x] 阅读课程要求、评分标准、提交要求、方案一说明。
- [x] 确定选题、项目名称、项目描述、角色、功能范围、数据表规划。
- [x] 完成 9 个功能的功能名称 + 功能描述 + 约束 + 输入/处理/输出 + 数据表。
- [x] 完成 Excel 功能清单，并导出 2 张高清截图。
- [x] 完成 Word 立项材料（项目名称、项目描述、功能清单、课程对应、表规划、SQL 任务、计划）。
- [x] 完成项目日志、README、AGENTS、课程要求整理、需求文档、数据库设计初稿。
- [x] 建立 Git 仓库并推送到 GitHub Private 仓库。
- [ ] **确认实际组号**（当前 `X` 占位）。
- [ ] **补全封面小组成员姓名/学号**。
- [ ] 用户自行提交到课程指定链接（本次任务不代为提交）。
- [ ] M2：ER 图、字段类型、DDL、初始化数据。
- [ ] M3—M5：后端、前端、统计、联调。
- [ ] M6：测试、课程报告、PPT。

---

## 6. 下一步（按优先级）

1. **确认组号**（P0）
   - 运行 `python scripts/build_deliverables.py --group <实际组号>`。
   - 检查新生成的 `第<组号>组_电商订单管理系统.docx`。
2. **补全封面成员信息**（P0）
   - 在 Word 封面“小组成员”处填写姓名（学号），或修改 `scripts/build_word.py` 的 `build_cover()` 后重新生成。
3. **M2 数据库详细设计**（P1）
   - 完成 ER 图（Chen 或 Crow's Foot）。
   - 完成 11 张表的字段类型、长度、默认值、外键删除策略。
   - 编写 `schema.sql` 与 `seed.sql`，准备样例数据。
4. **M3 后端基础框架**（P1）
   - FastAPI 项目结构、配置、数据库连接、JWT 认证、统一异常处理。
   - 用户注册/登录、商品分类、商品检索、购物车接口。
5. **M4 订单主链路**（P1）
   - 下单事务、库存行锁、库存流水、支付幂等、取消回补、状态机。
   - 重点写异常测试：库存不足、重复支付、非法状态、重复提交、越权。
6. **M5 管理端与统计**（P2）
   - 商品/分类/库存/订单/用户管理；ECharts 统计页。
7. **M6 报告与答辩**（P2）
   - 按课程模板补摘要、目录、ER 图、表结构、数据样例、测试截图、分工占比。

---

## 7. 已知风险 / 待确认

| 风险 | 影响 | 处理 |
|---|---|---|
| 组号未提供 | 文件名、封面、页脚为 `第 X 组` | 确认后运行 `--group` 一键替换 |
| 成员姓名/学号未提供 | 封面留空 | 提交前手工补填，或改脚本后重新生成 |
| 技术栈为建议方案 | 后续实现时可能调整 | 在 M2 详细设计中由组内确认；不影响数据库设计 |
| Excel 截图依赖 Microsoft Office | 无 Office 的机器无法重新导出 PNG | 已提交两张 PNG；可用 `--skip-images` 复用 |
| Word 字体依赖宋体/黑体/微软雅黑 | 其他系统打开可能轻微错位 | 提交 PDF 预览或在 Windows + Office 环境最终检查 |
| 课程截止 11-12 23:59 | 逾期无法提交 | 优先完成组号/成员信息，再提交 Word |

---

## 8. 复现与验证

### 8.1 环境

- Windows 10/11
- Python 3.11+（本机 3.13.5）
- Microsoft Office（Excel + Word，用于截图和预览）
- 依赖：`python-docx openpyxl pymupdf pillow pywin32`

### 8.2 一键构建

```bash
python scripts/build_deliverables.py
```

输出：

- `deliverables/软件功能清单.xlsx`
- `assets/功能清单-1.png`、`assets/功能清单-2.png`
- `deliverables/第X组_电商订单管理系统.docx`
- `docs/01-requirements.md`、`docs/02-database-design.md`
- `assets/preview/word-preview.pdf` + `page-*.png`（本地检查用）

### 8.3 组号确定后

```bash
python scripts/build_deliverables.py --group 7
```

### 8.4 没有 Office 时

```bash
python scripts/build_deliverables.py --skip-images --no-preview
```

### 8.5 GitHub 仓库状态

- 仓库：<https://github.com/Danielliu1219/scu-db-ecommerce-order-system>（Private）
- 默认分支：`main`
- 最新提交：见仓库 `main` 分支（本地与远端一致）
- 树对象：可通过 `git rev-parse HEAD^{tree}` 查看
- 本地 `main` 与 `origin/main` 指向同一提交；`git status` 干净。
- 由于当前网络无法通过 git HTTPS 访问 `github.com`，首次推送使用 GitHub Git Data API 完成；在可访问 GitHub 的网络下，后续可直接 `git fetch` / `git push`。

### 8.6 本次验证记录

- `python scripts/build_deliverables.py` 成功。
- Excel 工作簿可打开，5 个工作表：`功能清单`、`打印1`、`打印2`、`核心数据表`、`SQL任务`。
- Word 用 Microsoft Word 打开无修复提示，`ComputeStatistics(2)` 返回 11 页。
- PDF 预览 11 页；页脚页码连续（正文 1—10）。
- 功能清单截图 300 DPI，分别约 804 KB / 990 KB。
- Word 中功能清单为 2 页横向页面，表格文字可读，表头在跨页时重复。

---

## 9. 日志追加模板

后续每次修改请追加：

```markdown
### YYYY-MM-DD

- **HH:MM** 做了什么（文件/命令）。
- **HH:MM** 发现什么问题，如何修复。
- **HH:MM** 验证结果（页面数、接口、测试）。
- **决策**：如有新决策，补充到第 2 节 Decision Log。
- **下一步**：更新第 6 节。
```

---

## 10. 参考

- 课程原始文件：`references/2026学年四川大学数据库课程设计大作业.docx`
- 课程要求整理：`docs/00-course-requirements.md`
- 需求与功能清单：`docs/01-requirements.md`
- 数据库设计初稿：`docs/02-database-design.md`
- Agent 交接说明：`AGENTS.md`
