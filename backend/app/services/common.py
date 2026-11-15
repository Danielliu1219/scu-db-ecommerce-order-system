from sqlalchemy import func, select


def now(session, previous=None):
    current = session.scalar(select(func.now()))
    return max(current, previous) if previous is not None else current


def paged(items, total, page, page_size):
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def contains(column, keyword):
    return column.contains(keyword.strip(), autoescape=True)
