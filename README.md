# 电商订单管理系统

四川大学《数据库系统原理》课程设计，第20组。FastAPI + SQLAlchemy 2 + PostgreSQL 18，Vue 3 + Element Plus，普通用户与管理员两类角色，FR-01至FR-09。

> **在线体验**：[打开 GitHub Pages 展示站](https://danielliu1219.github.io/scu-db-ecommerce-order-system/)（示例数据，游客购物车仅保存在浏览器）

## 线上游客体验

展示站可按名称/分类/价格筛选、查看详情、加购、改量、勾选、删除和清空游客购物车，刷新后保留。使用明确标注的示例数据，不产生真实订单，不提供真实账号注册、登录和管理写入。

UI依据用户指定的[guizang-ppt-skill](https://github.com/op7418/guizang-ppt-skill)，选择瑞士国际主义/克莱因蓝视觉语言并适配Vue；商品示意图来源见frontend/public/image-credits.txt。gh-pages分支仅包含编译后的前端产物。

本地系统同样支持匿名浏览上架商品，游客购物车独立保存在浏览器中，不占用库存、不自动合并到账号；登录后仍使用后端真实业务。

## 项目入口

- [编码约定](AGENTS.md)：接手先读；保留现有未提交工作。
- [数据库与接口契约](docs/03-database-design.md)：九表、DDL、事务、错误码及统计口径的唯一依据。
- [实施清单](docs/04-implementation.md)：当前进度、默认决策、验收和文档维护；不另建重复计划。
- [项目日志](PROJECT_LOG.md)：历史与实际验证结果；[限制说明](Limitation.md)：既定范围及限制。
- 本地冻结报告：`deliverables/第20组_电商订单管理系统_课程报告.docx`（30页、15幅纯黑白图）；报告文字`docs/02-course-report.md`及references只读，未纳入本轮代码推送。

## 安装

要求Python 3.11+、Node.js 20.19+（或22.12+）、PostgreSQL 18+（需要ICU排序规则支持）。本机已核对PostgreSQL 18.6。下列PowerShell命令在项目根目录执行，依赖全部安装到项目局部环境。

```powershell
python -m venv backend/.venv
& backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.lock
& backend/.venv/Scripts/python.exe -m pip install -e backend --no-deps
npm --prefix frontend ci
```

使用Codex时优先使用工作区提供的Python和Node。根目录requirements.txt只服务原报告脚本，与应用依赖分开。

## 数据库与初始化

已有PostgreSQL：先核对端口、账号和权限。复制backend/.env.example为backend/.env，填写postgresql+psycopg格式的DATABASE_URL、独立TEST_DATABASE_URL和至少32字符随机JWT_SECRET。初始化账号需要创建数据库和public schema对象的权限；禁止提交.env或真实口令。

使用本机PostgreSQL 18二进制启动项目隔离实例：

```powershell
& backend/.venv/Scripts/python.exe -m db.dev_postgres start
```

工具从PATH寻找pg_ctl，也可用--bin指定安装目录的bin路径。默认端口55432，数据目录为系统临时目录下scu-ecommerce-postgres-加工作区路径摘要；不注册或操作系统服务。新集群使用随机口令、SCRAM认证、UTF8与Asia/Shanghai，仅监听127.0.0.1。已有.env不会覆盖；--env-file可指定另一个未跟踪配置文件。多个克隆的数据目录不同，但同时启动仍需使用不同--port。

以下命令仅用于新建的空应用库；已有业务库不得为了演练重置、重复导入或覆盖。

```powershell
& backend/.venv/Scripts/python.exe -m db.bootstrap
& backend/.venv/Scripts/python.exe -m db.seed
& backend/.venv/Scripts/python.exe -m db.demo
```

bootstrap只在空库执行冻结schema.sql，已有业务表时停止。seed通过ADMIN_PASSWORD、DEMO_PASSWORD环境变量或安全交互输入获取8至64字符密码，只补缺失的admin、demo_01至demo_03及零库存商品，不覆盖已有记录。demo仅在订单集为空时经业务服务补货并生成待支付、取消、支付、发货、完成五种状态；重复运行停止。demo_03保留为从未下单用户。

## 启动与演示

开发时分别启动两个终端：

```powershell
& backend/.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
npm --prefix frontend run dev
```

开发页面：http://127.0.0.1:5173；接口文档：http://127.0.0.1:8000/docs。Vite将/api原路径代理到8000。

同源演示先构建页面，再启动后端；浏览器访问http://127.0.0.1:8000：

```powershell
npm --prefix frontend run build
& backend/.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

管理员维护商品和可售库存；普通用户选购、下单、模拟支付；管理员发货；用户收货。待支付订单持续占用库存，只由所属用户手动取消。盘点输入为可售量，版本冲突后刷新并重新确认。

本地隔离实例使用完后：

```powershell
& backend/.venv/Scripts/python.exe -m db.dev_postgres stop
```

## 测试

```powershell
& backend/.venv/Scripts/python.exe -m pytest -q
npm --prefix frontend test
npm --prefix frontend run build
```

后端自动在独立PostgreSQL scu_ecommerce_test空库初始化，按外键顺序清理测试数据；拒绝使用应用库。并发测试使用真实PostgreSQL独立连接，不使用SQLite替代行锁。

从main的干净克隆演练时，先按“安装”创建该克隆自己的venv并执行npm ci。若没有另一个独立PostgreSQL实例，可仅在本机复制既有backend/.env到克隆目录，确认TEST_DATABASE_URL指向scu_ecommerce_test后运行本节检查；同一测试库不要同时运行多套pytest。此方式不运行bootstrap/seed/demo，不停止既有8000后端，跳过真实系统E2E；不能据此宣称新实例初始化或完整演示已通过。演练结束删除临时克隆，.env必须保持忽略且不提交。

也可在项目根目录统一执行下列检查。脚本使用现有局部依赖，任一步失败即停止；不启动数据库、不提交代码。`-E2E`要求8000端口后端和seed已就绪，会创建验收数据；`-QueryPlans`只读检查隔离应用库。

```powershell
./scripts/verify.ps1
./scripts/verify.ps1 -E2E -QueryPlans
```

查询计划可单独运行，默认读取测试库，也可指定有演示数据的隔离应用库：

```powershell
& backend/.venv/Scripts/python.exe -m db.query_plan
& backend/.venv/Scripts/python.exe -m db.query_plan --database application --json
```

脚本为每个数据库连接设置只读事务，覆盖Q1至Q4及实际分页服务，输出所用索引、估计扫描行数、Sort、Hash/Aggregate等计划节点和语句数；不写业务数据或修改DDL。行数是优化器估计，不是EXPLAIN ANALYZE实测；小表扫描或聚合排序不直接判失败。

浏览器验收需已运行后端、已构建页面、已执行seed，并提供对应ADMIN_PASSWORD；会通过业务接口创建演示账号、商品和订单：

```powershell
npm --prefix frontend exec -- playwright install chromium
npm --prefix frontend run test:e2e
```

后端运行时可刷新生成接口类型：npm --prefix frontend run gen:api。Python依赖版本记录在backend/requirements.lock，前端使用package-lock.json。

展示版的构建、自动启动本地预览验收及发布命令如下。发布需要Git和已授权的GitHub CLI；脚本只推送dist-pages产物到gh-pages，不使用Actions权限、不改变课程仓库可见性。

```powershell
npm --prefix frontend run build:pages
npm --prefix frontend run test:pages
& backend/.venv/Scripts/python.exe frontend/scripts/publish_pages.py --skip-build
```

源码格式使用局部Ruff和Prettier：Python执行`backend/.venv/Scripts/python.exe -m ruff check --config backend/pyproject.toml backend/app db tests`，前端执行`npm --prefix frontend run format:check`。GitHub Actions配置为`.github/workflows/ci.yml`，仅对main、codex/**分支的push及以这些分支为目标的pull_request运行，不对gh-pages触发应用检查。后端使用临时PostgreSQL 18服务，由测试夹具自动创建并初始化scu_ecommerce_test；前端执行格式、单测、类型检查和构建。实际结果见仓库Actions，不将本地通过等同于远端通过。

## 文档与原材料管理

每个FR结束更新实施清单；每三项FR及交付前整理一次过期临时材料和重复说明。README只保留现行入口与运行命令，日志只记真实结果；不自动删除历史日志、冻结报告、图源或用户参考文件。报告生成脚本保留在scripts，仅供已授权的文档工作，本阶段不运行。
