from conftest import make_material_payload

BUILTIN_CATEGORIES = ["苔藓", "沉木", "底床", "石材", "水草", "设备"]


def test_categories_endpoint_returns_builtin_six(client):
    response = client.get("/api/materials/categories")
    assert response.status_code == 200
    for category in BUILTIN_CATEGORIES:
        assert category in response.json()


def test_categories_not_swallowed_by_detail_route(client):
    response = client.get("/api/materials/categories")
    assert response.status_code != 422
    assert isinstance(response.json(), list)


def test_list_default_returns_eight_seeds_ordered_by_id(client):
    response = client.get("/api/materials/")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 8
    assert [item["id"] for item in items] == sorted(item["id"] for item in items)
    assert items[0]["name"] == "圣诞莫斯"


def test_list_without_trailing_slash_redirects(client):
    response = client.get("/api/materials", follow_redirects=False)
    assert response.status_code == 307
    followed = client.get("/api/materials")
    assert followed.status_code == 200
    assert len(followed.json()) == 8


def test_filter_match_returns_only_that_category(client):
    response = client.get("/api/materials/", params={"category": "苔藓"})
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 4
    assert all(item["category"] == "苔藓" for item in items)


def test_filter_no_match_returns_empty_list(client):
    response = client.get("/api/materials/", params={"category": "设备"})
    assert response.status_code == 200
    assert response.json() == []


def test_filter_strips_surrounding_whitespace(client):
    response = client.get("/api/materials/", params={"category": " 苔藓 "})
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 4
    assert all(item["category"] == "苔藓" for item in items)


def test_filter_empty_string_treated_as_no_filter(client):
    response = client.get("/api/materials/", params={"category": ""})
    assert response.status_code == 200
    assert len(response.json()) == 8


def test_filter_whitespace_only_treated_as_no_filter(client):
    response = client.get("/api/materials/", params={"category": "   "})
    assert response.status_code == 200
    assert len(response.json()) == 8


def test_create_keeps_existing_visible_and_avoids_id_collision(client):
    response = client.post("/api/materials/", json=make_material_payload())
    assert response.status_code == 200
    created = response.json()
    assert created["id"] not in range(1, 9)

    items = client.get("/api/materials/").json()
    assert len(items) == 9
    assert created["id"] in [item["id"] for item in items]

    first = client.get("/api/materials/1").json()
    assert first["name"] == "圣诞莫斯"


def test_detail_update_delete_consistent_for_seed_record(client):
    detail = client.get("/api/materials/3")
    assert detail.status_code == 200
    assert detail.json()["name"] == "大三角莫斯"

    updated = client.put(
        "/api/materials/3", json=make_material_payload(name="改名莫斯", category="苔藓")
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "改名莫斯"

    deleted = client.delete("/api/materials/3")
    assert deleted.status_code == 200

    gone = client.get("/api/materials/3")
    assert gone.status_code == 404
    assert gone.json()["detail"] == "Material not found"


def test_missing_material_404_wording(client):
    for method in ("get", "delete"):
        response = getattr(client, method)("/api/materials/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Material not found"
    response = client.put("/api/materials/999", json=make_material_payload())
    assert response.status_code == 404
    assert response.json()["detail"] == "Material not found"


def test_non_integer_id_still_422(client):
    response = client.get("/api/materials/abc")
    assert response.status_code == 422


def test_categories_sync_with_actual_values(client):
    client.post("/api/materials/", json=make_material_payload(category="CO2配件"))
    categories = client.get("/api/materials/categories").json()
    assert "CO2配件" in categories
    for category in BUILTIN_CATEGORIES:
        assert category in categories


def test_new_category_record_is_filterable(client):
    client.post("/api/materials/", json=make_material_payload(category="CO2配件"))
    items = client.get("/api/materials/", params={"category": "CO2配件"}).json()
    assert len(items) == 1
    assert items[0]["category"] == "CO2配件"
