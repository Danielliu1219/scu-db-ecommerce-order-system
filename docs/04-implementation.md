# 编码实施清单

最后更新：2026-11-17。按用户确认完成PostgreSQL迁移；仅更新当前实现与运行文档，冻结材料保留；这是唯一实施清单，接手时同时读取 AGENTS、docs/03 和 PROJECT_LOG 最新记录。

## 契约与边界

- docs/03 是九表业务模型、DDL、接口、错误码、事务和统计口径的唯一实现契约；物理DDL已按本轮授权迁移PostgreSQL，业务口径保持不变。
- 报告、references、deliverables、assets/report、docs/02、scripts/data.py 只读。
- 同步 FastAPI + SQLAlchemy 2 + psycopg 3；Pydantic 2；PyJWT HS256（2小时）；pwdlib Argon2id。
- Vue 3 + TypeScript + Element Plus + Router + Pinia + Vite；fetch；/api 原路径代理后端8000。
- schema.sql 与docs/03一致，仅初始化空库，不使用create_all覆盖已有库；PostgreSQL 18+，READ COMMITTED，Asia/Shanghai。
- 身份查询短会话；业务写入口独立会话和完整事务；辅助函数不提交；40P01/55P03/40001新会话整笔重试，最多3次。
- 金额 Decimal/两位字符串；无符号64位ID和版本使用NUMERIC(20,0)+范围CHECK、接口字符串；时间秒精度、+08:00。业务层校验角色与归属。

## 文件职责

- backend/app：config/database/models 为基础；transactions/errors/security/dependencies 为横切行为；value_types/checkout_payload/queries 为公共规则。
- backend/app/api、schemas、services：identity(auth/users)、catalog、cart、orders、payments、inventory、statistics 各自对应路由、DTO和事务；不加 Repository 层。
- frontend/src：api请求、types接口类型、stores身份、utils结算和格式、layouts角色导航、components订单和支付、views各FR页面。
- db：schema.sql、bootstrap.py、seed.py、demo.py、queries/q1至q4；种子不覆盖已有数据，演示经业务服务生成。
- tests：独立PostgreSQL夹具、契约、九项FR、并发、重试；frontend/tests：客户端、身份、结算、库存、浏览器演示。

## 执行和验收

| 顺序 | 切片 | 核心验收 | 状态 |
|---|---|---|---|
| 0 | M0 | 环境、九表、事务、统一错误、测试隔离、README命令 | 完成 |
| 1 | FR-01 | USER与cart共同提交，登录、资料、改密、管理员用户查询 | 完成 |
| 2 | FR-07 | 分类唯一、商品与零库存共同创建、上下架、删除保护 | 完成 |
| 3 | FR-08 | 可售量、派生占用、版本、补货、盘点差额、溢出 | 完成 |
| 4 | FR-02 | 上架商品组合检索、详情、价格边界、零库存 | 完成 |
| 5 | FR-03 | 父行锁、加购合并、改量、勾选、删除、参考总额 | 完成 |
| 6 | FR-04 | 下单/快照/扣库/清车原子性，token规范化与重放 | 完成 |
| 7 | FR-05 | 按订单分页、归属、取消回补、发货、收货 | 完成 |
| 8 | FR-06 | 模拟失败无记录、成功原子提交、重复返回原事实 | 完成 |
| 9 | FR-09 | 四条查询、订单粒度、支付窗口、固定as_of | 完成 |

每项完成后运行对应 tests/test_frNN_*.py；修改公共事务时运行关联回归。最终运行后端全套、前端测试、类型检查、构建、Playwright完整链路。不得把设计SQL核验当业务测试。

## 已确认默认细节

- 已支付的重复模拟返回原事实；selected 使用布尔值；失效条目可取消勾选/删除，再勾选须检查。
- 购物车和统计聚合使用宽Decimal；只有订单写入受单订单金额上限约束。
- 无偏移时间按上海解释，带偏移转换；拒绝非零小数秒；页面结束日转次日00:00。
- 非订单列表按ID升序；关键词字面包含并转义LIKE通配符，phone精确查询。
- 库存冲突details返回product_id/available/version/updated_at，不自动采用新版本重发。
- 所有分页的总数和当前页在同一条SQL中读取；订单先在该语句内部分页订单ID再关联全部明细，越界空页仍保留总数。重放、详情、支付使用独立参数化查询，不替换Q1文本。
- JWT和未确认结算存sessionStorage，结算按用户隔离；结果未知沿用原token和载荷。
- COMMIT断连先核对token/状态；不可判定的增量操作不自动重发，既定503 details标记未知。
- 空月份不补零；as_of翻页固定；种子只补缺失记录。

## 文档维护规则

- 不新增重复计划、总结、交接文档；本文件只保留当前状态、默认决策和尚未解决事项。
- README只保留现行入口与运行命令，PROJECT_LOG只追加简短真实结果；报告历史及来源证据保留。
- 每个FR结束检查重复说明与过期临时材料；连续三项FR后及最终交付前集中整理一次。
- 仅清理本轮临时/缓存材料；冻结文件、用户材料、历史日志不自动删除。需要精简历史时先归档且保持入口。

## 当前交接点（2026-11-17）

### PostgreSQL迁移

- 使用PostgreSQL 18.6与psycopg 3.3.9，九表实体、接口、错误码、业务状态和统计口径不变。数据库驱动、连接设置、DDL、SQL、事务SQLSTATE识别、EXPLAIN、真实数据库测试及CI服务均已迁移。
- ID、外键与version采用NUMERIC(20,0)+范围CHECK保持完整无符号64位API范围，ORM转换为Python int；常规生成ID使用独立BIGINT序列。文本使用ICU app_ci保留大小写/重音不敏感的查询及唯一性；token、摘要和状态使用C精确比较。时间为上海秒级TIMESTAMP，业务UPDATE在同事务写updated_at，不增触发器。
- 已保留并迁移24用户、23分类、28商品、23购物车、1购物车明细、33订单、38订单明细、28库存、13支付。源与目标规范化逐行SHA-256均为f0f8ff987f1633c0f5b58f894304db00ecf6cab20cf4a30c31f48d255ffabd96，核对后才切换backend/.env；原数据目录及只读快照保留，真实配置/数据均不提交。
- 项目隔离实例位于127.0.0.1:55432，系统既有数据库服务未操作。dev_postgres使用按工作区路径区分的临时数据目录，bootstrap只接受scu_ecommerce/scu_ecommerce_test并拒绝非空库；本次迁移库未运行seed/demo覆盖原数据。
- 最终scripts/verify.ps1 -E2E -QueryPlans退出0：后端91项（19.57s）、前端30项、真实系统E2E 3项（9.1s）通过，Ruff/Prettier/类型/构建及13个只读查询计划场景通过。覆盖原生40P01死锁、55P03超时、40001重试、提交响应失联、分页快照、统计、ICU语义、最大ID/版本和初始化保护；远端CI结果在推送后单独核验。两次浏览器验收新增数据保留，原有九表记录复核仍逐行一致。
- 用户确认：仅同步AGENTS、README、docs/03、docs/04和当前限制说明；冻结报告、references、deliverables、assets/report、docs/02及scripts/data.py保留，历史日志只追加。旧引擎设计与核验记录保留在历史日志中，不改写为本次结果。

### 已完成的前端与交付工作

- 游客仅匿名读商品/分类，购物车存浏览器；登录不自动合并，购物车页手动导入逐条复用现有接口，成功移除、失败保留并汇总。401清令牌后重载游客购物车，不将失败写入转换为游客加购。
- GitHub Actions已正式启用，仅对main/codex/**触发应用检查，gh-pages只运行原生Pages部署。此前启用和分包提交的远端运行成功记录见PROJECT_LOG；当前工作流使用postgres:18，真实数据库结果单独验证。
- 分包无新增前端依赖；普通入口21.45kB、Vue vendor 114.33kB、Element Plus vendor 924.63kB。Pages入口18.68kB，Vue vendor 114.44kB；Element Plus仍超过500kB并保留告警，未调高阈值。页面路由保持动态导入。
- Pages产物c2e995f，线上HTTP 200、4个入口资源SHA-256匹配，本地及线上游客各2项通过；地址https://danielliu1219.github.io/scu-db-ecommerce-order-system/，仅示例数据，无真实账号或交易。
- 干净克隆演练的main SHA为77a954eca5f690176b18c510c64ccb2d89a1f235，安装、后端86项、前端30项、Ruff/格式/类型/构建通过；该结果属于迁移前版本，不充作当前数据库迁移验收。

### 保留事项

- 临时克隆C:/Users/ltyco/AppData/Local/Temp/scu-delivery-1794730339866及其中.env的删除被自动审批以“blocked by policy”拒绝，尚待用户手动清理；未用其他工具绕过，内容未提交。
- httpx 0.28.1已是当前可用稳定版；Starlette要求迁移到httpx2才消除弃用提示，本轮保留提示，不改测试行为。npm audit的8项开发依赖漏洞（6 moderate、2 critical）涉及Vitest/tinypool等，omit=dev为0；未执行force升级或改变测试框架。Actions旧Node运行时/runner镜像提示及前端大包告警仍在。
