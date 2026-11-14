from sqlalchemy import func, select


def now(session, previous=None):
    current = session.scalar(select(func.now()))
    return max(current, previous) if previous is not None else current


def page(session, statement, page=1, page_size=20):
    total = session.scalar(select(func.count()).select_from(statement.order_by(None).subquery()))
    return session.execute(statement.offset((page - 1) * page_size).limit(page_size)), total


def paged(items, total, page, page_size):
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def contains(column, keyword):
    return column.contains(keyword.strip(), autoescape=True)
