# 项目日志 / PROJECT LOG

> **当前有效记录为2026年11月9日重做记录，见本文件末尾。** 用户指定以教师原件为依据，并要求难度适合本科大三。本次交付为3页Word和1张工作表的Excel，设置普通用户、管理员两个角色及9项功能，规划9类基础数据。组号和成员信息由用户自行补全。下方2026年11月8日的旧方案、文件地图及构建命令保留为历史，后续操作请使用当前`README.md`和`AGENTS.md`。

> **项目**：电商订单管理系统（课程给定方案一）  
> **课程**：四川大学《数据库系统原理》课程设计（2026）  
> **仓库**：<https://github.com/Danielliu1219/scu-db-ecommerce-order-system>（Private）  
> **最后更新**：2026-11-09
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

---

## 2026年11月9日 按教师原件重做立项材料

### 用户确认

- 选题为方案一“电商订单管理系统”。
- 用户为四川大学计算机学院本科大三学生，要求需求规模适中。
- 本次只完成项目名称、项目描述及功能清单，文件由用户自行提交。
- 组号、成员姓名及学号已经确定，用户选择自行补全，文档留空。
- 用户中途要求暂停，已立即停止操作，收到“继续”后完成最后整理。

### 内容与范围

- 重新查阅教师的大作业说明、功能清单模板及报告封面模板。区分本次立项材料与后续完整课程报告。
- 采用普通用户和管理员两个角色，编写FR-01至FR-09共9项功能。功能编号已重新编排，以当前`data.py`为准。
- 基础数据围绕教师建议的9类实体组织，收货信息直接保存在订单中，分类使用单层结构。
- 保留下单与扣库存一起成功或撤销、取消订单恢复库存、订单单价快照、模拟支付去重、角色权限等必要规则。
- 将订单查询与明细、月度销售与已支付订单量、销量前10、近30天未下单用户等教师SQL示例落实到功能清单。
- 明确统计口径，销售额与订单量按订单汇总，销量按明细汇总，支付时间决定销售所属月份。

### 文件调整

- 重写`scripts/data.py`，统一生成Word、Excel、功能截图与需求文字版。
- Word改为3页，首页项目名称和描述，后两页横向插入Excel截图。首页留组号及成员填写空白，文件名使用`X`占位。
- Excel为1个“功能清单”工作表，沿用教师模板七列，包含9条完整需求。
- 使用`build_excel.mjs`生成Excel，`export_office.ps1`通过原生Office只读打开及导出，`build_deliverables.py`编排与核验。
- 删除已被替代的旧Excel及导图脚本、旧数据库详细设计初稿。重写README、AGENTS和课程要求整理，更新Python依赖。

### 验证记录

- 逐格核对Excel的七列表头及9条需求，与`data.py`一致。工作簿ZIP结构正常，原生Excel打开和PDF导出成功。
- 原生Word打开和PDF导出成功，分页为3页。两张240DPI清单截图与当前Excel一致。
- 已逐页查看PNG预览，修正默认标题装饰线和重复页码，确认页码为1、2、3，正文及截图无裁切。
- 本机缺少LibreOffice，打包文档渲染脚本报找不到`soffice.exe`，最终使用原生Word导出并由Poppler渲染检查。
- 工作区Excel渲染库曾在保存后以Windows异常退出状态结束。构建流程仅在本轮输出重新生成、ZIP校验、全部需求单元格核验、预览存在均通过时继续，随后进行原生Office打开及导出检查。
- 最后复核3份教师原件的SHA-256，与本次任务开始时一致。Word内嵌图片与当前两张功能截图的SHA-256逐一对应，Excel七列表头及9条完整需求逐格一致。
- 交付目录仅保留Word和Excel两份最终文件，工具产生的检查明细移入内部预览目录。

### 交付与待用户补全

- `deliverables/第X组_电商订单管理系统.docx`
- `deliverables/软件功能清单.xlsx`
- 组号、姓名、学号由用户填写，并将文件名中的`X`替换为实际组号。
- 本次操作均在本地完成，提交由用户自行处理。

---

## 2026年11月13日 完成课程报告截至概要设计审核稿

### 用户指示与参考

- 用户要求依据教师大作业文档完成课程报告截至概要设计的内容，暂不进行业务代码工作，完成后交由用户审核。
- 需求分析与概要设计补充用例图、泳道图和传统ER图，全部使用黑白配色；限制、假设和待确认说明单独置于`Limitation.md`。
- 用户清空`deliverables/`，将已填写组号及成员信息的立项Word和可编辑功能清单Excel放入`references/`作为本轮参考。核对后采用第20组及三名成员姓名、学号；负责人、专业、成员角色和报告日期留空。
- 11月11日已完成主要编写、渲染及逐页修正；用户要求暂停后立即停止。11月13日收到“继续”后完成最终核验和记录整理。

### 内容与文件

- 新建`deliverables/第20组_电商订单管理系统_课程报告.docx`，包括封面、约150字中文摘要、目录、绪论和概要设计。绪论包含背景、开发环境与技术路线；概要设计包含按角色分析的需求、完整九项功能、关键用例、泳道、业务及非功能规则、模块图、概念数据模型、状态与事务及查询统计口径。
- 需求仍为普通用户和管理员两个角色、FR-01至FR-09九项功能，复用当前`data.py`的完整需求字段，未改变此前需求源或立项构建脚本。
- 概念模型沿用用户、分类、商品、购物车、购物车明细、订单、订单明细、库存、支付记录九类数据；下单扣库存、取消回补、支付去重及支付时间统计口径保持一致。
- 本轮明确空购物车初始化、用户与结算标识唯一、每商品一份库存、每订单最多一条成功支付、旧库存页面冲突后刷新确认等概念约束。商品删除先检查业务引用及零库存；这些说明记录在报告与独立审核说明中。
- 教师目录将ER图安排在3.2.1；根据用户本轮要求，概念ER总图及属性分图先放在概要设计2.3，不添加详细设计或实现测试的空章节。
- 完整报告文字保存为`docs/02-course-report.md`；12幅图同时保存PNG及SVG于`assets/report/`；内部生成脚本、PDF和逐页PNG仅保存在`assets/preview/course-report/`。
- 新建`Limitation.md`，集中记录制作范围、环境选择、概念假设及后续待核实事项，正文不放置制作免责声明或虚构测试结果。

### 验证与状态

- 原生Word可打开、更新目录及导出PDF，最终共25页，含12幅图和6张表。封面无页码，摘要和目录为I、II，正文为1至22。
- 逐页查看预览；修复段落溢页、子标题默认斜体、模块分支连接、泳道失败路径重叠及ER属性连线和注释间距。最后一轮未变页面逐像素一致，变化页面重新检查。
- 核对12幅图的RGB通道一致，全部为黑白及抗锯齿灰阶；ER使用矩形实体、菱形联系、椭圆属性及带下划线的标识，不以活动图或泳道代替。
- 核对全部九项需求、A4纸型、图文嵌入和目录页码；报告正文无制作免责说明。
- 3份教师原件与2份用户新增参考文件的SHA-256均与本轮读取时一致。
- 仅保存本地审核材料，不进行课程平台提交、Git提交或推送。下一步由用户审核报告，再按用户意见修改。

### 同日按用户要求改为纯黑白

- 用户进一步明确“纯黑白配色”。将12幅PNG图源和Word内嵌图全部转为1位黑白，逐图确认像素只有0和255；SVG仍只使用黑、白绘制。
- 统一Word文字颜色、表格填充和边框，并将文档主题色限制为纯黑与纯白，关闭图片自动压缩。修改内部制图保存步骤，使后续输出仍为1位黑白。
- 保留正文、表格文字、图表尺寸与位置，直接修改现有报告包，未重新生成或覆盖用户身份栏内容。原生Word更新目录及导出后仍为25页。
- 复核12个含图页面；其余13页与此前已检查预览逐像素一致。12幅内嵌图仍为1位黑白，全部段落及表格文字不变，5份参考文件哈希不变。
- 当前交付文件仍为`deliverables/第20组_电商订单管理系统_课程报告.docx`。未提交或推送。

### 同日按顶层与详细层次重绘用例图

- 用户要求用例图区分顶层用例图和详细用例图。将原来的两张按角色概括的图替换为1张系统顶层图和4张详细图。
- 顶层图统一展示普通用户、管理员与FR-01至FR-09九项功能；详细图分别展开账户与身份、商品选购与购物车、订单与支付、后台维护与统计，共覆盖31项角色操作及1项金额计算的包含行为。
- 详细图明确注册、登录、本人资料与密码、商品组合检索、购物车各项操作、本人订单处理、管理员订单查询与发货、支付结果与记录查询、商品分类及库存维护和三类统计查询。包含关系采用从基础用例指向被包含行为的虚线开放箭头；登录作为受限操作的前置条件。
- 同步更新`docs/02-course-report.md`中的2.1.3、2.1.4节，以及Word对应段落、后续图号、图注和正文引用。其余功能需求、表格、业务规则及身份栏保留。
- 当前报告为28页、15幅图、6张表，正文页码1至25；原生Word已更新目录并导出预览，全部28页检查完成。所有内嵌图仍为1位纯黑白。
- 图源仍置于`assets/report/`，已被替代的旧两张按角色用例图源移入内部预览目录保存。教师原件与用户新增参考文件均未修改。
- 当前交付文件名不变，继续由用户审核。未提交、推送或开展业务代码工作。

---

## 2026年11月13日 按七项问题定向返工课程报告

### 任务范围与修改

- 依据用户列出的七项问题进行定向返工，先复核项目约定、教师原件、当前28页报告、需求源和独立限制说明。原报告及文件哈希基线保存在内部预览目录，未修改旧日志记录。
- `build_report.py`的TOC域改为`TOC \o "1-3" \h \z \u`。原生Word生成两页目录，2.1.1至2.1.9均进入目录；前置页码顺延为I、II、III，正文与参考文献为1至26。
- 图2-13将结算标识、支付时间、发货时间、完成时间和取消时间绘为正式椭圆属性，删除原图下小字；订单实体共12项属性。2.3.4明确订单编号兼作实体标识与对外订单号，未增加补充属性表，图表编号及数量保持不变。
- 图2-10的用户与购物车联系明确标为“普通用户拥有”，保持普通用户与购物车一对一，管理员不拥有购物车。同步2.2.2、2.3.1、表2-4及图2-12的角色范围说明。
- 将“取消未支付订单”“未支付订单仍展示”“取消或已支付订单不可再次支付”分别统一为“取消待支付订单”“待支付订单仍展示”“已取消或已支付订单不可再次支付”，同步`scripts/data.py`、`docs/01-requirements.md`及`docs/02-course-report.md`。
- 在2.4.2明确待支付订单不自动超时取消，只能由所属普通用户手动取消以释放库存，管理员不代取消；`Limitation.md`同步说明未手动取消时持续占用库存。
- `Limitation.md`补充最终报告3.2.1复用或迁移当前ER，3.1 UI、3.2.2表结构、3.2.3数据样例及第4至第6章留待后续完成。正文未加入制作说明或免责声明，也未新增3.x至6.x章节。
- 补充并核实MySQL 8.0参考手册、FastAPI和Vue 3官方文档，在1.2环境表及1.3技术路线中实际引用；参考文献独立成页。
- 只更新图2-10、图2-12、图2-13的PNG/SVG源文件，其他12幅图的哈希保持不变。制图脚本增加按图选择输出，报告脚本保留纯黑白主题与1位图片，使用段前分页避免末尾分页段落产生空白页。
- 按用户指定使用`assets/preview/course-report/build_report.py`重新生成DOCX，并以`export_report.ps1`在原生Word更新目录和导出PDF；未运行3页立项材料构建脚本，未安装依赖。

### 验证结果与交付状态

- 最终报告30页，含9项FR、15幅图、6张表；两页目录共有30条一级至三级记录，全部与原生Word的目标页码匹配。
- 已逐页查看全部30页预览。首轮发现订单属性页文字溢页及事务页后多出空白页，已通过局部图尺寸、说明文字和分页设置修复；最终无裁切、图注分离、孤行或页码错位。
- Markdown正文段落及全部6张表与DOCX逐项一致，九项FR的名称、描述、约束及输入处理输出与`data.py`一致，三份文字源中的指定旧术语均已清除。
- 15幅图源及Word内嵌图均为1位图像，像素集合仅含0和255；原有A4纸型、字体与页边距不变。
- 封面正文及封面预览逐像素与返工前一致，第20组、三名成员姓名学号及指导教师信息未变；课题负责人、成员角色、专业和提交日期继续留空。
- `references/`下3份教师原件和2份用户参考文件的SHA-256均与返工前基线一致。
- 更新README和AGENTS中的当前页数与目录说明。核验材料保存于`assets/preview/course-report/targeted-20261113/`，当前Word文件名不变，继续交由用户审核；未提交或推送。

---

## 2026年11月13日 完成编码前数据库详细设计文档

### 用户授权与读取范围

- 用户明确要求作为详细设计agent，仅产出设计文档，不编写业务代码，不改已有报告正文、封面身份及references，不提交或推送。
- 按约定先读11月9日和11月13日项目记录、AGENTS、当前报告Markdown、Limitation及data.py；使用工作区依赖只读提取教师大作业原件和当前30页课程报告DOCX，并核对三张ER属性分图中的正式属性。
- 工作区已有此前任务的未提交改动，本轮保留原状，仅新增`docs/03-database-design.md`，修改`Limitation.md`并在本日志末尾追加记录。

### 已确定设计

- 沿用报告的单字段可售库存`inventory.available`，盘点输入为可售量，按最新版本计算差额；待支付占用由订单明细派生展示，不当作实物总库存。下单扣减、用户取消回补，支付、发货和收货不再扣库存。
- 不增加30分钟惰性过期或管理员代取消，不设expires_at；待支付订单只能由所属普通用户手动取消，无操作则持续占用库存。
- 客户端生成16个安全随机字节并编码为32位小写十六进制checkout_token，数据库按用户与token唯一；服务端存规范化载荷SHA-256摘要，同token异参拒绝，失败回滚可用原token重试，取消后的token仍绑定原单。订单自增主键继续兼作对外订单号。
- 完成users、category、product、cart、cart_item、orders、order_item、inventory、payment九张表的字段字典、默认值、主外键、UNIQUE、CHECK、索引及RESTRICT删除策略，覆盖报告2.3全部属性；保留独立库存编号，并补库存version和结算摘要等技术字段。
- 给出MySQL 8.0.16及以上可执行DDL，统一InnoDB、utf8mb4、DECIMAL(10,2)、INT和DATETIME；连接采用READ COMMITTED、+08:00，应用使用Asia/Shanghai。明确订单/库存行锁、商品编号升序加锁、库存版本校验及死锁/锁超时整笔回滚，最多3次总尝试。
- 写出用户订单及明细、月度销售额与已支付订单量、支付期间销量前10、近30天未下单普通用户四条SQL，沿用报告2.5支付时间、订单粒度、明细数量及左闭右开窗口口径。
- 完成FR-01至FR-09的API方法、路径、角色、入参、出参和主要错误码，以及下单、取消、支付伪代码、状态时间一致性规则和种子数据建议。同token重放使用单条SELECT读取订单、明细与支付，避免READ COMMITTED下拼接不同时刻的结果。
- Limitation同步库存及长期占用、MySQL最低版本、跨表完整性的事务责任、数量金额上界、无库存流水审计、仅成功支付事实及2小时JWT不即时撤销等限制；本轮技术决策均已选定，没有需要用户先确认的未决分支。

### SQL校验与保护范围

- 使用机器现有MySQL Community Server 8.0.40二进制，在系统临时目录初始化独立数据目录，绑定127.0.0.1:33316进行设计校验；未启动或修改原有MySQL80服务，未向现有数据库写入。
- 文档DDL完整执行成功，四条查询在空库执行成功；另完成46项样例、约束和结构检查。两张80.00及一张200.00多商品订单按11月支付合计360.00、已支付订单量3，未因明细关联或相同金额去重而出错。
- 复核跨月支付、支付区间上下界、商品改名归并、销量并列取前10、待支付与取消订单展示，以及近30天取消订单、从未下单、精确边界和管理员排除规则。唯一键、CHECK、数值上界、外键及删除保护按预期拒绝非法SQL，事务失败后库存和版本回滚。
- 核对九表全部为InnoDB和utf8mb4，样例订单总额等于明细和，支付金额及时间与订单一致。这些是设计SQL的验证，不是已实现业务接口或并发应用的测试结论。
- 最终复核本轮修改范围为上述三个Markdown文件；现有课程报告DOCX、报告Markdown、data.py、封面及全部参考文件内容保持不变。关闭临时MySQL校验实例，本地保存设计文档，不进行Git提交、推送或课程平台提交。

---

## 2026年11月14日 完成业务编码与本地验收

- 按用户确认计划完成M0及FR-01至FR-09：同步FastAPI/SQLAlchemy、九表映射、JWT/Argon2id、三个核心事务、四条查询和Vue 3/Element Plus页面；DDL、接口、错误码与统计口径保持docs/03契约。
- 在独立33316端口运行MySQL 8.0.40开发实例，应用库与测试库隔离，未启动原MySQL80服务；预置账号口令仅保存在忽略的本地.env，演示五种订单状态经业务服务生成。
- 实际结果：pytest全套42项通过（1条测试客户端依赖弃用提示）；Vitest 10项通过；TypeScript检查和Vite生产构建通过（Element Plus主包体积提示）；Playwright 2条链路通过，含双角色交易、响应丢失刷新后原token重放、旧版本库存表单冲突。
- 修复初轮检查中的ORM金额类型显示差异；补齐CHECK异常分类断言和浏览器异步筛选等待。一次浏览器检查与构建重叠后串行重跑通过，未伪造运行结果。
- 复核报告、图源、参考文件、报告文字、内容源及设计契约共39份文件SHA-256不变。保留报告阶段原有未提交改动。
- 按用户要求将唯一实施清单保存为docs/04-implementation.md，精简README为现行入口和命令，并在AGENTS加入接手及定期整理规则；本轮失败初始化目录的递归清理被自动审批策略阻止，保留在忽略的预览区。
- 用户后续允许GitHub代码托管，应用、测试及必要契约/运行文档使用codex/ecommerce-implementation分支；现有OAuth凭据缺workflow权限，首次推送被GitHub拒绝；改为.github/ci-template.yml未启用模板后继续托管，不宣称远端自动检查通过。
- 实际已将应用实现提交ead959d推送到origin/codex/ecommerce-implementation，远端分支SHA逐一核对一致；最终本地页面HTTP 200、未登录接口401，39份受保护文件哈希再次一致。

---

## 2026年11月14日 软件工程化与数据库质量基线审查（实施待确认）

- 用户要求本轮先检查、审查和汇报，确认后才实施。本轮仅追加本记录；未修改业务代码、测试、DDL或冻结材料，未新增依赖，未commit、push或提交课程平台。拟修复范围在本轮回复中列出，不另建计划文档。
- 已读取11月9日、11月13日及最新日志、AGENTS、docs/04、docs/03九表/索引/事务/查询/接口，并审查现有服务与测试。开始时分支为codex/ecommerce-implementation；`git status --short`已有25项已跟踪改动及11个未跟踪路径组；`git diff --stat`为25 files changed, 431 insertions(+), 2577 deletions(-)。保留全部原有改动。检查期间前端、游客测试、docs/04及.gitignore继续被外部更新，以下初轮与复查结果分别记录，不将外部改动算作本轮实现。
- 环境只读核对：应用后端127.0.0.1:8000可访问；MySQL 8.0.40在127.0.0.1:33316，应用库scu_ecommerce与测试库scu_ecommerce_test分离；MySQL80服务为Stopped/Manual，本轮未操作该服务，也未重启后端。
- 初轮实际命令：`backend/.venv/Scripts/python.exe -m pytest -q`复跑完整输出为42 passed、1条Starlette/httpx弃用告警；`npm --prefix frontend test`为10 passed；`npm --prefix frontend run format:check`失败，11个文件格式告警且vite.config.ts:7多余右括号导致语法错误；`npm --prefix frontend run build`同处TS1005失败；现有构建上的`npm --prefix frontend run test:e2e`为2 passed（12.8s）。初轮E2E不能作为当时未成功构建源码的验收。
- 外部源码更新后再次执行：pytest为43 passed、1 warning（9.49s）；前端单元测试为15 passed；生产构建含类型检查通过（Vite构建8.52s，主包大于500kB告警）；重新构建后E2E为2 passed（7.6s）。最后格式检查仍失败，告警仅ProductCard.vue、UserLayout.vue、ProductListView.vue三文件。本轮未修复语法或格式；新增1项后端和5项前端游客测试来自外部工作。局部Ruff检查`backend/.venv/Scripts/python.exe -m ruff check --config backend/pyproject.toml backend/app db tests`通过。
- 真实MySQL测试库单独复现：订单列表请求status=PENDING，在ID分页后通过另一连接取消该单，返回total=1且items状态为CANCELLED，确认READ COMMITTED下跨语句分页过滤失配。极端输入created_start=0001-01-01T00:00:00+14:00触发时间转换溢出，响应500纯文本Internal Server Error；缺开始、缺结束、逆序时间均实际返回422 TIME_RANGE_INVALID。首次探针错误假定测试库残留alice，因账号不存在失败；改用独立命名测试数据后完成上述复现。探针不是新增自动测试，也未写入应用库。
- 查询审查：Q1到Q4的左闭右开时间、支付月、状态集合、订单金额粒度、按商品ID归并、并列按ID取前10、Q4管理员排除/取消订单/固定as_of符合契约。订单分页按订单ID取完整明细，没有直接LIMIT明细；当前未发现分页N+1。维护风险为queries.order_snapshots对Q1进行多次字符串替换，及分页COUNT/数据跨语句读取。库存COUNT还重复执行待支付占用聚合。
- 在隔离应用库以START TRANSACTION READ ONLY执行EXPLAIN，未写数据或DDL；样本15用户、18商品、21订单、26明细、9支付。Q1使用uk_orders_user_token（估计5行）、明细/支付唯一索引，有temporary/filesort；Q2/Q3使用idx_payment_paid_order（估计9行），聚合有temporary/filesort；Q4使用用户主键扫描（估计15行）及idx_orders_user_created反连接。用户/管理员订单ID分页分别使用idx_orders_user_created/idx_orders_status_created，反向索引扫描，无该分页步骤的filesort；商品分类价格筛选使用idx_product_category_status_price（估计3行），ID排序有filesort；关键词COUNT为ALL（估计18行）；库存按商品用uk_inventory_product，派生占用使用状态索引及temporary；用户COUNT使用idx_users_role_created；未下单用户反连接使用idx_orders_user_created。rows为优化器估计，未运行EXPLAIN ANALYZE；小样本扫描/聚合排序不是失败证据，目前不建议新增索引。实际服务SELECT次数：订单3，商品/库存/用户各2，未下单用户3（含NOW）。
- 事务审查未发现需重写锁顺序的缺陷：结算父车锁后商品/库存升序，取消订单锁后库存升序，支付锁订单；版本更新、单笔回滚、最多3次新会话重试及未知提交不重放增量已实现并有部分测试。仍缺完整的输入/权限边界、跨用户token、整页多单多明细、非零库存与历史引用删除、盘点负差额、改名销量归并/并列前10、固定as_of翻页、业务提交失联核对及更完整的API序列化与故障回滚测试。
- 当前索引未跟踪实际.env、预览/浏览器结果或常见数据库转储文件；逐文件检查索引内容未匹配本地数据库口令、管理员/演示口令或JWT密钥；相关敏感路径在可见Git历史中未发现提交。backend/.env、assets/preview和frontend/test-results被忽略。新frontend/.env.pages仅含两个公开VITE展示配置键，无口令/密钥键。.github/ci-template.yml仍为未启用模板，未运行或宣称远端CI通过。
- 两次E2E使应用库相对检查前增加用户4、分类4、商品/库存各4、订单6、明细6、成功支付2、购物车4；最终17用户、20商品、24订单、10支付，未删除演示数据。浏览器截图等仅更新被忽略的预览/测试输出。
- 文档问题：日志开头的2026-11-09“当前状态”仍是历史入口；新docs/04已记录用户授权游客浏览，与docs/03公开入口旧文字存在差异。本轮保留游客改造，不擅改契约或撤销现有授权。只读查询计划脚本、统一检查脚本、修复与回归测试均未落地，等待本轮用户确认。
- 交付前按开始时SHA-256复核：40份现存受保护文件（冻结报告/参考/图源/内容源、docs/03及db/schema.sql）均未变化；原有删除状态也未变化。最终`git status --short`仍为混合工作区，`git diff --cached --stat`为空；本轮唯一主动编辑是本日志的追加。

---

## 2026年11月14日 瑞士风前端、游客体验与Pages上线

- 按用户要求安装并读取guizang-ppt-skill，选择Swiss/IKB主题，将视觉语言适配Vue商品目录、详情、购物车、登录入口及统一组件；使用局部Lucide图标依赖和本地Unsplash示意图，不复制PPT运行时代码。
- 新增游客访问状态：原商品/分类查询接口允许匿名读取，仍拒绝非法令牌；购物车仅在浏览器保存，不增加角色或表、不扣真实库存，交易与管理接口继续鉴权。冻结报告、docs/03和内容源保持原样，授权差异集中记录在Limitation及实施清单。
- Pages构建使用明确标注的示例数据和hash路由；拒绝账户/交易/管理请求，不携带数据库配置或账号口令。通过独立暂存仓库只推送dist-pages产物，课程仓库保持私有。
- 已发布https://danielliu1219.github.io/scu-db-ecommerce-order-system/，gh-pages提交75be60d，GitHub Pages状态built，公开HTTP 200，线上资源名与本轮构建一致。修复发布API空响应的解析，重复发布保留分支历史。
- 实际验收：MySQL后端43项、前端15项、双角色浏览器回归2条、本地Pages浏览器2条、线上Pages浏览器2条全部通过；游客覆盖组合筛选、缺货、购物车改量/勾选/清空/刷新保存、交易拦截和390px手机布局；线上未发出业务API请求。类型/格式检查及完整系统、Pages两种构建通过。
- 已查看桌面及手机实测截图，修正商品图裁切和页脚对齐；截图等待动效稳定。39份受保护文件SHA-256不变，报告阶段原有未提交改动保留，文档在原文件内精简更新。

---

## 2026年11月15日 完成后端查询与事务质量加固

- 用户确认上一轮第3、4项范围，优先修复订单分页失配及时间换算溢出；分页总数与当前页必须同语句快照。游客方案重新等待确认，现有实现不扩大；不改九表DDL、接口路径、统计口径，不commit、不push。本轮保留原有47项已暂存文件及报告阶段未提交改动，不运行报告生成脚本。
- 按README核对本地root账号配置与33316端口后执行`backend/.venv/Scripts/python.exe -m db.dev_mysql start`，只启动已有隔离实例；原MySQL80服务始终Stopped。应用库scu_ecommerce、测试库scu_ecommerce_test保持分离。为E2E按README在8000启动本轮后端，未重新seed或删除应用数据。
- 改动前实际基线：`backend/.venv/Scripts/python.exe -m pytest -q`为43 passed、1 warning；`npm --prefix frontend run format:check`通过，三个此前格式失败文件已由既有工作修复；`npm --prefix frontend test`为15 passed；`npm --prefix frontend run build`通过。本轮前端文件SHA-256全部保持原样，无视觉或游客代码改动。
- 两个已证实缺陷先补回归：原实现3项失败（分页total=1但items为空、时区换算上下溢出各1项），修复后通过。应用订单查询改为SQLAlchemy独立参数化SELECT，保留Q1原文件；订单ID筛选/分页、总数、完整明细及支付由一条SELECT读取，防止READ COMMITTED下跨语句混合状态；空页用总数锚点保留total。商品、库存、用户、未下单用户分页同步采用单语句总数+数据；未下单用户另有一次NOW读取固定as_of。库存COUNT不再重复计算待支付占用量。时间转换捕获OverflowError并返回已有422错误码。
- 新增43项真实MySQL自动测试，总计86项；并加强已有快照金额、取消回补版本和失败支付无记录断言。覆盖并发分页、完整多单多明细、空页总数、时间边界/偏移、非法结算输入、金额/数量上界、跨用户token、Unicode/ID规范化重放、权限拒绝、清车后异常回滚、删除保护、盘点正负零差额、完整冲突details、统计改名/并列前10/固定as_of、API序列化和敏感错误。原生1205锁等待超时与1213死锁分别验证整笔回滚、新会话重试；结算/取消/支付提交响应丢失核对原事实，未知结算不重试、未知补货503及旧版本防重复入库均通过。
- 新增`db/query_plan.py`，每个连接设置SESSION TRANSACTION READ ONLY，检查Q1至Q4及9个实际分页场景，输出索引、估计rows、temporary/filesort和SELECT次数，支持JSON；测试验证运行前后数据不变。新增`scripts/verify.ps1`复用既有命令并失败即停止，README补运行方式；无新增依赖，CI仍为未启用模板。
- 最终完整命令`powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify.ps1 -E2E -QueryPlans`退出0：pytest **86 passed、1 warning（23.24s）**；Ruff通过；Prettier通过；Vitest **15 passed**；TypeScript/Vite构建通过（Vite 12.84s）；Playwright **2 passed（9.0s）**；13个查询计划场景全部执行成功。保留Starlette/httpx弃用、Vite主包大于500kB和Playwright颜色环境告警，不宣称远端CI通过。开发中一次测试误引用DTO类名造成收集错误、一次Ruff报告3条E731，均已修正并纳入最终通过结果。
- EXPLAIN样本为MySQL 8.0.40、21用户/24商品/30订单/35明细/12支付。Q1使用uk_orders_user_token（估计5行）及明细/支付唯一索引，有temporary/filesort；Q2/Q3使用idx_payment_paid_order（估计10行），聚合有temporary/filesort；Q4用用户主键（估计20行）及idx_orders_user_created反连接。订单分页的用户/状态索引估计5/9行并反向扫描；商品分类价格索引估计3行，关键词COUNT扫描估计24行；库存按商品用uk_inventory_product，待支付聚合仅一次；用户角色索引及未下单用户反连接有效。合并分页有派生表及页面结果排序，属于同语句一致性方案的实际代价，不据小样本扫描或排序添加索引。未执行EXPLAIN ANALYZE；rows不是实测扫描量。订单/商品/库存/用户分页各1条SELECT，未下单用户2条（NOW及一条总数+当前页SQL）。
- 本轮一次E2E新增应用数据：2用户、2分类、2商品/库存、3订单/明细、1成功支付、2购物车，全部保留；最终21用户、24商品、30订单、12支付。测试清理只作用于独立测试库，浏览器输出和后端运行日志位于忽略目录。
- 交付复核：44份受保护文件（冻结材料、内容源、docs/03、schema及Q1至Q4）SHA-256与本轮开始一致；原有删除状态保留，前端无改动。Git索引内容及HEAD逐一比较未变，当前索引未发现本地真实口令/JWT密钥匹配，未跟踪.env、预览或构建结果。无新增重复计划/交接文档，无过期本轮临时源文件需删除。仅游客保留与契约权限文字同步仍待用户确认，已记入唯一实施清单。

---

## 2026年11月15日 游客购物车手动导入与真实系统回归

- 接手分支codex/ecommerce-implementation为ab43c28、main为2dd4b9d，树内容一致；读取AGENTS、docs/03 §9、docs/04及日志。用户明确授权完成三项前端改动后提交相关文件、推送codex并合并main；保留既有报告阶段14项未提交文件改动及未跟踪冻结材料，不提交这些内容。
- 登录后仅在浏览器有游客条目时显示“导入游客购物车”；点击后逐条调用现有POST /cart/items，由服务端合并同商品增加量。每条成功立即移除对应游客记录，下架、缺货、已删除及数量溢出的条目保留并汇总提示。遇401、网络故障或未知提交结果停止后续导入，不自动重发；导入期间阻止重复点击和条目编辑。不自动导入、不新增接口或表。
- 游客结算先跳登录，成功后返回购物车页确认导入；账号购物车仍独立。购物车GET遇401时沿用请求层清令牌行为，然后一次性改读游客购物车；非401错误仍报告，失败写入不回退成游客加购。
- 新增guest-import.spec.ts与cart-view.spec.ts共15项Vitest用例，覆盖参数增加量、顺序提交与逐条清理、失败保留、匿名拒绝、失效/断网/未知结果停止、仅401回退、回退自身失败不循环、按钮条件/手动触发/防重复及汇总提示。真实系统新增tests/e2e/guest.spec.ts：匿名列表及详情→加购→刷新→改量/删除→登录→空账号购物车和导入入口；请求监测证明登录前无购物车请求、手动导入前无购物车写入，点击后恰有一次POST，游客记录清空且库存不变。
- 改动前npm --prefix frontend test为15 passed。最终powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify.ps1 -E2E退出0：pytest **86 passed、1 warning（60.21s）**，Ruff通过，格式通过，Vitest **30 passed（14.88s）**，TypeScript/Vite构建通过（Vite 29.43s），Playwright **3 passed（17.6s）**。保留既有Starlette/httpx弃用、Vite主包大于500kB及Playwright颜色环境告警；未运行远端CI或重新发布Pages。
- 使用已运行的127.0.0.1:33316隔离MySQL及8000后端，未重启或重新seed，原MySQL80为Stopped且未操作。一次完整E2E创建3个验收账号、3个分类、4个商品及库存、3个订单、1条成功支付；新增游客用例还保留1条账号购物车明细。验收数据保留，测试库清理由既有夹具负责。
- 本轮仅改3个前端源码文件、新增3个前端测试文件，必要文档为docs/03 §9游客交互说明、docs/04当前状态及本日志；无新增依赖、视觉改版、后端/DDL/统计/错误码改动。逐文件SHA-256复核确认其余既有文件均未变化，原有删除状态保留；构建和浏览器输出仍在忽略目录，没有新增重复计划或交接文档。

---

## 2026年11月15日 启用GitHub Actions

- 首次gh auth status只有gist/read:org/repo，按用户指示立即停止，未绕过权限。用户确认继续后复查已含workflow scope，才移动模板为.github/workflows/ci.yml；push/pull_request限定main及codex/**，权限为contents: read，不对gh-pages触发应用检查。
- 核对tests/conftest.py：拒绝应用库，先查scu_ecommerce_test是否有表，空库调用db.bootstrap.initialize；该函数只接受scu_ecommerce或scu_ecommerce_test。CI的TEST_DATABASE_URL保持scu_ecommerce_test，mysql:8.0使用临时凭据，不改测试隔离逻辑或业务代码。首次远端运行尚待推送后核验，后续追加真实结果。

---

## 2026年11月17日 续作CI核验、干净克隆与构建分包

- 上轮CI启用提交4925ab9已推codex，main合并77a954e。实际gh run watch --exit-status：codex运行43693251563和main运行43693366838均success；前者日志明确后端86 passed（22.33s）、前端30 passed，Ruff/格式/类型/构建通过。运行链接见docs/04，不以本地结果替代远端结论。
- 从HTTPS克隆main到系统临时目录scu-delivery-1794730339866，SHA为77a954eca5f690176b18c510c64ccb2d89a1f235，初始git status为空。python -m venv backend/.venv成功；跨日恢复后重跑pip install -r backend/requirements.lock、pip install -e backend --no-deps及npm --prefix frontend ci，全部退出0；pip check无依赖冲突。npm安装209包，报告8项漏洞（6 moderate、2 critical），独立npm audit证实来自开发依赖；omit=dev为0。未执行自动修复或大版本升级。
- 仅本地复制忽略的backend/.env到clone，不打印口令。pytest使用scu_ecommerce_test；未运行bootstrap/seed/demo、未启动克隆后端、未执行真实系统E2E。恢复时Get-NetTCPConnection未列出监听，原项目db.dev_mysql start因端口已占用退出1且未启动实例；随后socket和只读SQL确认原33316仍可用、MySQL 8.0.40，应用九表行数及SHA-256与11月15日基线一致。没有停止或重启服务，8000当时不可连接。
- clone内powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify.ps1退出0：后端86 passed、1 warning（26.81s），Ruff通过，Prettier通过，Vitest 30 passed（8.33s），TypeScript/Vite构建通过（12.51s）。git status仍空；.env与dist均被忽略，34个产物文件未匹配本地数据库口令、JWT或演示口令。README补固定RUNTIME不能跨克隆并存、测试库不可并行跑多套pytest，以及不初始化应用库的演练边界。
- 包含绝对路径和目录校验的临时clone清理命令Remove-Item -LiteralPath ... -Recurse -Force被自动审批整体拒绝，原因为“blocked by policy”。降低范围单独删除clone/backend/.env也被拒绝，未换工具绕过；clone及.env仍在C:/Users/ltyco/AppData/Local/Temp/scu-delivery-1794730339866，需用户手动清理，不能报告已清理。
- frontend/vite.config.ts只增加manualChunks，将Vue/vue-router/pinia与Element Plus拆为vendor；无新依赖、无业务代码或样式改动。普通构建入口1060.21kB降为21.45kB，Vue 114.33kB、Element Plus 924.63kB；Pages入口18.68kB、Vue 114.44kB、Element Plus 924.63kB。依赖仍需加载，不宣称总下载量等比例下降；500kB告警继续输出，未修改告警阈值。
- 工作区scripts/verify.ps1退出0：后端86 passed、1 warning（27.05s），Ruff/格式通过，Vitest 30 passed（5.87s），类型/构建通过（9.38s）。build:pages通过（14.27s），本地test:pages两项通过（11.4s），覆盖桌面游客流程、手机布局、hash深链及无业务API请求；真实系统E2E本轮未运行，应用库不写入。
- httpx锁定/实际0.28.1，pip index versions httpx仍为最新版，pip check通过；实际Starlette 1.10.0源码在没有httpx2时发出该弃用提示。按用户允许保留告警，不添加新包、不改测试行为。其余保留的提示包括npm开发依赖审计、whatwg-encoding/lucide-vue-next弃用及Actions旧Node运行时和runner镜像提示。
- 按README执行publish_pages.py --skip-build退出0，gh-pages产物提交c2e995f205c4a6c1ab690820d7a8eeb2b4356ceb，GitHub Pages状态built。线上首页和4个入口资源均HTTP 200，JS入口/两个vendor/CSS与本地SHA-256一致；PAGES_BASE_URL指向线上后test:pages两项通过（30.1s）。普通构建/Pages仍分别包含16/17个动态import；base/hash深链与游客行为验证通过。gh-pages只运行原生pages-build-deployment（44046913746成功），Application checks分支过滤生效。
- 最终dist的36个文件及dist-pages的37个文件未匹配本地数据库口令、JWT或账号口令。测试通过后的应用库只读复核连接33316报2003/WinError 10061，随后33316和8000探测均不可连接；未执行stop或重启，末次数据库摘要未能重取，此环境状态不替代或抹去先前真实通过结果。
