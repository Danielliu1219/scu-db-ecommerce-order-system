# 编码实施清单

最后更新：2026-11-14。用户已确认实施；这是唯一实施清单，接手时同时读取 AGENTS、docs/03 和 PROJECT_LOG 最新记录。

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
- 订单ID分页后单查询取完整详情；重放、详情、支付不拼接不同时刻状态。
- JWT和未确认结算存sessionStorage，结算按用户隔离；结果未知沿用原token和载荷。
- COMMIT断连先核对token/状态；不可判定的增量操作不自动重发，既定503 details标记未知。
- 空月份不补零；as_of翻页固定；种子只补缺失记录。

## 文档维护规则

- 不新增重复计划、总结、交接文档；本文件只保留当前状态、默认决策和尚未解决事项。
- README只保留现行入口与运行命令，PROJECT_LOG只追加简短真实结果；报告历史及来源证据保留。
- 每个FR结束检查重复说明与过期临时材料；连续三项FR后及最终交付前集中整理一次。
- 仅清理本轮临时/缓存材料；冻结文件、用户材料、历史日志不自动删除。需要精简历史时先归档且保持入口。

## 当前交接点

已完成九项接口、事务、页面及演示数据；42项真实MySQL后端测试、10项前端测试、2条Playwright链路通过，类型检查与生产构建通过。39份冻结文件哈希不变。

本地演示入口为http://127.0.0.1:8000，账号admin及demo_01至demo_03，口令在被忽略的backend/.env中。隔离MySQL端口33316，原MySQL80服务仍停止。启动命令统一见README。

已推送到codex/ecommerce-implementation，应用实现提交为ead959d；只纳入应用、测试及必要契约/运行文档，报告阶段既有改动保留本地。CI配置保存为.github/ci-template.yml未启用模板；现有OAuth凭据缺workflow权限，远端未执行自动检查，本地验收已完成。

文档已集中为本清单、README和原项目日志，不新增验收总结副本。仅本轮失败的中文路径MySQL初始化目录仍在忽略的assets/preview/runtime-mysql中，递归清理被自动审批策略拦截；不影响运行或托管。
