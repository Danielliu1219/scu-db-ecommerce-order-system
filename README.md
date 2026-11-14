# 电商订单管理系统

四川大学《数据库系统原理》课程设计，第20组。FastAPI + SQLAlchemy 2 + MySQL 8.0，Vue 3 + Element Plus，普通用户与管理员两类角色，FR-01至FR-09。

## 项目入口

- [编码约定](AGENTS.md)：接手先读；保留现有未提交工作。
- [数据库与接口契约](docs/03-database-design.md)：九表、DDL、事务、错误码及统计口径的唯一依据。
- [实施清单](docs/04-implementation.md)：当前进度、默认决策、验收和文档维护；不另建重复计划。
- [项目日志](PROJECT_LOG.md)：历史与实际验证结果；[限制说明](Limitation.md)：既定范围及限制。
- [冻结课程报告](deliverables/第20组_电商订单管理系统_课程报告.docx)：30页、15幅纯黑白图；[报告文字](docs/02-course-report.md)及references只读。

## 安装

要求Python 3.11+、Node.js 20.19+（或22.12+）、MySQL 8.0.16+。本机已核对MySQL 8.0.40。下列PowerShell命令在项目根目录执行，依赖全部安装到项目局部环境。

```powershell
python -m venv backend/.venv
& backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.lock
& backend/.venv/Scripts/python.exe -m pip install -e backend --no-deps
npm --prefix frontend ci
```

使用Codex时优先使用工作区提供的Python和Node。根目录requirements.txt只服务原报告脚本，与应用依赖分开。

## 数据库与初始化

已有MySQL：先核对端口、账号和权限，再启动服务。复制backend/.env.example为backend/.env，填写DATABASE_URL、独立TEST_DATABASE_URL和至少32字符随机JWT_SECRET。URL中的口令须进行URL编码；禁止提交.env或真实口令。

也可使用本机MySQL二进制启动隔离开发实例：

```powershell
& backend/.venv/Scripts/python.exe -m db.dev_mysql start
```

此辅助工具使用127.0.0.1:33316、临时目录下的独立数据目录，初始化本实例root随机口令并在不存在时写入本地.env；不操作原MySQL80服务。MySQL二进制不在默认位置时使用--bin指定其bin目录。Windows数据目录放在系统临时目录，避开中文路径兼容问题。

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
& backend/.venv/Scripts/python.exe -m db.dev_mysql stop
```

## 测试

```powershell
& backend/.venv/Scripts/python.exe -m pytest -q
npm --prefix frontend test
npm --prefix frontend run build
```

后端自动在独立scu_ecommerce_test空库初始化，按外键顺序清理测试数据；拒绝使用应用库。并发测试使用真实MySQL独立连接，不使用SQLite替代行锁。

浏览器验收需已运行后端、已构建页面、已执行seed，并提供对应ADMIN_PASSWORD；会通过业务接口创建演示账号、商品和订单：

```powershell
npm --prefix frontend exec -- playwright install chromium
npm --prefix frontend run test:e2e
```

后端运行时可刷新生成接口类型：npm --prefix frontend run gen:api。Python依赖版本记录在backend/requirements.lock，前端使用package-lock.json。

源码格式使用局部Ruff和Prettier：Python执行`python -m ruff check --config backend/pyproject.toml backend/app db tests`，前端执行`npm --prefix frontend run format:check`。CI配置保留为`.github/ci-template.yml`未启用模板；当前Git凭据缺少workflow权限，未启用GitHub Actions。本地检查已实际运行。

## 文档与原材料管理

每个FR结束更新实施清单；每三项FR及交付前整理一次过期临时材料和重复说明。README只保留现行入口与运行命令，日志只记真实结果；不自动删除历史日志、冻结报告、图源或用户参考文件。报告生成脚本保留在scripts，仅供已授权的文档工作，本阶段不运行。
