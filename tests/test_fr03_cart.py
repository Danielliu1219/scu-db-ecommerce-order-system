from tests.fixtures import auth


def test_merge_selection_ownership_and_invalid_item_removal(client, accounts, goods):
    h = auth(accounts["alice"])
    p = goods[0]["id"]
    r = client.post("/api/v1/cart/items", headers=h, json={"product_id": p, "quantity": 2})
    assert r.status_code == 201
    item = r.json()["data"]["item"]
    assert (
        client.post(
            "/api/v1/cart/items", headers=h, json={"product_id": p, "quantity": 1}
        ).status_code
        == 200
    )
    assert client.get("/api/v1/cart", headers=h).json()["data"]["selected_total"] == "90.00"
    assert (
        client.patch(
            "/api/v1/cart/items/" + item["id"],
            headers=auth(accounts["bob"]),
            json={"selected": False},
        ).status_code
        == 404
    )
    assert (
        client.post(
            "/api/v1/cart/items", headers=h, json={"product_id": p, "quantity": True}
        ).status_code
        == 422
    )
    assert (
        client.delete("/api/v1/admin/products/" + p, headers=auth(accounts["admin"])).json()[
            "error"
        ]["code"]
        == "PRODUCT_IN_USE"
    )
    client.put(
        f"/api/v1/admin/products/{p}/status",
        headers=auth(accounts["admin"]),
        json={"status": "OFF_SHELF"},
    )
    path = "/api/v1/cart/items/" + item["id"]
    assert client.patch(path, headers=h, json={"selected": False}).status_code == 200
    assert client.patch(path, headers=h, json={"selected": True}).status_code == 409
    assert client.delete(path, headers=h).status_code == 204
