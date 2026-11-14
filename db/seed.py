"""Create missing demo identities and zero-stock catalog; never overwrite records."""

import getpass
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / "backend/.env")

from app.models import Category, Product, User
from app.schemas.catalog import ProductCreate
from app.security import hash_password
from app.services.catalog import create_in_session
from app.services.identity import create
from app.transactions import write
from sqlalchemy import select


def seed(admin_password=None, demo_password=None):
    admin_password = (
        admin_password
        or os.getenv("ADMIN_PASSWORD")
        or getpass.getpass("Admin password (8-64 chars): ")
    )
    demo_password = (
        demo_password
        or os.getenv("DEMO_PASSWORD")
        or getpass.getpass("Demo user password (8-64 chars): ")
    )
    if not all(8 <= len(p) <= 64 for p in (admin_password, demo_password)):
        raise ValueError("Passwords must contain 8-64 characters")

    def change(s):
        for username, nickname, role, password in (
            ("admin", "课程管理员", "ADMIN", admin_password),
            ("demo_01", "演示用户一", "USER", demo_password),
            ("demo_02", "演示用户二", "USER", demo_password),
            ("demo_03", "从未下单演示用户", "USER", demo_password),
        ):
            if not s.scalar(select(User).where(User.username == username)):
                create(s, username, hash_password(password), nickname, "演示-000", role)
        catalog = {
            "数码配件": [
                ("数据线", "30.00", "ON_SHELF"),
                ("无线鼠标", "59.00", "ON_SHELF"),
                ("零库存样品", "10.00", "ON_SHELF"),
            ],
            "文具": [("笔记本", "20.00", "ON_SHELF"), ("中性笔", "5.00", "ON_SHELF")],
            "日用": [
                ("保温杯", "39.90", "ON_SHELF"),
                ("下架样品", "15.00", "OFF_SHELF"),
            ],
        }
        for category, goods in catalog.items():
            c = s.scalar(select(Category).where(Category.name == category))
            if c is None:
                c = Category(name=category)
                s.add(c)
                s.flush()
            for name, price, status in goods:
                if not s.scalar(
                    select(Product).where(Product.category_id == c.id, Product.name == name)
                ):
                    create_in_session(
                        s,
                        ProductCreate(
                            category_id=c.id,
                            name=name,
                            price=price,
                            description="课程演示商品",
                            status=status,
                        ),
                    )

    write(change)


if __name__ == "__main__":
    seed()
    print("Missing identities and zero-stock catalog initialized; existing records preserved")
