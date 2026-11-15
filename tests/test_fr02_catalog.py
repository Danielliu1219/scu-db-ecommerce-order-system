from tests.fixtures import auth


def test_guest_can_browse_but_cannot_write_or_use_accounts(client, goods):
    assert {} in client.get("/openapi.json").json()["paths"]["/api/v1/products"]["get"]["security"]
    assert client.get("/api/v1/categories").status_code == 200
    result = client.get("/api/v1/products").json()["data"]
    assert result["total"] == 2
    assert client.get("/api/v1/products/" + goods[0]["id"]).status_code == 200
    assert (
        client.get("/api/v1/products", headers={"Authorization": "Bearer invalid"}).status_code
        == 401
    )
    for method, path in (("get", "/cart"), ("get", "/orders"), ("get", "/admin/products")):
        assert getattr(client, method)("/api/v1" + path).status_code == 401
    assert (
        client.post(
            "/api/v1/cart/items", json={"product_id": goods[0]["id"], "quantity": 1}
        ).status_code
        == 401
    )


def test_filters_and_zero_stock(client, accounts, goods):
    h = auth(accounts["alice"])
    assert (
        client.get(
            "/api/v1/products",
            headers=h,
            params={"keyword": "数据", "min_price": "30", "max_price": "30"},
        ).json()["data"]["total"]
        == 1
    )
    assert (
        client.get(
            "/api/v1/products", headers=h, params={"min_price": "31", "max_price": "30"}
        ).json()["error"]["code"]
        == "PRICE_RANGE_INVALID"
    )
    assert (
        client.get("/api/v1/products", headers=h, params={"keyword": "%"}).json()["data"]["total"]
        == 0
    )
    p = goods[0]["id"]
    assert (
        client.put(
            f"/api/v1/admin/products/{p}/status",
            headers=auth(accounts["admin"]),
            json={"status": "OFF_SHELF"},
        ).status_code
        == 200
    )
    assert client.get(f"/api/v1/products/{p}", headers=h).status_code == 404
    assert client.get("/api/v1/products", headers=auth(accounts["admin"])).status_code == 403
