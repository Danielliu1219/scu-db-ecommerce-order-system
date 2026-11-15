from sqlalchemy import text

from ..dependencies import require
from ..errors import fail
from ..queries import sql
from ..transactions import read
from ..value_types import local_time, time_range
from .common import now, paged


def sales(actor, paid_start, paid_end, top=False):
    require(actor, "ADMIN")
    start, end = time_range(paid_start, paid_end, True)

    def query(s):
        rows = s.execute(text(sql(3 if top else 2)), {"start_at": start, "end_at": end}).mappings()
        if top:
            return [
                {
                    "product_id": str(r["product_id"]),
                    "product_name": r["product_name"],
                    "sold_quantity": int(r["sold_quantity"]),
                }
                for r in rows
            ]
        return [
            {
                "sales_month": r["sales_month"],
                "sales_amount": r["sales_amount"],
                "paid_order_count": int(r["paid_order_count"]),
            }
            for r in rows
        ]

    return read(query)


def inactive(actor, as_of=None, page_number=1, page_size=20):
    require(actor, "ADMIN")

    def query(s):
        current = now(s)
        cutoff = local_time(as_of, "AS_OF_INVALID") if as_of is not None else current
        if cutoff > current:
            fail("AS_OF_INVALID", 422)
        statement = sql(4)
        params = {
            "as_of": cutoff,
            "offset": (page_number - 1) * page_size,
            "limit": page_size,
        }
        # Keep the contract Q4 intact. The total-only row also covers out-of-range pages.
        page_sql = f"""
            WITH inactive AS ({statement})
            SELECT totals.total, page_rows.*
            FROM (SELECT COUNT(*) AS total FROM inactive) AS totals
            LEFT JOIN (
                SELECT * FROM inactive ORDER BY user_id LIMIT :limit OFFSET :offset
            ) AS page_rows ON TRUE
            ORDER BY page_rows.user_id
        """
        rows = s.execute(text(page_sql), params).mappings().all()
        items = []
        for row in rows:
            if row["user_id"] is not None:
                item = dict(row)
                item.pop("total")
                item["user_id"] = str(item["user_id"])
                items.append(item)
        return paged(items, rows[0]["total"], page_number, page_size) | {"as_of": cutoff}

    return read(query)
