# 编码实施清单

最后更新：2026-11-15。当前进行GitHub Actions启用、干净克隆交付演练与构建告警清理；这是唯一实施清单，接手时同时读取 AGENTS、docs/03 和 PROJECT_LOG 最新记录。

## 契约与边界

- docs/03 是九表、DDL、接口、错误码、事务和统计口径的唯一实现契约，不改表。
- 报告、references、deliverables、assets/report、docs/02、scripts/data.py 只读。
- 同步 FastAPI + SQLAlchemy 2 + PyMySQL；Pydantic 2；PyJWT HS256（2小时）；pwdlib Argon2id。
- Vue 3 + TypeScript + Element Plus + Router + Pinia + Vite；fetch；/api 原路径代理后端8000。
- schema.sql 直接提取定稿 DDL，不使用迁移或 create_all；MySQL 8.0.16+，READ COMMITTED，Asia/Shanghai。
- 身份查询短会话；业务写入口独立会话和完整事务；辅助函数不提交；1213/1205新会话整笔重试，最多3次。
- 金额 Decimal/两位字符串；BIGINT ID和版本字符串；时间秒精度、+08:00。业务层校验角色与归属。

## 文件职责

- backend/app：config/database/models 为基础；transactions/errors/security/dependencies 为横切行为；value_types/checkout_payload/queries 为公共规则。
- backend/app/api、schemas、services：identity(auth/users)、catalog、cart、orders、payments、inventory、statistics 各自对应路由、DTO和事务；不加 Repository 层。
- frontend/src：api请求、types接口类型、stores身份、utils结算和格式、layouts角色导航、components订单和支付、views各FR页面。
- db：schema.sql、bootstrap.py、seed.py、demo.py、queries/q1至q4；种子不覆盖已有数据，演示经业务服务生成。
- tests：独立MySQL夹具、契约、九项FR、并发、重试；frontend/tests：客户端、身份、结算、库存、浏览器演示。

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

## 当前交接点（2026-11-15）

### CI与交付演练

- 用户完成交互授权后，gh auth status已确认workflow scope；原模板移动至.github/workflows/ci.yml，仅对main和codex/**的push/pull_request运行，不对gh-pages运行应用检查。保留真实MySQL测试夹具与scu_ecommerce_test隔离规则，首次远端结果待实际运行后记录。
- 干净克隆使用系统临时目录，不启动第二个固定RUNTIME实例、不改应用库、不停止33316或8000；没有独立新实例时只复用测试库，跳过bootstrap/seed/demo与E2E。

### 游客购物车集成

- 登录不自动导入。普通用户购物车页仅在localStorage有游客条目时显示手动导入入口；逐条复用POST /cart/items合并数量，逐条清理成功记录，保留下架/缺货/已删除等失败记录并汇总提示。登录失效、网络中断或结果未知停止后续导入，不自动重发；导入过程中禁用重复点击和条目编辑。
- 游客结算登录后返回购物车页，账号购物车保持独立。购物车读取401清令牌后重新读取游客购物车；仅对读取回退，不把失败写入转换为游客加购。
- 实际执行scripts/verify.ps1 -E2E退出0：真实MySQL后端86项、Vitest 30项、真实系统E2E 3项通过；Ruff、格式、类型检查及构建通过。新增15项前端用例和1条真实游客链路，覆盖部分失败保留、重复点击、未知结果停止、401回退及导入前无服务端购物车写入。
- 不新增依赖、后端接口或表，九表DDL、统计口径和错误码保持不变。按本轮授权仅提交相关前端、测试和必要文档，推送codex后合并main；冻结材料与历史未提交改动继续保留。

### 2026-11-15 后端质量加固

- 已完成订单分页跨语句状态失配和时区换算溢出修复，所有分页总数/当前页同语句读取；独立订单查询替代Q1字符串替换，库存计数移除占用聚合。九表DDL、接口路径和统计口径保持不变。
- 2026-11-15实际执行verify.ps1 -E2E -QueryPlans：真实MySQL后端86项、前端15项、E2E两条通过，Ruff/格式/类型/构建通过；包含原生1205/1213、提交失联、并发分页、空页总数及统计边界测试。query_plan.py只读覆盖13个场景，不以全扫描判失败，目前没有加索引依据。
- 前端三个文件在本轮开始时已通过格式检查，本轮未编辑前端文件。原有暂存内容及HEAD不变，未commit、push或重新发布Pages；完整命令和告警见PROJECT_LOG。
- 2026-11-15用户确认保留游客只读方案：商品列表、详情、分类匿名可读，游客购物车仅存浏览器；docs/03 §9已同步，不新增角色或表。下方11月14日游客/Pages条目保留为当时记录。
- 2026-11-15仓库状态：仓库为Public；main与codex的README均已加入展示站入口并推送；GitHub About的Website指向Pages。应用代码、测试及本文件其余改动已同步提交并推送，main已合并codex实现。

### 2026-11-14 既有前端与Pages状态

- 已上线：https://danielliu1219.github.io/scu-db-ecommerce-order-system/ 。仓库当前为Public，gh-pages仅发布前端产物，原生Pages构建状态built；GitHub仓库About的Website已设为同一地址。
- 用户新增游客测试需求：商品列表、详情、分类匿名可读；游客购物车在浏览器持久保存，不扣库存、不自动合并到账号。不增加数据库角色或表，订单/支付/资料/管理接口继续鉴权。此明确授权覆盖docs/03原文中的商品登录要求，原文和冻结报告不改动。
- 使用用户指定guizang-ppt-skill的Swiss/IKB视觉方向，适配Vue和Element Plus；仅借鉴设计规则，不复制PPT运行时代码。示意图为本地打包的Unsplash照片，来源随前端保留。
- Pages明确使用示例数据，支持筛选、详情、购物车增删改勾选和清空；不提供真实注册/登录/交易，不包含后端口令或令牌。hash路由与base支持项目子路径。
- 验证：真实MySQL后端43项、Vitest 15项、本地双角色交易2条、本地Pages游客2条、线上Pages游客2条通过；类型、格式和两种生产构建通过。39份冻结文件哈希不变。
- 源码继续在codex/ecommerce-implementation；当前Pages产物提交75be60d。发布命令见README，frontend/scripts/publish_pages.py仅推送静态产物，现有Git权限即可发布，无需workflow scope。
- 本地完整系统：http://127.0.0.1:8000；账号admin、demo_01至demo_03，密码在忽略的backend/.env。MySQL隔离端口33316，原MySQL80服务保持原状。完整交易测试保留。
- 文档只维护本清单、README、Limitation和原日志，不新增计划/验收副本。历史中被策略拦截清理的失败初始化目录仍在忽略的预览区；自定义CI仍保留未启用模板。
