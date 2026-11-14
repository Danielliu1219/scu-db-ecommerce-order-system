import hashlib
import json


def canonical(user_id, data):
    payload = {
        "user_id": str(user_id),
        "items": [
            {"cart_item_id": str(i.cart_item_id), "quantity": i.quantity}
            for i in sorted(data.items, key=lambda i: i.cart_item_id)
        ],
        "receiver_name": data.receiver_name,
        "receiver_phone": data.receiver_phone,
        "receiver_address": data.receiver_address,
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def digest(user_id, data):
    return hashlib.sha256(canonical(user_id, data)).hexdigest()
