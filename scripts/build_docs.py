# -*- coding: utf-8 -*-
"""从 scripts/data.py 生成 Markdown 需求与数据库设计文档。"""

from __future__ import annotations

from pathlib import Path

from data import (
    BUSINESS_RULES,
    COURSE_MAPPING,
    FUNCTIONS,
    PLAN,
    PROJECT,
    ROLES,
    SCOPE_IN,
    SCOPE_OUT,
    SQL_TASKS,
    TABLES,
    TECH_STACK,
)

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def _meta() -> str:
    return (
        f"> 项目：**{PROJECT['name']}**（{PROJECT['scheme']}）  \n"
        f"> 课程：{PROJECT['course_full']}  \n"
        f"> 组号：第 {PROJECT['group_no']} 组  \n"
        f"> 生成日期：2026-11-08  \n"
        f"> 本文件由 `scripts/build_docs.py` 从 `scripts/data.py` 生成，请勿手改。"
    )


def _escape(text: str) -> str:
    return str(text).replace("|", "\\|").replace("\n", "<br>")


def _table(headers: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(_escape(c) for c in row) + " |")
    return "\n".join(lines)


def build_requirements_md() -> Path:
    lines = [
        f"# {PROJECT['name']}——需求与功能清单",
        "",
        _meta(),
        "",
        "## 1. 项目概览",
        "",
        f"- 中文名称：{PROJECT['name']}",
        f"- 英文名称：{PROJECT['en_name']}",
        f"- 项目代号：{PROJECT['code']}",
        f"- 选题类型：{PROJECT['scheme']}",
        "- 一句话定位：面向中小电商场景，围绕“商品—购物车—订单—支付—库存”主链路构建的 B/S 订单管理系统。",
        "- 设计重点：订单与库存一致性、订单状态机、支付幂等、重复提交防护、多表统计查询。",
        "",
        "## 2. 用户角色",
        "",
        _table(
            ["角色", "数据范围", "主要权限"],
            [[r["role"], r["scope"], r["permissions"]] for r in ROLES],
        ),
        "",
        "## 3. 功能清单",
        "",
        "### 3.1 功能结构概览",
        "",
        _table(
            ["编号", "功能名称", "使用角色", "功能概述"],
            [[f["id"], f["name"], f["role"], f["summary"]] for f in FUNCTIONS],
        ),
        "",
        "### 3.2 功能详细说明",
        "",
    ]

    for fn in FUNCTIONS:
        lines += [
            f"#### {fn['id']} {fn['name']}",
            "",
            f"- **使用角色**：{fn['role']}",
            f"- **功能描述**：{fn['desc']}",
            f"- **约束条件与异常处理**：{fn['constraints']}",
            f"- **输入**：{fn['input']}",
            f"- **处理**：{fn['process']}",
            f"- **输出**：{fn['output']}",
            f"- **主要数据表**：{fn['tables']}",
            "",
        ]

    lines += [
        "## 4. 关键业务规则",
        "",
        _table(
            ["规则", "实现方式与异常提示"],
            [[r["rule"], r["implementation"]] for r in BUSINESS_RULES],
        ),
        "",
        "## 5. 课程要求对应",
        "",
        _table(
            ["课程要求", "本项目的落实"],
            [[c["requirement"], c["implementation"]] for c in COURSE_MAPPING],
        ),
        "",
        "## 6. SQL 任务",
        "",
        _table(
            ["编号", "任务", "涉及表", "主要 SQL 技术"],
            [[s["id"], s["task"], s["tables"], s["techniques"]] for s in SQL_TASKS],
        ),
        "",
        "## 7. 范围与边界",
        "",
        "### 7.1 纳入范围",
        "",
    ]
    lines += [f"- {item}" for item in SCOPE_IN]
    lines += ["", "### 7.2 暂不实现", ""]
    lines += [f"- {item}" for item in SCOPE_OUT]
    lines += [
        "",
        "## 8. 技术路线（建议）",
        "",
        _table(
            ["层次", "技术选型", "说明"],
            [[t["layer"], t["stack"], t["note"]] for t in TECH_STACK],
        ),
        "",
        "## 9. 后续计划",
        "",
        _table(
            ["阶段", "主要工作", "产出"],
            [[p["phase"], p["work"], p["output"]] for p in PLAN],
        ),
        "",
    ]

    path = DOCS / "01-requirements.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def build_database_md() -> Path:
    lines = [
        f"# {PROJECT['name']}——数据库设计（初稿）",
        "",
        _meta(),
        "",
        "> 阶段说明：本文件是立项阶段的初步设计，用于统一表名、字段范围和业务约束；完整字段类型、DDL、ER 图和数据样例将在第 11 周细化。",
        "",
        "## 1. 设计原则",
        "",
        "- 使用 MySQL 8.0、InnoDB、utf8mb4；金额统一 `DECIMAL(10,2)`，时间统一 `DATETIME`。",
        "- 主键统一 `BIGINT UNSIGNED AUTO_INCREMENT`；业务单号（订单号、支付号）单独建唯一索引。",
        "- 主数据（用户、分类、商品）采用状态字段做逻辑删除，避免破坏历史订单引用。",
        "- 订单明细保存商品名称、下单单价、数量和小计快照，商品调价不影响历史订单。",
        "- 库存变动必须写 `inventory_log`，保证可追溯；库存扣减与回补必须在事务内完成。",
        "- 表名使用小写复数或业务名，字段名使用 snake_case。",
        "",
        "## 2. 实体关系（Mermaid 初稿）",
        "",
        "```mermaid",
        "erDiagram",
        "    users ||--o{ address : has",
        "    users ||--|| cart : owns",
        "    users ||--o{ orders : places",
        "    users ||--o{ payment : pays",
        "    category ||--o{ product : contains",
        "    category ||--o{ category : parent_of",
        "    product ||--|| inventory : has",
        "    product ||--o{ inventory_log : changes",
        "    product ||--o{ cart_item : added_to",
        "    cart ||--o{ cart_item : contains",
        "    orders ||--|{ order_item : contains",
        "    product ||--o{ order_item : snapshot",
        "    orders ||--|| payment : paid_by",
        "    address ||--o{ orders : shipping",
        "```",
        "",
        "> 说明：`payment.order_id` 唯一，用于支付幂等；`cart.user_id` 唯一，保证一个用户一个购物车；`inventory.product_id` 唯一，保证一个商品一条库存记录。",
        "",
        "## 3. 表清单",
        "",
        _table(
            ["序号", "表名", "中文名", "关键字段", "作用"],
            [[t["no"], t["name"], t["cn"], t["fields"], t["purpose"]] for t in TABLES],
        ),
        "",
        "## 4. 关键约束",
        "",
        _table(
            ["表", "约束 / 索引", "说明"],
            [
                ["users", "UNIQUE(username), UNIQUE(phone)", "用户名、手机号唯一；role、status 使用枚举/短字符串并在服务层校验。"],
                ["address", "FK(user_id), INDEX(user_id, is_default)", "同一用户默认地址由事务保证唯一；删除前检查未完成订单引用。"],
                ["category", "UNIQUE(name), FK(parent_id)", "分类名唯一；存在子分类或商品时禁止删除。"],
                ["product", "FK(category_id), CHECK(price >= 0)", "仅上架商品可购买；被订单引用时只下架不物理删除。"],
                ["inventory", "UNIQUE(product_id), CHECK(stock >= 0)", "一商品一库存；低库存条件为 stock <= warning_threshold。"],
                ["inventory_log", "FK(product_id), CHECK(change_qty <> 0)", "只增不改；记录 before_stock / after_stock 与 change_type。"],
                ["cart", "UNIQUE(user_id)", "一个用户一个购物车。"],
                ["cart_item", "UNIQUE(cart_id, product_id), CHECK(quantity > 0)", "重复加购累加数量；勾选状态 selected 为 0/1。"],
                ["orders", "UNIQUE(order_no), UNIQUE(idempotency_key), CHECK(total_amount >= 0)", "订单号与幂等键唯一；状态机集中校验。"],
                ["order_item", "FK(order_id), FK(product_id), CHECK(quantity > 0), CHECK(unit_price >= 0)", "保存商品名称、单价、数量、小计快照。"],
                ["payment", "UNIQUE(order_id), CHECK(amount >= 0)", "订单最多一条成功支付记录；重复支付返回已有结果。"],
            ],
        ),
        "",
        "## 5. 索引规划",
        "",
        _table(
            ["索引", "列", "用途"],
            [
                ["idx_orders_user_time", "orders(user_id, created_at)", "用户订单列表按时间倒序分页。"],
                ["idx_orders_status_time", "orders(status, created_at)", "后台按状态筛选与履约看板。"],
                ["idx_product_category_status", "product(category_id, status)", "分类页与上架商品检索。"],
                ["idx_order_item_order", "order_item(order_id)", "订单详情与销量聚合。"],
                ["idx_inventory_stock", "inventory(stock)", "低库存扫描与预警。"],
                ["uk_payment_order", "payment(order_id) UNIQUE", "支付幂等与订单支付查询。"],
                ["uk_cart_item", "cart_item(cart_id, product_id) UNIQUE", "重复加购合并。"],
            ],
        ),
        "",
        "## 6. 状态与枚举",
        "",
        _table(
            ["字段", "建议取值", "说明"],
            [
                ["users.role", "USER / ADMIN", "普通用户 / 管理员。"],
                ["users.status", "0 / 1", "禁用 / 正常；禁用用户不能登录和下单。"],
                ["product.status", "0 / 1 / 2", "下架 / 上架 / 已删除（逻辑删除）。"],
                ["orders.status", "UNPAID / PAID / SHIPPED / COMPLETED / CANCELLED", "待支付 / 已支付 / 已发货 / 已完成 / 已取消。"],
                ["payment.status", "PENDING / SUCCESS / FAILED", "待支付 / 支付成功 / 支付失败；退款暂不实现。"],
                ["inventory_log.change_type", "PURCHASE_IN / ORDER_OUT / CANCEL_IN / ADJUST", "采购入库 / 下单出库 / 取消回补 / 盘点调整。"],
                ["cart_item.selected", "0 / 1", "未勾选 / 已勾选。"],
                ["address.is_default", "0 / 1", "非默认 / 默认。"],
            ],
        ),
        "",
        "## 7. 事务与并发设计",
        "",
        "### 7.1 下单扣库存",
        "",
        "```sql",
        "START TRANSACTION;",
        "-- 1. 按 product_id 升序锁定库存行，避免死锁",
        "SELECT stock FROM inventory WHERE product_id = ? FOR UPDATE;",
        "-- 2. 校验库存；不足则 ROLLBACK 并返回具体商品",
        "-- 3. 写 orders、order_item",
        "-- 4. UPDATE inventory SET stock = stock - ? WHERE product_id = ?;",
        "-- 5. 写 inventory_log（ORDER_OUT）",
        "-- 6. 删除已结算的 cart_item",
        "COMMIT;",
        "```",
        "",
        "### 7.2 取消回补",
        "",
        "- 仅允许 `UNPAID → CANCELLED`；事务内更新订单状态、回补 `inventory.stock`、写 `inventory_log`（CANCEL_IN）。",
        "- 若订单已支付，取消需要退款流程；本期不实现，返回“已支付订单请联系管理员”。",
        "",
        "### 7.3 支付幂等",
        "",
        "- `payment.order_id` 唯一；重复支付请求先查已有成功记录，存在则直接返回。",
        "- 支付状态与订单状态在同一事务内更新；失败支付保留 FAILED 记录用于排查。",
        "",
        "### 7.4 重复提交",
        "",
        "- 下单请求携带 `idempotency_key`；`orders.idempotency_key` 唯一。",
        "- 重复请求返回同一订单，不重复扣库存。",
        "",
        "## 8. 待细化事项",
        "",
        "- [ ] 完整字段类型、长度、默认值、注释。",
        "- [ ] 完整 ER 图（Chen 表示法或 Crow's Foot）。",
        "- [ ] 建表 DDL 与初始化数据（用户、分类、商品、库存、样例订单）。",
        "- [ ] 外键删除策略（RESTRICT / CASCADE）逐表确认。",
        "- [ ] 订单状态机时序图与异常测试用例。",
        "",
    ]

    path = DOCS / "02-database-design.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def build_docs(group_no: str = "X") -> tuple[Path, Path]:
    PROJECT["group_no"] = group_no
    return build_requirements_md(), build_database_md()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--group", default="X")
    args = parser.parse_args()
    for p in build_docs(args.group):
        print(p)
