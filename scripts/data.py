# -*- coding: utf-8 -*-
"""项目单一数据源（Single Source of Truth）。

Word、Excel、Markdown 文档均由本文件的数据生成，修改内容后重新运行
`python scripts/build_deliverables.py` 即可。请勿直接手改生成物。
"""

from __future__ import annotations

PROJECT = {
    "name": "电商订单管理系统",
    "en_name": "E-Commerce Order Management System",
    "code": "SCU-DB-2026-EC-01",
    "scheme": "给定方案一",
    "group_no": "X",
    "university": "四川大学",
    "college": "人工智能学院",
    "course": "数据库系统原理",
    "course_full": "2026 年《数据库系统原理》课程设计",
    "instructor": "郭际香",
    "date": "2026 年 11 月",
    "version": "V1.0",
}

ROLES = [
    {
        "role": "游客",
        "scope": "未登录访问者",
        "permissions": "浏览首页、按名称/分类/价格检索商品、查看商品详情、注册与登录；不能加入购物车、下单或访问后台。",
    },
    {
        "role": "普通用户",
        "scope": "已注册且状态正常的买家",
        "permissions": "维护个人资料与收货地址；管理购物车；提交订单、模拟支付、取消未支付订单、确认收货；查询本人订单与明细。",
    },
    {
        "role": "管理员",
        "scope": "平台运营与仓储管理人员",
        "permissions": "维护分类、商品、库存与预警；查询和处理订单、发货；管理用户状态；查看销售统计与报表。",
    },
]

FUNCTIONS = [
    {
        "id": "FR-01",
        "name": "用户注册与登录",
        "role": "游客 / 普通用户 / 管理员",
        "summary": "注册、登录、退出与账号状态控制，按角色进入前台或后台。",
        "desc": "游客注册账号；用户登录、退出；系统按角色进入前台或后台。密码加盐哈希存储，管理员可启用/禁用账号。",
        "constraints": "用户名、手机号唯一；密码不少于 8 位且同时包含字母和数字；连续 5 次登录失败锁定 10 分钟；禁用账号禁止登录；管理员账号由系统初始化。",
        "input": "用户名、密码、确认密码、手机号、验证码；登录凭证。",
        "process": "格式与唯一性校验 → 密码哈希 → 写入 users → 认证 → 签发 JWT → 按角色跳转。",
        "output": "注册/登录结果、JWT 令牌、角色首页；失败原因提示。",
        "tables": "users",
    },
    {
        "id": "FR-02",
        "name": "商品浏览与检索",
        "role": "游客 / 普通用户",
        "summary": "按名称、分类、价格区间组合检索商品，查看详情与可售库存。",
        "desc": "展示分类与上架商品；支持按名称模糊、分类、价格区间组合筛选，按销量/价格/上新排序并分页；查看商品详情与可售库存。",
        "constraints": "仅展示上架商品；最低价不得高于最高价；分页与排序参数必须合法；无结果返回空态；下架商品详情不可访问。",
        "input": "关键词、分类 ID、最低价、最高价、排序方式、页码。",
        "process": "动态多条件查询 → 关联 category、inventory → 分页 → 计算可售状态。",
        "output": "商品列表/详情、价格、库存状态、分页信息。",
        "tables": "product、category、inventory",
    },
    {
        "id": "FR-03",
        "name": "购物车管理",
        "role": "普通用户",
        "summary": "加购、改数量、删除、勾选结算，实时计算小计与合计。",
        "desc": "加入购物车、修改数量、删除、清空、勾选结算；展示单项小计与选中合计；库存或价格变化时给出提示。",
        "constraints": "同一用户同一商品仅一条记录，重复加入累加数量；数量为 1 至库存；下架或库存不足商品不可结算；只能操作本人购物车。",
        "input": "商品 ID、数量、勾选状态、删除/清空指令。",
        "process": "校验登录、商品状态与库存 → upsert cart_item → 重算金额 → 返回购物车。",
        "output": "购物车列表、数量、小计、合计、异常提示。",
        "tables": "cart、cart_item、product、inventory",
    },
    {
        "id": "FR-04",
        "name": "订单提交与库存扣减",
        "role": "普通用户",
        "summary": "多商品下单，保存价格快照，事务内校验并扣减库存。",
        "desc": "选择收货地址与购物车商品提交订单；保存商品名称、下单单价、数量快照；计算总价；事务内校验并扣减库存，写库存流水，清理已结算购物车项。",
        "constraints": "至少选择 1 件商品；地址必须属于本人；库存不足整单失败并提示具体商品；订单、明细、库存、流水必须在同一事务；幂等令牌防止重复提交。",
        "input": "购物车项 ID 列表、地址 ID、备注、幂等令牌。",
        "process": "开启事务 → 行锁读取库存 → 校验 → 写 orders/order_item → 扣减 inventory → 写 inventory_log → 删除 cart_item → 提交。",
        "output": "订单号、总金额、待支付状态；失败原因与回滚结果。",
        "tables": "orders、order_item、cart_item、inventory、inventory_log、address",
    },
    {
        "id": "FR-05",
        "name": "订单支付与状态管理",
        "role": "普通用户 / 管理员",
        "summary": "模拟支付、取消、发货、收货，按状态机约束流转。",
        "desc": "待支付订单模拟支付并生成支付记录；用户取消未支付订单；管理员发货；用户确认收货；系统按状态机校验流转。",
        "constraints": "允许流转：待支付 → 已支付 → 已发货 → 已完成；待支付 → 已取消。支付幂等，同一订单最多一条成功支付记录；取消仅限待支付并回补库存；发货仅限已支付；非法流转拒绝。",
        "input": "订单号、支付方式、操作类型（支付/取消/发货/收货）。",
        "process": "校验状态与权限 → 写 payment → 更新 orders 及时间戳 → 取消时回补库存并写流水 → 返回最新状态。",
        "output": "支付结果、支付流水号、订单最新状态；异常提示。",
        "tables": "orders、payment、inventory、inventory_log",
    },
    {
        "id": "FR-06",
        "name": "商品与分类管理",
        "role": "管理员",
        "summary": "分类与商品的新增、编辑、上下架、软删除及多条件查询。",
        "desc": "分类新增、编辑、停用；商品新增、编辑、上下架、软删除；维护价格、图片、描述；按名称/分类/状态查询商品。",
        "constraints": "分类名称唯一；存在子分类或商品时不得删除分类；商品价格大于 0；已被订单引用的商品不物理删除，改为下架；下架商品不可购买。",
        "input": "分类/商品表单、上下架指令、查询条件。",
        "process": "校验 → 写 category/product → 初始化或联动 inventory → 返回结果。",
        "output": "分类/商品列表、操作结果、校验提示。",
        "tables": "category、product、inventory",
    },
    {
        "id": "FR-07",
        "name": "库存与预警管理",
        "role": "管理员",
        "summary": "入库、出库、盘点调整、预警阈值与库存流水查询。",
        "desc": "查看库存；入库、出库与盘点调整；设置预警阈值；查询低库存商品与库存流水；按商品和时间筛选。",
        "constraints": "调整后库存不得小于 0；调整数量不得为 0；必须填写调整原因；并发调整使用行锁；库存流水只增不改；低库存条件为 stock ≤ threshold。",
        "input": "商品 ID、调整数量、调整原因、预警阈值、查询条件。",
        "process": "锁定库存行 → 计算新库存 → 更新 inventory → 写 inventory_log → 生成预警列表。",
        "output": "最新库存、低库存清单、库存流水、操作结果。",
        "tables": "inventory、inventory_log、product",
    },
    {
        "id": "FR-08",
        "name": "订单查询与销售统计",
        "role": "普通用户 / 管理员",
        "summary": "订单多维查询，以及月度销售、Top10、分类占比等统计。",
        "desc": "用户查看本人订单列表、详情与明细；管理员按订单号、用户、状态、时间多条件查询；统计月度销售额与订单量、销量 Top10、分类销售占比、近 30 天未下单用户。",
        "constraints": "用户只能查看本人订单；销售额只统计已支付/已发货/已完成订单；时间范围合法；Top N 限制 1—50；列表分页；统计结果可下钻到明细。",
        "input": "订单号、用户、状态、时间范围、Top N。",
        "process": "多表 JOIN、GROUP BY、聚合与子查询 → 分页 → 生成图表数据。",
        "output": "订单列表/明细、月度报表、Top10、分类占比、沉默用户清单。",
        "tables": "orders、order_item、product、category、payment、users",
    },
    {
        "id": "FR-09",
        "name": "用户与地址管理",
        "role": "普通用户 / 管理员",
        "summary": "个人资料、密码、收货地址维护，以及后台用户状态管理。",
        "desc": "用户维护个人资料、修改密码、管理收货地址并设置默认地址；管理员查询用户、启用/禁用账号、查看用户订单数与累计消费。",
        "constraints": "手机号/邮箱格式合法；同一用户默认地址唯一；被未完成订单引用的地址不得删除；禁用用户不能登录和下单；用户只能操作本人数据。",
        "input": "个人资料、密码、地址表单、用户状态、查询条件。",
        "process": "校验 → 更新 users/address → 事务维护默认地址 → 聚合用户订单指标。",
        "output": "个人资料、地址列表、用户列表、订单数/消费额、操作结果。",
        "tables": "users、address、orders",
    },
]

TABLES = [
    {
        "no": "1",
        "name": "users",
        "cn": "用户表",
        "fields": "user_id、username、password_hash、phone、email、role、status、created_at",
        "purpose": "账号、角色与状态",
    },
    {
        "no": "2",
        "name": "address",
        "cn": "收货地址表",
        "fields": "address_id、user_id、receiver、phone、province、city、district、detail、is_default",
        "purpose": "用户收货地址",
    },
    {
        "no": "3",
        "name": "category",
        "cn": "商品分类表",
        "fields": "category_id、name、parent_id、sort_no、status",
        "purpose": "分类树与排序",
    },
    {
        "no": "4",
        "name": "product",
        "cn": "商品表",
        "fields": "product_id、category_id、name、price、original_price、description、image_url、status、created_at",
        "purpose": "商品主数据",
    },
    {
        "no": "5",
        "name": "inventory",
        "cn": "库存表",
        "fields": "inventory_id、product_id、stock、warning_threshold、updated_at",
        "purpose": "可售库存与预警",
    },
    {
        "no": "6",
        "name": "inventory_log",
        "cn": "库存流水表",
        "fields": "log_id、product_id、change_qty、before_stock、after_stock、change_type、order_id、operator_id、remark、created_at",
        "purpose": "库存变动审计",
    },
    {
        "no": "7",
        "name": "cart",
        "cn": "购物车表",
        "fields": "cart_id、user_id、created_at",
        "purpose": "用户唯一购物车",
    },
    {
        "no": "8",
        "name": "cart_item",
        "cn": "购物车明细表",
        "fields": "cart_item_id、cart_id、product_id、quantity、selected、added_at",
        "purpose": "购物车商品明细",
    },
    {
        "no": "9",
        "name": "orders",
        "cn": "订单表",
        "fields": "order_id、order_no、user_id、address_id、total_amount、status、remark、idempotency_key、created_at、paid_at、shipped_at、completed_at、cancelled_at",
        "purpose": "订单主表与状态时间",
    },
    {
        "no": "10",
        "name": "order_item",
        "cn": "订单明细表",
        "fields": "order_item_id、order_id、product_id、product_name、unit_price、quantity、subtotal",
        "purpose": "下单时价格快照",
    },
    {
        "no": "11",
        "name": "payment",
        "cn": "支付记录表",
        "fields": "payment_id、payment_no、order_id、user_id、amount、method、status、paid_at",
        "purpose": "支付流水与幂等",
    },
]

BUSINESS_RULES = [
    {
        "rule": "库存一致性",
        "implementation": "下单事务内使用 SELECT … FOR UPDATE 锁定库存行，校验后扣减；任一商品库存不足则整单回滚，并返回具体商品与剩余库存。",
    },
    {
        "rule": "订单状态机",
        "implementation": "仅允许 UNPAID → PAID → SHIPPED → COMPLETED 与 UNPAID → CANCELLED；其他流转返回 409，并在服务层集中校验。",
    },
    {
        "rule": "支付幂等",
        "implementation": "payment.order_id 建唯一索引；重复支付请求返回已有支付结果，不重复扣款、不重复写流水。",
    },
    {
        "rule": "价格快照",
        "implementation": "order_item 保存 product_name、unit_price、quantity、subtotal；商品调价不影响历史订单金额。",
    },
    {
        "rule": "购物车唯一",
        "implementation": "cart_item 对 (cart_id, product_id) 建唯一索引；重复加购执行数量累加而非新增行。",
    },
    {
        "rule": "删除保护",
        "implementation": "有商品或子分类的分类不可删除；被订单引用的商品改为下架；被未完成订单引用的地址不可删除。",
    },
    {
        "rule": "权限边界",
        "implementation": "JWT 携带 user_id 与 role；接口同时校验角色和资源归属，越权访问返回 403，未登录返回 401。",
    },
    {
        "rule": "重复提交",
        "implementation": "下单请求携带幂等令牌，orders.idempotency_key 建唯一索引；重复请求返回同一订单。",
    },
    {
        "rule": "并发调整库存",
        "implementation": "库存调整与下单统一使用行锁；inventory.stock 增加 CHECK (stock >= 0) 兜底，流水记录调整前后值。",
    },
]

COURSE_MAPPING = [
    {
        "requirement": "两个及以上角色与权限差异",
        "implementation": "游客、普通用户、管理员三类角色；前台/后台菜单与接口双重鉴权，用户只能访问本人数据。",
    },
    {
        "requirement": "5—10 个相互关联的核心功能",
        "implementation": "共 9 个核心功能，覆盖账号、商品、购物车、订单、支付、库存、统计、用户与地址管理。",
    },
    {
        "requirement": "数据库表不少于 5 张",
        "implementation": "规划 11 张表，含主键、外键、唯一约束、CHECK 约束与组合索引。",
    },
    {
        "requirement": "数据插入、删除、更新",
        "implementation": "注册、商品、订单、明细、支付、库存流水插入；购物车项、地址、分类删除；商品、库存、订单状态、用户状态更新。",
    },
    {
        "requirement": "多表关联查询",
        "implementation": "商品检索关联分类与库存；订单详情关联订单、明细、支付、地址；统计关联订单、明细、商品、分类、用户。",
    },
    {
        "requirement": "业务约束与异常处理",
        "implementation": "库存不足回滚、重复支付幂等、非法状态流转拒绝、重复加购合并、删除保护、越权访问拦截。",
    },
    {
        "requirement": "查询统计",
        "implementation": "月度销售额与订单量、销量 Top10、分类销售占比、近 30 天未下单用户、低库存商品。",
    },
    {
        "requirement": "索引与查询效率",
        "implementation": "订单 (user_id, created_at)、商品 (category_id, status)、明细 (order_id)、支付 (order_id)、库存 (stock) 等索引。",
    },
]

SQL_TASKS = [
    {
        "id": "SQL-01",
        "task": "查询某用户的全部订单及订单明细",
        "tables": "orders、order_item、payment、address",
        "techniques": "多表 JOIN、嵌套明细、排序",
    },
    {
        "id": "SQL-02",
        "task": "统计每月销售额和订单量",
        "tables": "orders、payment",
        "techniques": "DATE_FORMAT、GROUP BY、COUNT/SUM",
    },
    {
        "id": "SQL-03",
        "task": "查询销量最高的前 10 种商品",
        "tables": "order_item、orders、product",
        "techniques": "JOIN、SUM、ORDER BY、LIMIT",
    },
    {
        "id": "SQL-04",
        "task": "查询近 30 天没有产生订单的用户",
        "tables": "users、orders",
        "techniques": "LEFT JOIN、NOT EXISTS、日期函数",
    },
    {
        "id": "SQL-05",
        "task": "查询库存低于预警阈值的商品",
        "tables": "inventory、product",
        "techniques": "JOIN、条件比较、排序",
    },
    {
        "id": "SQL-06",
        "task": "统计各分类销售额占比",
        "tables": "category、product、order_item、orders",
        "techniques": "多表 JOIN、聚合、窗口函数",
    },
]

TECH_STACK = [
    {
        "layer": "前端",
        "stack": "Vue 3 + Vite + Element Plus + ECharts",
        "note": "前后台共用组件库，统计页使用 ECharts 展示趋势与占比。",
    },
    {
        "layer": "后端",
        "stack": "Python 3.12 + FastAPI + SQLAlchemy 2.0 + Pydantic v2",
        "note": "业务接口使用 ORM，复杂统计查询使用原生 SQL，兼顾开发效率与 SQL 可读性。",
    },
    {
        "layer": "数据库",
        "stack": "MySQL 8.0（InnoDB / utf8mb4）",
        "note": "使用事务、行锁、外键、唯一约束、CHECK 约束与组合索引。",
    },
    {
        "layer": "认证与安全",
        "stack": "JWT + bcrypt",
        "note": "密码加盐哈希；接口按角色与资源归属鉴权。",
    },
    {
        "layer": "测试与工具",
        "stack": "pytest + httpx + Postman/Apifox + MySQL Workbench",
        "note": "覆盖正常流程、库存不足、重复支付、非法状态流转等异常用例。",
    },
    {
        "layer": "部署",
        "stack": "本地运行；可选 Docker Compose",
        "note": "不引入 Redis、消息队列和微服务，保持单机可演示。",
    },
]

FLOW_STEPS = [
    "浏览/检索商品",
    "加入购物车",
    "选择地址并提交订单",
    "校验并扣减库存",
    "模拟支付",
    "管理员发货",
    "用户确认收货",
    "销售统计与复盘",
]

SCOPE_IN = [
    "商品、分类、库存、购物车、订单、订单明细、支付、地址、用户等 11 张核心表。",
    "游客浏览与检索、用户购物车与下单、模拟支付、管理员商品/库存/订单/用户管理。",
    "订单状态机、库存事务与回补、支付幂等、重复提交防护、越权拦截等关键异常处理。",
    "月度销售、销量 Top10、分类占比、沉默用户、低库存等统计查询。",
]

SCOPE_OUT = [
    "真实支付渠道（支付宝/微信）与真实退款结算，仅做模拟支付记录。",
    "真实物流轨迹、电子面单与第三方配送接口。",
    "优惠券、秒杀、拼团、会员积分、评价、推荐算法等营销功能。",
    "微服务、消息队列、Redis 缓存、移动端 App 等非数据库课程重点。",
]

PLAN = [
    {
        "phase": "第 11 周",
        "work": "确认需求与功能边界；完成 ER 图、关系模式、建表脚本、样例数据。",
        "output": "数据库设计文档、DDL、初始化数据。",
    },
    {
        "phase": "第 12 周",
        "work": "搭建后端框架与前端脚手架；完成注册登录、商品分类、商品检索、购物车。",
        "output": "可运行的前后台基础功能。",
    },
    {
        "phase": "第 13 周",
        "work": "完成下单、支付、取消、发货、收货；实现库存事务、状态机与幂等。",
        "output": "订单主链路闭环与异常用例。",
    },
    {
        "phase": "第 14 周",
        "work": "完成库存预警、用户管理、销售统计与图表；前后端联调与性能检查。",
        "output": "统计报表、联调记录、测试用例。",
    },
    {
        "phase": "第 15—16 周",
        "work": "系统演示准备、报告撰写、PPT 制作与答辩演练。",
        "output": "课程报告、演示 PPT、可演示系统。",
    },
]

DOC_SECTIONS = {
    "background": [
        "中小型电商的业务核心并不是“把商品展示出来”，而是围绕商品、购物车、订单、支付和库存形成一条可追踪、可对账的履约链路。实际教学中常见的简化系统往往只完成商品列表与下单展示，容易出现超卖、重复支付、订单状态混乱、库存与订单不一致、统计口径不统一等问题。",
        "本项目以“订单—库存一致性”为主线，设计一个规模适中、业务闭环完整的电商订单管理系统。系统不追求大而全的营销功能，而是把数据库设计、事务控制、约束与统计查询做扎实，使系统能够支撑课程要求的增删改查、多表关联、状态流转与异常处理。",
    ],
    "goals": [
        "用户端完成“浏览商品 → 加入购物车 → 提交订单 → 模拟支付 → 查询订单”的完整闭环；管理端完成“商品与分类维护 → 库存调整与预警 → 订单发货 → 用户管理 → 销售统计”的运营闭环。",
        "数据库层面形成 11 张核心表，合理设置主键、外键、唯一约束、CHECK 约束与组合索引；通过事务与行锁保证下单扣库存、取消回补库存、支付幂等的一致性。",
        "系统边界清晰、难度适中：保留电商最核心的交易与履约流程，不引入真实支付、物流、推荐算法等与数据库课程目标关联较弱的模块。",
    ],
}
