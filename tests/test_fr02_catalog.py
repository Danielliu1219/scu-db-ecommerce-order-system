from tests.fixtures import auth


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
