# 电商订单管理系统数据库详细设计

编写日期：2026年11月13日。本文供第20组编码前核对表结构、接口和事务使用，不改写现有课程报告。设计依据为教师大作业原件、`scripts/data.py`、当前课程报告DOCX及`docs/02-course-report.md`的2.3至2.5节；功能编号和业务含义沿用FR-01至FR-09。

本文确定使用九张表、单字段可售库存、仅用户手动取消待支付订单、用户维度的结算幂等，以及MySQL行锁配合库存版本号。下面的DDL是设计文档的一部分；业务代码、实际部署库和课程报告排版均不在本次交付中。

## 1 设计决策

### 1.1 库存采用单字段可售量和盘点差额调整

选择`inventory.available`单字段，不增加`on_hand`、`reserved`。它表示现在还能接受新订单的数量，下单时即扣减，待支付和已支付未发货商品均已从可售量中扣除。这样与报告2.2.1、2.3.3、2.4.2以及`data.py`现行口径一致；课程规模不引入实物仓储、预占转实扣和库存流水的另一套账。

| 操作 | available变化 | 规则 |
| --- | --- | --- |
| 加购、修改购物车 | 不变 | 只检查当时上架状态和可售量，不保证随后仍有库存 |
| 下单q件 | 减q | q为正INT；所有商品一次事务，库存不足整单撤销 |
| 用户取消待支付订单q件 | 加q | 数量取订单明细，首次成功取消执行一次 |
| 模拟支付成功或失败 | 不变 | 成功只保存支付并推进订单；失败仍待支付 |
| 管理员发货、用户收货 | 不变 | 下单已经扣减，不得二次扣减 |
| 管理员补货q件 | 加q | q大于0，按锁定后的最新库存计算 |
| 管理员盘点 | 加delta | 输入`counted_available`是确认后的可售量；在版本一致时计算delta = counted_available - 当前available，再应用差额 |

盘点输入**是可售量，不是实物总量**。例如初始可售10件，下单3件后可售7件、待支付占用3件；实物仍为10件时，不能填10，否则错误多放出3件。若核实可售品损坏1件，应在最新页面填6，delta为-1；随后原订单取消，可售恢复为9。已支付未发货的分配量也不能作为盘点中的可售量。

管理员库存列表返回`available`、`version`、`updated_at`和派生的`pending_occupied`。后者按该商品的`order_item.quantity`求和，限定订单`status='PENDING'`；只读展示为“待支付订单占用”，不存第二个库存字段。列表使用一条查询同时关联按商品预聚合的占用量，避免N+1查询和多个读取时刻的混合；无占用用0。普通用户看可售量和本人待支付订单，不公开其他用户的订单信息。此占用量与available相加也不能被标为完整实物库存，因为还可能存在已支付未发货分配、损耗等。

补货和盘点必须提交页面读取的`expected_version`。锁定库存后若版本不同，返回409 `INVENTORY_VERSION_CONFLICT`及最新库存，管理员刷新并重新确认；禁止把旧盘点目标直接覆盖到新值，禁止冲突后自动替用户确认。所有成功库存写入均`version = version + 1`并设置更新时间，包括确认delta=0的盘点。下单与取消不用页面版本，使用事务内读到的版本进行条件更新。

### 1.2 待支付订单只由所属用户手动取消

不做30分钟惰性过期，不做管理员兜底取消，不设置`expires_at`、`EXPIRED`状态、定时任务或读请求隐式取消。只能订单所属普通用户手动取消，管理员无代取消权限，与报告2.4.2一致。待支付列表明确显示“持续占用库存，请支付或手动取消”；未操作时持续保留占用，可在任意后续时刻支付。

待支付和已取消订单不计销售额、已支付订单量及商品销量；两者仍参加“近30天是否下过单”的判断，因为订单曾成功创建。取消保留订单、明细和结算标识，不自动恢复购物车。

### 1.3 订单号和结算幂等

`orders.id`为`BIGINT UNSIGNED AUTO_INCREMENT`主键，也就是报告中的订单编号和对外订单号，不另建`order_no`。支付编号同理为`payment.id`。HTTP/JSON中所有BIGINT标识和库存版本以十进制字符串传输，避免JavaScript整数精度损失；不依赖编号连续或无间隙，回滚可消耗自增号。

| 项目 | 确定规则 |
| --- | --- |
| checkout_token生成方 | 普通用户前端在一次结算确认开始时用`crypto.getRandomValues`生成16个随机字节，编码为32个小写十六进制字符，共128位随机值 |
| 请求和存储 | `POST /orders`必填；服务端校验`^[0-9a-f]{32}$`；存`CHAR(32)`，按二进制排序规则比较，不能用时间戳或商品ID代替随机值 |
| 唯一性 | `UNIQUE(user_id, checkout_token)`，同用户同token最多一个订单；不同用户空间独立 |
| 请求摘要 | 服务端对规范化的用户ID、条目ID及预期数量、收货人、电话、地址计算SHA-256，存64位小写十六进制`checkout_request_hash`；不含token、商品现价和服务端生成时间 |
| 相同token相同摘要 | 返回原订单、明细和最新可读取状态；不重新读购物车建单、不重新核价扣库存。即使已支付、完成或取消也返回原订单 |
| 相同token不同摘要 | 返回409 `CHECKOUT_TOKEN_CONFLICT`；不能覆盖旧订单、不能替换收货信息 |
| 明确回滚后的重试 | 没有订单提交即没有已消费的token；原载荷可用同token重试，重新检查商品现价、库存和购物车。用户修改载荷后前端生成新token |
| 断网或提交结果未知 | 保留原token和载荷重发；先按唯一键找原订单。不能立即生成新token重下单 |
| 取消后的复用 | token永久绑定已取消原订单，不能复活或再建单；用户重新加购并确认新结算，生成新token |
| 生命周期 | 前端持久保存当前未获明确结果的token与载荷到本次浏览器会话存储；成功后在订单详情保留结果；服务端不清理订单token，无单独token表 |

规范化由服务端统一完成：用户ID及条目ID转为无前导零十进制字符串，数量为JSON整数；所有文本去除首尾空白，Unicode统一NFC，内部空白保留；条目ID去重校验后按数字升序排列。用于散列的JSON键按固定次序`user_id, items, receiver_name, receiver_phone, receiver_address`输出；每个item键依次`cart_item_id, quantity`，UTF-8编码、不转义非ASCII字符、无额外空格。前端不自行计算可信摘要。重复条目、未知字段、格式非法或空收货信息先拒绝，金额不从客户端接受。

相同用户的购物车父行充当结算互斥锁。获取该锁后再次查询token，先处理已存在的订单，再检查购物车；因此第一笔成功清空已结算条目后，第二笔同token请求仍能返回原单。重放结果用同一条SELECT关联订单、明细和支付取得一致的语句快照，避免READ COMMITTED下分次读到“旧待支付状态加新支付记录”。唯一索引是数据库的最后保护；遇该索引1062时整个事务回滚，再按`user_id + token`查询并比对摘要，不把其他唯一键冲突误当成功。

## 2 数据类型和完整性分工

数据库为MySQL 8.0.16及以上版本，推荐8.0.40；8.0.16起CHECK才实际执行。全部表使用InnoDB、utf8mb4，默认排序规则`utf8mb4_0900_ai_ci`；token、摘要、角色和状态单列使用`utf8mb4_bin`作精确比较。用户名只接受3至32位小写ASCII字母、数字和下划线，注册和登录统一去首尾空格并转小写；分类名去首尾空格后按默认排序规则唯一，不设置父分类。

金额、单价使用`DECIMAL(10,2)`，取值0.01至99,999,999.99元；不用浮点数。数量一律有符号`INT`，购买量大于0，available不小于0，上限2,147,483,647。合计用Decimal或更宽的数据库精确类型计算，确认总额不超DECIMAL范围再写入；补货、回补也先检查INT上界，超界整笔回滚并返回`QUANTITY_OVERFLOW`，不能截断或丢弃回补量。此时管理员先按实际可售口径核对并修正库存，再由用户重试取消。

所有时间列为`DATETIME`，秒级精度，保存Asia/Shanghai本地墙钟时间，不隐式保存UTC。数据库连接统一`SET time_zone='+08:00'`（无需安装命名时区表），应用配置使用`Asia/Shanghai`；API输出带`+08:00`的ISO 8601时间，带其他偏移的输入先转为该时区再去偏移绑定。一次状态变更从数据库取一次`NOW()`，必要时与前置事件时间取较大值，防止时钟回拨造成时间倒序。同秒的连续事件允许相等。

DDL负责行内合法值、非空、主外键、唯一性和状态时间组合。普通用户恰有一个购物车、每商品恰有库存、订单至少一条明细、总额等于明细和、支付金额及时间与订单相等、跨表角色范围和合法的前后状态迁移，均由下文同一事务负责；MySQL CHECK不能查询其他表，不宣称DDL独自保证这些条件。不增加触发器、存储过程或第十张业务表。业务写入只能经统一事务入口，不能把数据库直连改表当接口。

## 3 九张表字段字典

“必填”表示NOT NULL且无业务默认值；`AI`表示自动增长；`NOW`表示`CURRENT_TIMESTAMP`。未列入可空列的字段均NOT NULL。外键、索引及完整CHECK以第4节DDL为准。

### 3.1 users 用户

| 字段 | 类型 | 可空 | 默认 | 含义与约束 |
| --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | 否 | AI | 用户编号，PK |
| username | VARCHAR(32) | 否 | 必填 | 用户名，UNIQUE；规范化后3至32位 |
| password_hash | VARCHAR(255) | 否 | 必填 | 带盐密码哈希编码，采用Argon2id，不保存明文 |
| role | VARCHAR(10) | 否 | USER | USER普通用户、ADMIN管理员；注册强制USER |
| nickname | VARCHAR(50) | 否 | 必填 | 昵称，非空白 |
| phone | VARCHAR(20) | 否 | 必填 | 联系电话，文本保留前导零和区号 |
| created_at | DATETIME | 否 | NOW | 创建时间 |
| updated_at | DATETIME | 否 | NOW并自动更新 | 最近资料变更 |

### 3.2 category 商品分类

| 字段 | 类型 | 可空 | 默认 | 含义与约束 |
| --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | 否 | AI | 分类编号，PK |
| name | VARCHAR(50) | 否 | 必填 | 单层分类名称，UNIQUE，非空白 |
| created_at | DATETIME | 否 | NOW | 创建时间 |
| updated_at | DATETIME | 否 | NOW并自动更新 | 更新时间 |

### 3.3 product 商品

| 字段 | 类型 | 可空 | 默认 | 含义与约束 |
| --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | 否 | AI | 商品编号，PK |
| category_id | BIGINT UNSIGNED | 否 | 必填 | FK到category.id |
| name | VARCHAR(100) | 否 | 必填 | 商品名称，不作唯一标识 |
| price | DECIMAL(10,2) | 否 | 必填 | 当前售价，大于0 |
| description | TEXT | 否 | 必填 | 商品介绍，允许空字符串，不允许NULL |
| status | VARCHAR(10) | 否 | OFF_SHELF | ON_SHELF上架、OFF_SHELF下架 |
| created_at | DATETIME | 否 | NOW | 创建时间 |
| updated_at | DATETIME | 否 | NOW并自动更新 | 最近资料变更 |

### 3.4 cart 购物车

| 字段 | 类型 | 可空 | 默认 | 含义与约束 |
| --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | 否 | AI | 购物车编号，PK |
| user_id | BIGINT UNSIGNED | 否 | 必填 | FK到users.id，UNIQUE；必须属于USER |
| created_at | DATETIME | 否 | NOW | 注册事务内创建，管理员无此记录 |

### 3.5 cart_item 购物车明细

| 字段 | 类型 | 可空 | 默认 | 含义与约束 |
| --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | 否 | AI | 条目编号，PK |
| cart_id | BIGINT UNSIGNED | 否 | 必填 | FK到cart.id |
| product_id | BIGINT UNSIGNED | 否 | 必填 | FK到product.id；同车同商品UNIQUE |
| quantity | INT | 否 | 1 | 购买数量，大于0 |
| selected | TINYINT | 否 | 1 | 0未勾选、1勾选 |
| created_at | DATETIME | 否 | NOW | 首次加入时间；合并数量不重置 |
| updated_at | DATETIME | 否 | NOW并自动更新 | 最近修改时间 |

### 3.6 orders 订单

| 字段 | 类型 | 可空 | 默认 | 含义与约束 |
| --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | 否 | AI | PK兼对外订单号 |
| user_id | BIGINT UNSIGNED | 否 | 必填 | FK到users.id，所属USER |
| checkout_token | CHAR(32) | 否 | 必填 | 结算标识；与user_id组成UNIQUE |
| checkout_request_hash | CHAR(64) | 否 | 必填 | 原始结算业务载荷摘要，防止同token异参 |
| total_amount | DECIMAL(10,2) | 否 | 必填 | 应付金额，大于0且等于明细合计 |
| status | VARCHAR(12) | 否 | PENDING | PENDING、PAID、SHIPPED、COMPLETED、CANCELLED |
| receiver_name | VARCHAR(50) | 否 | 必填 | 收货人快照，非空白 |
| receiver_phone | VARCHAR(20) | 否 | 必填 | 收货电话快照，非空白 |
| receiver_address | VARCHAR(255) | 否 | 必填 | 收货地址快照，非空白 |
| created_at | DATETIME | 否 | NOW | 下单时间 |
| paid_at | DATETIME | 是 | NULL | 成功支付时间，与payment.paid_at相等 |
| shipped_at | DATETIME | 是 | NULL | 发货时间 |
| completed_at | DATETIME | 是 | NULL | 完成时间 |
| cancelled_at | DATETIME | 是 | NULL | 取消时间 |
| updated_at | DATETIME | 否 | NOW并自动更新 | 最近状态更新时间 |

### 3.7 order_item 订单明细

| 字段 | 类型 | 可空 | 默认 | 含义与约束 |
| --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | 否 | AI | 明细编号，PK |
| order_id | BIGINT UNSIGNED | 否 | 必填 | FK到orders.id |
| product_id | BIGINT UNSIGNED | 否 | 必填 | FK到product.id；同单同商品UNIQUE |
| product_name | VARCHAR(100) | 否 | 必填 | 商品名称成交快照，不随商品改名 |
| unit_price | DECIMAL(10,2) | 否 | 必填 | 下单时单价快照，大于0 |
| quantity | INT | 否 | 必填 | 购买数量，大于0 |

行金额为`unit_price * quantity`，查询时计算，不增加冗余可写字段。订单成立后明细、收货快照、总额、user_id及token摘要不可修改。

### 3.8 inventory 库存

| 字段 | 类型 | 可空 | 默认 | 含义与约束 |
| --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | 否 | AI | 库存编号，PK，保留报告正式属性 |
| product_id | BIGINT UNSIGNED | 否 | 必填 | FK到product.id，UNIQUE，每商品一份 |
| available | INT | 否 | 0 | 当前可售数量，非负 |
| version | BIGINT UNSIGNED | 否 | 0 | 库存乐观锁版本，库存写入递增 |
| updated_at | DATETIME | 否 | NOW并自动更新 | 最近库存操作时间，写入时显式设置 |

### 3.9 payment 成功支付记录

| 字段 | 类型 | 可空 | 默认 | 含义与约束 |
| --- | --- | --- | --- | --- |
| id | BIGINT UNSIGNED | 否 | AI | 支付编号，PK |
| order_id | BIGINT UNSIGNED | 否 | 必填 | FK到orders.id，UNIQUE |
| amount | DECIMAL(10,2) | 否 | 必填 | 支付金额，取订单总额且大于0 |
| paid_at | DATETIME | 否 | 必填 | 成功支付时间，与订单共同写入 |

只存成功事实，失败不插入payment；不需要可与事实矛盾的支付状态列。

## 4 MySQL 8.0 DDL

下列完整代码块可直接在MySQL 8.0.16及以上的**空数据库**执行。数据库名为`scu_ecommerce`；不包含DROP，不负责迁移或覆盖已有表。`SET SESSION`必须在每个应用连接建立时同样执行，不能只在建库时设置。

```sql
CREATE DATABASE IF NOT EXISTS scu_ecommerce
  CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE scu_ecommerce;
SET NAMES utf8mb4 COLLATE utf8mb4_0900_ai_ci;
SET SESSION time_zone = '+08:00';
SET SESSION transaction_isolation = 'READ-COMMITTED';
SET SESSION sql_mode = 'STRICT_TRANS_TABLES,ONLY_FULL_GROUP_BY,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

CREATE TABLE users (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  username VARCHAR(32) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(10) COLLATE utf8mb4_bin NOT NULL DEFAULT 'USER',
  nickname VARCHAR(50) NOT NULL,
  phone VARCHAR(20) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_users_username (username),
  KEY idx_users_role_created (role, created_at, id),
  CONSTRAINT ck_users_username CHECK (CHAR_LENGTH(TRIM(username)) BETWEEN 3 AND 32),
  CONSTRAINT ck_users_password CHECK (CHAR_LENGTH(TRIM(password_hash)) > 0),
  CONSTRAINT ck_users_role CHECK (role IN ('USER', 'ADMIN')),
  CONSTRAINT ck_users_nickname CHECK (CHAR_LENGTH(TRIM(nickname)) > 0),
  CONSTRAINT ck_users_phone CHECK (CHAR_LENGTH(TRIM(phone)) > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE category (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  name VARCHAR(50) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_category_name (name),
  CONSTRAINT ck_category_name CHECK (CHAR_LENGTH(TRIM(name)) > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE product (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  category_id BIGINT UNSIGNED NOT NULL,
  name VARCHAR(100) NOT NULL,
  price DECIMAL(10,2) NOT NULL,
  description TEXT NOT NULL,
  status VARCHAR(10) COLLATE utf8mb4_bin NOT NULL DEFAULT 'OFF_SHELF',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_product_category_status_price (category_id, status, price, id),
  KEY idx_product_status_price (status, price, id),
  CONSTRAINT fk_product_category FOREIGN KEY (category_id) REFERENCES category (id)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT ck_product_name CHECK (CHAR_LENGTH(TRIM(name)) > 0),
  CONSTRAINT ck_product_price CHECK (price > 0),
  CONSTRAINT ck_product_status CHECK (status IN ('ON_SHELF', 'OFF_SHELF'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE cart (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id BIGINT UNSIGNED NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_cart_user (user_id),
  CONSTRAINT fk_cart_user FOREIGN KEY (user_id) REFERENCES users (id)
    ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE cart_item (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  cart_id BIGINT UNSIGNED NOT NULL,
  product_id BIGINT UNSIGNED NOT NULL,
  quantity INT NOT NULL DEFAULT 1,
  selected TINYINT NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_cart_item_product (cart_id, product_id),
  KEY idx_cart_item_product (product_id),
  CONSTRAINT fk_cart_item_cart FOREIGN KEY (cart_id) REFERENCES cart (id)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_cart_item_product FOREIGN KEY (product_id) REFERENCES product (id)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT ck_cart_item_quantity CHECK (quantity > 0),
  CONSTRAINT ck_cart_item_selected CHECK (selected IN (0, 1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE orders (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id BIGINT UNSIGNED NOT NULL,
  checkout_token CHAR(32) COLLATE utf8mb4_bin NOT NULL,
  checkout_request_hash CHAR(64) COLLATE utf8mb4_bin NOT NULL,
  total_amount DECIMAL(10,2) NOT NULL,
  status VARCHAR(12) COLLATE utf8mb4_bin NOT NULL DEFAULT 'PENDING',
  receiver_name VARCHAR(50) NOT NULL,
  receiver_phone VARCHAR(20) NOT NULL,
  receiver_address VARCHAR(255) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  paid_at DATETIME NULL DEFAULT NULL,
  shipped_at DATETIME NULL DEFAULT NULL,
  completed_at DATETIME NULL DEFAULT NULL,
  cancelled_at DATETIME NULL DEFAULT NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_orders_user_token (user_id, checkout_token),
  KEY idx_orders_user_created (user_id, created_at, id),
  KEY idx_orders_status_created (status, created_at, id),
  KEY idx_orders_created (created_at, id),
  CONSTRAINT fk_orders_user FOREIGN KEY (user_id) REFERENCES users (id)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT ck_orders_token CHECK (CHAR_LENGTH(checkout_token) = 32),
  CONSTRAINT ck_orders_hash CHECK (CHAR_LENGTH(checkout_request_hash) = 64),
  CONSTRAINT ck_orders_total CHECK (total_amount > 0),
  CONSTRAINT ck_orders_receiver CHECK (
    CHAR_LENGTH(TRIM(receiver_name)) > 0 AND
    CHAR_LENGTH(TRIM(receiver_phone)) > 0 AND
    CHAR_LENGTH(TRIM(receiver_address)) > 0
  ),
  CONSTRAINT ck_orders_status_times CHECK (
    (status = 'PENDING' AND paid_at IS NULL AND shipped_at IS NULL
      AND completed_at IS NULL AND cancelled_at IS NULL)
    OR (status = 'PAID' AND paid_at IS NOT NULL AND shipped_at IS NULL
      AND completed_at IS NULL AND cancelled_at IS NULL)
    OR (status = 'SHIPPED' AND paid_at IS NOT NULL AND shipped_at IS NOT NULL
      AND completed_at IS NULL AND cancelled_at IS NULL)
    OR (status = 'COMPLETED' AND paid_at IS NOT NULL AND shipped_at IS NOT NULL
      AND completed_at IS NOT NULL AND cancelled_at IS NULL)
    OR (status = 'CANCELLED' AND paid_at IS NULL AND shipped_at IS NULL
      AND completed_at IS NULL AND cancelled_at IS NOT NULL)
  ),
  CONSTRAINT ck_orders_time_sequence CHECK (
    (paid_at IS NULL OR paid_at >= created_at) AND
    (shipped_at IS NULL OR shipped_at >= paid_at) AND
    (completed_at IS NULL OR completed_at >= shipped_at) AND
    (cancelled_at IS NULL OR cancelled_at >= created_at)
  )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE order_item (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  order_id BIGINT UNSIGNED NOT NULL,
  product_id BIGINT UNSIGNED NOT NULL,
  product_name VARCHAR(100) NOT NULL,
  unit_price DECIMAL(10,2) NOT NULL,
  quantity INT NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_order_item_product (order_id, product_id),
  KEY idx_order_item_product_order (product_id, order_id),
  CONSTRAINT fk_order_item_order FOREIGN KEY (order_id) REFERENCES orders (id)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_order_item_product FOREIGN KEY (product_id) REFERENCES product (id)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT ck_order_item_name CHECK (CHAR_LENGTH(TRIM(product_name)) > 0),
  CONSTRAINT ck_order_item_price CHECK (unit_price > 0),
  CONSTRAINT ck_order_item_quantity CHECK (quantity > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE inventory (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  product_id BIGINT UNSIGNED NOT NULL,
  available INT NOT NULL DEFAULT 0,
  version BIGINT UNSIGNED NOT NULL DEFAULT 0,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_inventory_product (product_id),
  CONSTRAINT fk_inventory_product FOREIGN KEY (product_id) REFERENCES product (id)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT ck_inventory_available CHECK (available >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE payment (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  order_id BIGINT UNSIGNED NOT NULL,
  amount DECIMAL(10,2) NOT NULL,
  paid_at DATETIME NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_payment_order (order_id),
  KEY idx_payment_paid_order (paid_at, order_id),
  CONSTRAINT fk_payment_order FOREIGN KEY (order_id) REFERENCES orders (id)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT ck_payment_amount CHECK (amount > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
```

### 4.1 索引使用与删除策略

商品分类状态价格联合索引支持组合筛选，无分类时用状态价格索引；商品名称采用参数化`LIKE '%关键词%'`，课程数据量下接受扫描，不宣称普通B树可加速前置百分号检索。订单查询按用户和下单时间、按状态和下单时间、或全局下单时间定位。`payment(paid_at, order_id)`服务支付期间统计，`orders(user_id, created_at, id)`服务用户订单和反连接查询。明细唯一索引既约束粒度又支持按订单取明细；商品外键均有以商品编号开头的索引。其余主键及唯一索引提供精确查找，不为每列单独建索引。

| 对象 | 删除策略 |
| --- | --- |
| users、cart | 本轮不提供账号或购物车容器删除接口，不允许改角色；注册USER与空cart同一事务提交 |
| category | 有商品引用即RESTRICT；只有空分类可以删除 |
| product、inventory | 商品有任何当前购物车明细或历史订单明细引用则拒绝物理删除，只下架；无引用且available=0时，在事务中先删库存再删商品 |
| cart_item | 用户可删除本人条目；结算仅删除本次条目，不级联删容器 |
| orders、order_item、payment | 保留历史，不提供普通物理删除；取消只改状态；全部FK RESTRICT防止误删 |

全部外键`ON UPDATE RESTRICT`，主键创建后不可改。商品删除先锁商品、再锁库存并检查零量和引用，不通过则整笔回滚；FK再兜底并发引用。不能用CASCADE隐藏删除历史，不能临时关闭`FOREIGN_KEY_CHECKS`绕过限制。

### 4.2 报告2.3属性覆盖

| 报告属性组 | 本设计字段 |
| --- | --- |
| 用户编号、用户名、密码哈希、角色、昵称、联系电话 | users.id、username、password_hash、role、nickname、phone |
| 分类编号、分类名称 | category.id、name |
| 商品编号、名称、当前售价、上架状态、介绍、创建时间 | product.id、name、price、status、description、created_at |
| 购物车编号、创建时间 | cart.id、created_at；user_id实现普通用户拥有联系 |
| 条目编号、购买数量、勾选状态、加入时间 | cart_item.id、quantity、selected、created_at；cart_id和product_id实现联系 |
| 库存编号、可售数量、更新时间 | inventory.id、available、updated_at；product_id实现一对一联系 |
| 订单编号、应付金额、状态、创建时间、收货人、电话、地址、结算标识、支付/发货/完成/取消时间 | orders.id、total_amount、status、created_at、receiver_name、receiver_phone、receiver_address、checkout_token、paid_at、shipped_at、completed_at、cancelled_at |
| 明细编号、名称快照、下单单价、数量 | order_item.id、product_name、unit_price、quantity；order_id和product_id实现联系 |
| 支付编号、金额、时间 | payment.id、amount、paid_at；order_id实现订单联系 |

库存version、结算摘要、若干更新时间为实现既定一致性规则增加的技术字段，不替换概念属性，不另增实体。

## 5 并发控制

### 5.1 隔离级别和加锁顺序

采用InnoDB `READ COMMITTED`。业务判断所依赖的订单、商品和库存通过锁定读取得最新值；不依赖普通快照读抵御超卖。一次事务只处理一个购物车或一个现有订单，禁止任意批量混锁。

| 路径 | 固定顺序 |
| --- | --- |
| 新结算、购物车写入 | 先按user_id锁cart父行；再读取/锁本车条目；需要商品校验时按product.id升序逐行锁商品，再按product_id升序逐行锁库存；结算最后插入新orders和order_item，不锁其他已有订单 |
| 取消 | 按主键锁已有orders，检查归属及状态；按product_id升序锁inventory并回补；不再锁cart或product |
| 支付、发货、确认收货 | 按主键锁已有orders；支付再访问该单payment；不锁购物车、商品或库存 |
| 商品编辑或删除、库存补货/盘点 | 先锁product，再锁对应inventory；不反向锁已有订单或购物车；分类存在性通过FK及必要的分类锁保证 |

锁库存使用`SELECT ... FROM inventory WHERE product_id = ? FOR UPDATE`，订单使用`SELECT ... FROM orders WHERE id = ? FOR UPDATE`。多商品先在内存按编号排序，再逐个主键/唯一键点查，不能只依赖`WHERE product_id IN (...)`的偶然执行顺序。所有库存写入路径遵循该顺序；有锁以后也保留版本条件。

同用户购物车的增加、合并、勾选、改量、删除也先锁cart父行；与结算串行，防止结算后误删期间新增或改量的条目。商品行锁保证下单取价、名称快照和上架状态不会在提交前被管理员改变。分类编辑/删除不再反向锁购物车、订单或库存，外键冲突回滚处理。

### 5.2 version与行锁的分工

事务先锁行保证当前检查和更新之间无人插入修改；版本号用于识别管理员旧页面并保证所有库存更新经过同一路径。下单的条件更新形状如下，`q`和`old_version`均取自已校验值：

```sql
UPDATE inventory
SET available = available - ?, version = version + 1, updated_at = NOW()
WHERE product_id = ? AND version = ? AND available >= ?;
```

绑定顺序为`q, product_id, old_version, q`。受影响行数必须为1，否则整单回滚。取消用`available = available + q`并检查上界；补货同样做加法；盘点在版本相等时计算delta后用`available = available + delta`。每个写入都携带`WHERE version=old_version`，不得无条件覆盖。

### 5.3 死锁与重试

固定顺序减少死锁，不能消除InnoDB外键、唯一键检查带来的所有等待。MySQL 1213死锁、1205锁等待超时均显式回滚**整个事务**，释放全部锁后重读并重试；最多3次总尝试，重试前分别等待约50ms、150ms并加入0至50ms随机抖动。不在持锁期间等待，不只重跑失败SQL。

结算自动重试沿用同token、同载荷；取消、支付沿用同订单。管理员维护重试仍携带原expected_version，若已变化就转409供人工刷新，不悄悄采纳新版本。库存不足、非法状态、版本冲突、金额超界、格式错误不自动重试。三次仍失败返回503 `TRANSACTION_RETRY_EXHAUSTED`，不泄露SQL细节。连接在COMMIT时断开属于结果未知，必须新连接先核对token或订单/支付状态后再决定重试，不能假设未提交。

## 6 状态与时间戳

| 状态 | paid_at | shipped_at | completed_at | cancelled_at | payment行 |
| --- | --- | --- | --- | --- | --- |
| PENDING 待支付 | NULL | NULL | NULL | NULL | 无 |
| PAID 已支付 | 非NULL | NULL | NULL | NULL | 恰1条 |
| SHIPPED 已发货 | 非NULL | 非NULL | NULL | NULL | 恰1条 |
| COMPLETED 已完成 | 非NULL | 非NULL | 非NULL | NULL | 恰1条 |
| CANCELLED 已取消 | NULL | NULL | NULL | 非NULL | 无 |

唯一允许的首次迁移是`PENDING → PAID → SHIPPED → COMPLETED`以及`PENDING → CANCELLED`。模拟失败为`PENDING → PENDING`，不写时间和payment。每次迁移在一条UPDATE中同时写状态和本次时间，不能先改状态再另一个事务补时间。`created_at ≤ paid_at ≤ shipped_at ≤ completed_at`，取消时间不早于创建时间；未发生事件为NULL，不能写零日期。既有事件时间不可覆盖。

成功支付要求`payment.amount = orders.total_amount`、`payment.paid_at = orders.paid_at`，且payment唯一对应该单。下单时间、收货信息、成交明细及总额建立后不可修改。DDL只校验当前行形状，历史迁移、至少一条明细和跨表等式还需事务保证。

重复取消返回已取消状态，不再次加库存；取消已支付或后续状态返回409。重复模拟支付对PAID、SHIPPED、COMPLETED只返回原成功记录（即使此次传simulate_result=FAILURE，也不推翻已成功事实），不再次支付；CANCELLED拒绝。重复发货对SHIPPED或COMPLETED返回当前状态而不重写shipped_at；重复收货对COMPLETED返回原结果。用户仍须通过角色及归属校验，重复请求也不能绕过鉴权。

## 7 三个核心事务伪代码

下列BEGIN到COMMIT在一个数据库连接内执行，异常统一ROLLBACK。身份来自登录上下文，客户端user_id不决定归属。响应成功均在COMMIT确认后发送。所有辅助写入也适用第5节重试规则。

### 7.1 提交订单

```text
checkout(current_user, token, items[id, expected_quantity], receiver):
  要求current_user.role=USER；规范化并校验token、载荷；计算request_hash
  BEGIN (READ COMMITTED)
  cart = SELECT cart WHERE user_id=current_user.id FOR UPDATE
  若cart不存在：视为初始化完整性错误，回滚，不能临时拼出无主购物车
  old_result = 一条SELECT读取orders及LEFT JOIN的order_item、payment
    WHERE orders.user_id=current_user.id AND checkout_token=token
  若存在：
    摘要不同则ROLLBACK，409 CHECKOUT_TOKEN_CONFLICT
    检查明细非空及状态/支付一致；结束事务，返回200及同一语句快照中的原单
    不再校验已清理的购物车，不分次重新读取支付拼接旧订单头
  锁定并读取本车条目；要求请求集合恰为当前全部勾选条目，且至少1项
  核对每条id属于本车、selected=1、quantity等于expected_quantity
  不一致则ROLLBACK，409 CART_CHANGED；重复id或非正数量返回422
  按product_id升序逐个SELECT product FOR UPDATE
  再按相同顺序逐个SELECT inventory WHERE product_id=? FOR UPDATE
  检查商品全部上架、库存记录齐全、available>=购买数
  使用数据库现价及名称构建快照，Decimal求和，验证总额范围
  now = 数据库NOW()
  INSERT orders(user_id, token, request_hash, total_amount, PENDING, receiver, created_at=now)
  取得自增id，作为对外订单号
  对每个商品：
    INSERT order_item(order_id, product_id, product_name快照, unit_price快照, quantity)
    UPDATE inventory SET available=available-q, version=version+1, updated_at=now
      WHERE product_id=? AND version=本次读取版本 AND available>=q
    要求affected_rows=1，否则抛错并整单ROLLBACK
  再核对本单至少1条明细且SUM(unit_price*quantity)=orders.total_amount
  DELETE本车本次已结算条目，未勾选条目保留；核对删除数量
  COMMIT；返回201（新订单、明细、应付金额、PENDING）
  任意失败：ROLLBACK；订单、token、明细、扣库、购物车清理一并撤销
  若uk_orders_user_token出现1062：ROLLBACK后新事务查询原单并比较摘要
```

同token返回原单的分支不再申请已有订单的排他锁；第一个结算提交已持久化完整订单，后续取消/支付可以独立推进状态。返回状态表示本次读取时状态。其他非token唯一冲突、引用缺失和金额不一致均报错回滚，不伪装成重复成功。

### 7.2 取消订单

```text
cancel(current_user, order_id):
  要求current_user.role=USER
  BEGIN
  order = SELECT orders WHERE id=order_id FOR UPDATE
  不存在或不属于current_user：ROLLBACK，404 ORDER_NOT_FOUND
  若CANCELLED：结束事务，返回200及原结果，不操作库存
  若非PENDING：ROLLBACK，409 ORDER_STATE_CONFLICT
  读取不可变的order_item，要求非空
  按product_id升序逐个锁inventory，核对存在及available+quantity不超INT上界
  now = GREATEST(数据库NOW(), order.created_at)
  对每项按读取版本UPDATE inventory：available加原数量、version加1、updated_at=now
  每项要求affected_rows=1
  UPDATE orders SET status=CANCELLED, cancelled_at=now, updated_at=now
    WHERE id=order_id AND status=PENDING
  要求affected_rows=1，且本单无payment
  COMMIT；返回200及CANCELLED；不恢复购物车条目
  任意失败：ROLLBACK，订单仍PENDING、所有库存均不变
```

### 7.3 模拟支付

```text
pay(current_user, order_id, simulate_result):
  要求current_user.role=USER，simulate_result只允许SUCCESS或FAILURE
  BEGIN
  order = SELECT orders WHERE id=order_id FOR UPDATE
  不存在或不属于current_user：ROLLBACK，404 ORDER_NOT_FOUND
  若PAID/SHIPPED/COMPLETED：
    读取唯一payment并核对金额及时间一致，结束事务，返回200及原成功记录
  若CANCELLED：ROLLBACK，409 ORDER_STATE_CONFLICT
  要求PENDING且无payment，否则ROLLBACK并报完整性错误
  若simulate_result=FAILURE：结束事务，返回200 result=FAILURE，订单仍PENDING
  amount = order.total_amount（不接受客户端金额）
  now = GREATEST(数据库NOW(), order.created_at)
  INSERT payment(order_id, amount, paid_at=now)
  UPDATE orders SET status=PAID, paid_at=now, updated_at=now
    WHERE id=order_id AND status=PENDING
  要求affected_rows=1且支付等式成立
  COMMIT；返回201 result=SUCCESS、原订单及支付id/金额/时间
  任意失败：ROLLBACK，不能只留下payment或只留下PAID状态
```

支付和取消争用同一订单行锁，先提交者决定后续分支。支付成功后取消失败，取消成功后支付失败。唯一支付索引是额外保护；若payment唯一冲突且订单仍为PENDING，属于数据不一致，不能仅捕获1062并报支付成功。

发货与收货沿用同一订单锁；管理员仅PAID时设置SHIPPED及`shipped_at=max(NOW(), paid_at)`，所属用户仅SHIPPED时设置COMPLETED及`completed_at=max(NOW(), shipped_at)`；均不改库存，不调用模拟支付。

## 8 四条查询SQL

以下每个代码块可在DDL创建的库中执行，示例用MySQL会话变量设置参数；实际接口使用驱动绑定参数。时间均为Asia/Shanghai，统一`[start_at, end_at)`；校验起点小于终点。普通用户的user_id由身份注入，不能直接相信URL参数。四条查询均与报告2.5一致。

### 8.1 Q1 用户订单及明细

按下单时间筛选，包括待支付、已取消和已支付后续状态。输出粒度为一条订单明细，订单头和支付列会在多明细行重复显示，但不在这个结果上累计销售金额。使用LEFT JOIN支付保留无支付订单。普通用户强制本人；管理员可指定用户，`@user_id=NULL`表示全部用户；状态为NULL表示不限。

```sql
SET @user_id = 2;
SET @status = NULL;
SET @start_at = '2026-01-01 00:00:00';
SET @end_at = '2027-01-01 00:00:00';
SELECT o.id AS order_id, o.user_id, u.username,
       o.status, o.created_at, o.total_amount,
       o.receiver_name, o.receiver_phone, o.receiver_address,
       o.paid_at, o.shipped_at, o.completed_at, o.cancelled_at,
       oi.id AS order_item_id, oi.product_id, oi.product_name,
       oi.unit_price, oi.quantity, oi.unit_price * oi.quantity AS line_amount,
       p.id AS payment_id, p.amount AS payment_amount, p.paid_at AS payment_time
FROM orders AS o
JOIN users AS u ON u.id = o.user_id
JOIN order_item AS oi ON oi.order_id = o.id
LEFT JOIN payment AS p ON p.order_id = o.id
WHERE (@user_id IS NULL OR o.user_id = @user_id)
  AND (@status IS NULL OR o.status = @status)
  AND o.created_at >= @start_at AND o.created_at < @end_at
ORDER BY o.created_at DESC, o.id DESC, oi.id ASC;
```

订单列表接口分页以orders为单位：先按相同过滤选一页订单ID，再取这些订单的全部明细并组装嵌套对象；不能在Q1的明细行上直接LIMIT造成一单被切断。需要某用户全部历史时，用其注册时刻作为起点、查询时刻的下一秒作为终点以覆盖DATETIME秒级记录，或在绑定SQL中同时省略时间条件；并保留本人限制。

### 8.2 Q2 月度销售额及已支付订单量

按唯一成功支付时间筛选并归月，订单处于PAID、SHIPPED、COMPLETED均计入。关联后仍为一订单一行，禁止关联明细再SUM订单金额，也不能用SUM(DISTINCT total_amount)补救（不同订单可能同金额）。

```sql
SET @start_at = '2026-01-01 00:00:00';
SET @end_at = '2027-01-01 00:00:00';
SELECT DATE_FORMAT(p.paid_at, '%Y-%m') AS sales_month,
       SUM(o.total_amount) AS sales_amount,
       COUNT(*) AS paid_order_count
FROM payment AS p
JOIN orders AS o ON o.id = p.order_id
WHERE p.paid_at >= @start_at AND p.paid_at < @end_at
  AND o.status IN ('PAID', 'SHIPPED', 'COMPLETED')
GROUP BY DATE_FORMAT(p.paid_at, '%Y-%m')
ORDER BY sales_month ASC;
```

无交易月份不产生行，完全无数据返回空数组；不伪造实际交易。若前端需连续月份表格，可以按请求区间补0并标明补齐值。区间只覆盖某月一部分时，该月行仅代表所选期间贡献，不宣称完整月销售额。

### 8.3 Q3 指定支付期间商品销量前10

按product_id归并历史数量，用当前商品名称作展示；订单详情仍用历史快照。商品改名、下架均不改变历史归并。销量为件数，不是订单数；并列按商品编号升序，最多10行，不使用“并列全入选”。

```sql
SET @start_at = '2026-11-01 00:00:00';
SET @end_at = '2026-12-01 00:00:00';
SELECT oi.product_id, pr.name AS product_name,
       SUM(oi.quantity) AS sold_quantity
FROM payment AS p
JOIN orders AS o ON o.id = p.order_id
JOIN order_item AS oi ON oi.order_id = o.id
JOIN product AS pr ON pr.id = oi.product_id
WHERE p.paid_at >= @start_at AND p.paid_at < @end_at
  AND o.status IN ('PAID', 'SHIPPED', 'COMPLETED')
GROUP BY oi.product_id, pr.name
ORDER BY sold_quantity DESC, oi.product_id ASC
LIMIT 10;
```

### 8.4 Q4 近30天未下单的普通用户

固定一个查询时刻`as_of`，窗口为`[as_of - INTERVAL 30 DAY, as_of)`，包括恰在下界创建的订单，不包括恰在上界创建的订单。任何状态的订单都算曾下单，包含随后取消者；支付时间无关。含从未下单者，排除管理员及查询时刻之后才注册者。

```sql
SET @as_of = '2026-11-13 22:00:00';
SELECT u.id AS user_id, u.username, u.nickname, u.phone, u.created_at
FROM users AS u
WHERE u.role = 'USER'
  AND u.created_at <= @as_of
  AND NOT EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.user_id = u.id
      AND o.created_at >= @as_of - INTERVAL 30 DAY
      AND o.created_at < @as_of
  )
ORDER BY u.id ASC;
```

`as_of`由服务端取得，管理员可选择不晚于当前时刻的历史截止时刻，禁止未来时刻。新注册且从未下单的普通用户也入选；不要求注册满30天。“截至时刻”是半开区间的终点，同一秒新创建记录如在上界则在下一次查询覆盖，符合报告统一边界约定。

## 9 FR接口清单

API前缀统一`/api/v1`，下表路径省略此前缀。USER表示普通用户，ADMIN表示管理员；公开入口为注册、登录，以及商品列表、商品详情和分类的匿名只读查询（下表记作公开），不增加第三类持久化角色。登录使用带过期时间的JWT Bearer访问令牌，令牌有效期2小时、`sub`为用户ID；受限请求仍查询用户当前角色，不接受请求体指定权限。课程版本不做服务端令牌撤销表，改密码后的已发令牌可持续到过期，见Limitation.md。

成功返回`{data: ...}`，分页返回`{data: {items, page, page_size, total}}`；默认page=1、page_size=20，最大100。订单详情为头部及`items[]`、`payment|null`；金额以两位小数十进制字符串传输，数量为JSON整数，时间为带+08:00字符串，未发生事件为null。错误为`{error: {code, message, details?}}`；204删除不带响应体。空列表200，普通用户访问他人资源按404处理。

通用错误：401 `UNAUTHENTICATED`或`INVALID_CREDENTIALS`，403 `ROLE_FORBIDDEN`，404 `RESOURCE_NOT_FOUND`（订单用`ORDER_NOT_FOUND`），422 `VALIDATION_ERROR`，503 `TRANSACTION_RETRY_EXHAUSTED`，500 `DATA_INTEGRITY_ERROR`。以下列主要业务错误，所有写入错误均不留下部分成功。

### 9.1 FR-01 用户注册与登录

| 方法与路径 | 角色 | 入参 | 出参 | 主要错误码 |
| --- | --- | --- | --- | --- |
| POST /auth/register | 公开 | username、password（8至64字符）、nickname、phone | 201 用户基本资料，不含哈希；同事务建空cart | 409 USERNAME_EXISTS；422 VALIDATION_ERROR；传role拒绝 |
| POST /auth/login | 公开 | username、password | 200 access_token、token_type=Bearer、expires_in=7200、用户ID/角色 | 401 INVALID_CREDENTIALS |
| GET /users/me | USER、ADMIN | 无 | 本人ID、用户名、昵称、电话、角色 | 401 UNAUTHENTICATED |
| PATCH /users/me | USER | nickname、phone，至少一项 | 更新后的本人资料 | 422 VALIDATION_ERROR |
| PUT /users/me/password | USER | old_password、new_password | 修改结果 | 400 OLD_PASSWORD_INCORRECT；422 VALIDATION_ERROR |
| GET /admin/users | ADMIN | username关键词、phone、page、page_size | 普通用户分页列表，不含密码哈希 | 403 ROLE_FORBIDDEN |

管理员账号预置，不从注册或资料修改入口授予ADMIN，不提供角色变更或普通用户删除。密码每次使用新盐，校验后才能改密；日志不得记录原始密码或令牌。

### 9.2 FR-02 商品浏览与查询

| 方法与路径 | 角色 | 入参 | 出参 | 主要错误码 |
| --- | --- | --- | --- | --- |
| GET /products | 公开（游客/USER） | keyword、category_id、min_price、max_price、page、page_size | 仅上架商品，名称、分类、单价、可售量 | 422 PRICE_RANGE_INVALID |
| GET /products/{product_id} | 公开（游客/USER） | 商品ID | 上架商品详情、介绍、available | 404 PRODUCT_NOT_FOUND（含下架） |
| GET /categories | 公开（游客/USER） | 无 | 单层分类列表 | 非法令牌401 |

价格边界为包含式，min_price不得大于max_price，价格不得为负；无匹配结果返回空列表，可售0仍展示但不可加购。

三个查询不要求令牌；携带非法或过期令牌仍返回401 UNAUTHENTICATED，不降级为游客。游客购物车仅保存在浏览器，不调用服务端购物车接口、不占用库存，也不在登录时自动合并。

### 9.3 FR-03 购物车管理

| 方法与路径 | 角色 | 入参 | 出参 | 主要错误码 |
| --- | --- | --- | --- | --- |
| GET /cart | USER | 无 | 本人全部条目、当前价、可售量、上架状态、selected_total | 500 DATA_INTEGRITY_ERROR（缺容器） |
| POST /cart/items | USER | product_id、quantity（本次增加量） | 201新条目或200合并后的条目及参考总价 | 409 PRODUCT_OFF_SHELF、STOCK_INSUFFICIENT；422 QUANTITY_OVERFLOW |
| PATCH /cart/items/{item_id} | USER | quantity（目标数量）、selected，至少一项 | 更新条目和参考总价 | 404 RESOURCE_NOT_FOUND；409 STOCK_INSUFFICIENT、PRODUCT_OFF_SHELF |
| DELETE /cart/items/{item_id} | USER | 条目ID | 204 | 404 RESOURCE_NOT_FOUND |

改quantity检查正整数和当时可售量；仅取消勾选或删除已下架/缺货条目仍允许，不能因缺货让用户无法移出购物车。selected_total按所有勾选条目的**当前**单价乘数量求和，未勾选为空时0.00；对失效条目标记原因，下单再次校验，参考金额不保证成交或库存。

### 9.4 FR-04 提交订单

| 方法与路径 | 角色 | 入参 | 出参 | 主要错误码 |
| --- | --- | --- | --- | --- |
| POST /orders | USER | checkout_token、items[{cart_item_id, quantity}]、receiver_name、receiver_phone、receiver_address | 201新订单；200同token原订单；均含order_id、total_amount、status、items、payment | 409 CHECKOUT_TOKEN_CONFLICT、CART_CHANGED、PRODUCT_OFF_SHELF、STOCK_INSUFFICIENT；422 EMPTY_CHECKOUT、AMOUNT_OVERFLOW |

items是本人购物车全部勾选条目及预期数量；拒绝重复ID、漏掉或夹入未勾选条目。客户端不得提交成交价或total_amount。并发修改购物车导致不同则返回CART_CHANGED；失败时购物车保留。

### 9.5 FR-05 订单查询与处理

| 方法与路径 | 角色 | 入参 | 出参 | 主要错误码 |
| --- | --- | --- | --- | --- |
| GET /orders | USER | status、created_start、created_end、page、page_size | 本人订单分页，items可简述；时间可同时省略表示全部历史 | 422 TIME_RANGE_INVALID |
| GET /orders/{order_id} | USER | 订单ID | 本人完整订单、明细快照及支付 | 404 ORDER_NOT_FOUND |
| POST /orders/{order_id}/cancel | USER | 无请求体 | 200当前CANCELLED及cancelled_at；重复不回补 | 409 ORDER_STATE_CONFLICT；422 QUANTITY_OVERFLOW |
| POST /orders/{order_id}/confirm-receipt | USER | 无请求体 | 200 COMPLETED及completed_at；重复返回原结果 | 409 ORDER_STATE_CONFLICT |
| GET /admin/orders | ADMIN | order_id、user_id、status、created_start、created_end、page、page_size | 全部订单按条件分页 | 422 TIME_RANGE_INVALID |
| GET /admin/orders/{order_id} | ADMIN | 订单ID | 完整订单、用户基本信息、明细、支付 | 404 ORDER_NOT_FOUND |
| POST /admin/orders/{order_id}/ship | ADMIN | 无请求体 | 200 SHIPPED及shipped_at，已完成重试返回当前状态 | 409 ORDER_STATE_CONFLICT |

所有下单时间过滤为左闭右开，起止同时提供或同时省略。没有管理员取消接口；管理员也不能用用户取消路径越权。

### 9.6 FR-06 模拟支付与记录查询

| 方法与路径 | 角色 | 入参 | 出参 | 主要错误码 |
| --- | --- | --- | --- | --- |
| POST /orders/{order_id}/payments/simulate | USER | simulate_result=SUCCESS或FAILURE；不接受amount | 首次成功201，重复成功200；payment_id、amount、paid_at、order_status；模拟失败200 result=FAILURE且payment=null | 404 ORDER_NOT_FOUND；409 ORDER_STATE_CONFLICT |
| GET /orders/{order_id}/payment | USER | 本人订单ID | 200成功记录或null及当前订单状态 | 404 ORDER_NOT_FOUND |
| GET /admin/payments | ADMIN | order_id（必填） | 该单唯一成功支付或null及订单状态 | 404 ORDER_NOT_FOUND |

模拟失败是正常演示结果，不等同数据库写入失败；后者返回通用错误且整笔回滚。此功能不发起第三方扣款，不保存失败尝试历史。

### 9.7 FR-07 商品与分类管理

| 方法与路径 | 角色 | 入参 | 出参 | 主要错误码 |
| --- | --- | --- | --- | --- |
| GET /admin/categories | ADMIN | 无 | 全部单层分类 | 403 ROLE_FORBIDDEN |
| POST /admin/categories | ADMIN | name | 201分类 | 409 CATEGORY_NAME_EXISTS |
| PATCH /admin/categories/{category_id} | ADMIN | name | 更新分类 | 409 CATEGORY_NAME_EXISTS |
| DELETE /admin/categories/{category_id} | ADMIN | 分类ID | 204 | 409 CATEGORY_IN_USE |
| GET /admin/products | ADMIN | keyword、category_id、status、page、page_size | 含上下架商品的分页列表和库存 | 422 VALIDATION_ERROR |
| GET /admin/products/{product_id} | ADMIN | 商品ID | 商品详情及库存 | 404 PRODUCT_NOT_FOUND |
| POST /admin/products | ADMIN | category_id、name、price、description；status可省略 | 201商品；同事务初始化available=0、version=0 | 404 CATEGORY_NOT_FOUND；422 PRICE_INVALID |
| PATCH /admin/products/{product_id} | ADMIN | category_id、name、price、description，至少一项 | 更新后的商品资料，不影响成交快照 | 404 CATEGORY_NOT_FOUND；422 PRICE_INVALID |
| PUT /admin/products/{product_id}/status | ADMIN | status=ON_SHELF或OFF_SHELF | 更新状态 | 422 VALIDATION_ERROR |
| DELETE /admin/products/{product_id} | ADMIN | 商品ID | 204，同时删除零库存记录 | 409 PRODUCT_IN_USE、INVENTORY_NOT_ZERO |

售价严格大于0且最多两位小数，不能依赖数据库自动四舍五入接受非法精度。新商品默认下架，也允许显式创建上架但零库存商品。当前购物车引用也构成PRODUCT_IN_USE。

### 9.8 FR-08 库存查询与维护

| 方法与路径 | 角色 | 入参 | 出参 | 主要错误码 |
| --- | --- | --- | --- | --- |
| GET /admin/inventory | ADMIN | product_id、keyword、page、page_size | 库存ID、商品信息、available、pending_occupied、version、updated_at | 422 VALIDATION_ERROR |
| POST /admin/inventory/{product_id}/restock | ADMIN | quantity（增加量，正INT）、expected_version | 最新available、version、updated_at | 409 INVENTORY_VERSION_CONFLICT；422 QUANTITY_OVERFLOW |
| POST /admin/inventory/{product_id}/count | ADMIN | counted_available（目标可售量，非负INT）、expected_version | delta、最新available、version、updated_at | 409 INVENTORY_VERSION_CONFLICT；422 VALIDATION_ERROR |

库存维护响应丢失后先GET刷新确认，不自动用新版本重发补货。原expected_version已被消费时返回409，因此网络重发不会重复入库；其他写入改变版本也一律要求重新确认。无需新增库存流水表，但也不提供历史变更审计。

### 9.9 FR-09 销售统计与用户查询

| 方法与路径 | 角色 | 入参 | 出参 | 主要错误码 |
| --- | --- | --- | --- | --- |
| GET /admin/statistics/monthly-sales | ADMIN | paid_start、paid_end | Q2：sales_month、sales_amount、paid_order_count数组 | 422 TIME_RANGE_INVALID |
| GET /admin/statistics/top-products | ADMIN | paid_start、paid_end | Q3：product_id、product_name、sold_quantity，最多10项 | 422 TIME_RANGE_INVALID |
| GET /admin/statistics/inactive-users | ADMIN | as_of可省略（默认数据库当前时刻）、page、page_size | Q4：近30天未下单普通用户分页及采用的as_of | 422 AS_OF_INVALID |

两个销售接口要求时间区间同时提供；一次查询固定参数，不因分页重新计算as_of。空结果正常200。统计只查询，不在读取时触发任何库存释放或状态变更。

## 10 种子数据与后续核验建议

种子数据只给出建议，不在本次工作区建立应用或执行持久化业务初始化。初始化导入顺序为users与category、product、inventory、普通用户cart；所有测试用户的角色固定，管理员无cart。账号密码通过初始化时输入或环境变量提供，再以Argon2id生成独立盐哈希，不在文档给出固定明文管理口令。

| 类型 | 建议内容 | 初始约束 |
| --- | --- | --- |
| 管理员 | 1个`admin`，昵称“课程管理员”，联系电话使用明确标注的演示数据 | role=ADMIN，不建cart |
| 普通用户 | 3至5个演示USER，至少一名从未下单 | 每人一个空cart，不使用真实个人联系电话 |
| 分类 | 数码配件、文具、日用，共3个 | 单层、名称唯一 |
| 商品 | 每类2至3个；例如数据线30.00、笔记本20.00；另设下架商品和零库存商品 | 售价正数，介绍可空字符串，每商品均有inventory |
| 库存 | 先随商品创建为0，再走补货流程设10、20、50等小整数 | 初始version=0，补货后版本递增；下架也保留库存 |
| 交易演示 | 待支付、取消、已支付、发货、完成各至少1单，含一单两种商品 | 通过事务生成，不能只改状态伪造时间、支付和库存 |

后续实现应覆盖以下可判定情形；这些是验收设计，不宣称业务代码已经测试通过：

1. 两用户同时购买最后1件，最多一个下单成功；失败者购物车不变。第二件商品扣减失败时第一件也回滚。
2. 同用户同token并发提交，只产生一张订单、一次扣库；同token不同收货信息返回冲突。提交成功但响应丢失后重试返回原单；取消后重试原token仍返回已取消原单。
3. 取消与支付并发，仅一个首次迁移成功；重复取消不重复回补；重复成功支付始终一条payment。模拟失败不创建payment。
4. 盘点页面读取version后发生下单或取消，旧expected_version盘点被拒；库存INT溢出、负量、零售价及孤立外键均失败。
5. 一张订单包含30.00×2和20.00×1，支付后月销售额80.00、订单量1、两商品销量2和1；另一张同金额订单也应额外累计80.00，不能用DISTINCT金额。
6. 跨月份支付按支付月归属；恰在结束时刻支付不入本期；商品改名仍按ID归并；销量相同按ID升序取10。
7. 近30天创建后取消的订单仍排除该用户；从未下单者入选；下界订单算窗口内，上界不算；管理员永不入选。
8. 注册和创建商品的第二步失败分别回滚用户/购物车、商品/库存；商品有历史明细、当前购物车引用或非零库存均不可物理删除。

### 10.1 本次设计文档的SQL核验

2026年11月13日在本机MySQL Community Server 8.0.40上，以临时数据目录、独立端口和独立实例执行本设计DDL；未启动或修改机器原有MySQL80服务，未向现有业务库导入数据。DDL及四条空库查询全部执行成功。另完成46项样例、约束及数据库结构检查，核对结果如下：

- 多明细、同金额的两张80.00订单，以及一张含10种商品、金额200.00的已发货订单，11月合计360.00、已支付订单量3；9月和12月支付分别归属各自月份，11月末下单而12月初支付不进入11月。
- 前10销量结果按商品ID归并，商品改名不拆分；第一商品4件、第二商品2件，其余并列1件按ID取至第10号，不多纳入并列商品。
- 普通用户订单查询保留待支付及取消订单；近30天查询包含从未下单、仅历史订单、仅上界订单者，排除窗口内已取消订单用户、恰在下界下单者、管理员及未来注册者。
- 用户名、分类、购物车、明细、库存、结算标识和成功支付的唯一约束，正价正量、非负库存、状态时间组合、事件先后、数值上界、外键和删除保护均按预期拒绝非法SQL。事务中先改库存再触发失败，连接退出回滚后库存及version保持原值。
- 九张表均为InnoDB及utf8mb4；样例订单总额与明细和一致，成功支付金额与时间同订单一致。

以上只验证文档所含DDL、查询和数据库约束，不代表接口、并发业务流程或前后端已经实现。第10节列出的应用事务验收仍需在后续编码后完成。

## 11 交接结论

本设计已确定库存口径、释放规则、token、锁顺序、隔离级别、时区、九表字段、可执行DDL、四条查询、全部FR接口与事务边界，不存在需要先征求用户才能定下的技术分支。限制同步在`Limitation.md`；现有课程报告正文、封面身份和references保持原样。后续如要启用超时取消、管理员代取消、实物库存账、退款或真实支付，属于业务范围变更，必须另行调整需求及报告后再实现。
