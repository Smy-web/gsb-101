from tests.conftest import NEW_MATERIAL

BUILTIN_CATEGORIES = ["苔藓", "沉木", "底床", "石材", "水草", "设备"]


def test_categories_endpoint_available_and_contains_builtin_six(client):
    resp = client.get("/api/materials/categories")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    for category in BUILTIN_CATEGORIES:
        assert category in data


def test_categories_not_swallowed_by_detail_route(client):
    resp = client.get("/api/materials/categories")
    assert resp.status_code != 422
    assert resp.status_code == 200


def test_list_returns_seed_data_ordered_by_id(client):
    resp = client.get("/api/materials/")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 8
    assert [m["id"] for m in data] == list(range(1, 9))
    assert data[0]["name"] == "圣诞莫斯"


def test_list_without_trailing_slash_redirects(client):
    resp = client.get("/api/materials", follow_redirects=False)
    assert resp.status_code == 307
    assert client.get("/api/materials").status_code == 200


def test_filter_by_category_returns_only_matches(client):
    resp = client.get("/api/materials/", params={"category": "苔藓"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 4
    assert all(m["category"] == "苔藓" for m in data)


def test_filter_no_match_returns_empty_list(client):
    resp = client.get("/api/materials/", params={"category": "设备"})
    assert resp.status_code == 200
    assert resp.json() == []


def test_filter_strips_surrounding_whitespace(client):
    resp = client.get("/api/materials/", params={"category": " 苔藓 "})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 4
    assert all(m["category"] == "苔藓" for m in data)


def test_filter_empty_string_means_no_filter(client):
    resp = client.get("/api/materials/", params={"category": ""})
    assert resp.status_code == 200
    assert len(resp.json()) == 8


def test_filter_whitespace_only_means_no_filter(client):
    resp = client.get("/api/materials/", params={"category": "   "})
    assert resp.status_code == 200
    assert len(resp.json()) == 8


def test_create_keeps_existing_records_visible_and_no_id_collision(client):
    resp = client.post("/api/materials/", json=NEW_MATERIAL)
    assert resp.status_code == 200
    new_id = resp.json()["id"]
    assert new_id > 8

    listing = client.get("/api/materials/").json()
    assert len(listing) == 9
    assert {m["id"] for m in listing} == set(range(1, 9)) | {new_id}

    first = client.get("/api/materials/1").json()
    assert first["name"] == "圣诞莫斯"
    created = client.get(f"/api/materials/{new_id}").json()
    assert created["name"] == "测试莫斯"


def test_detail_update_delete_visibility_consistent(client):
    resp = client.get("/api/materials/3")
    assert resp.status_code == 200
    assert resp.json()["name"] == "大三角莫斯"

    updated = dict(NEW_MATERIAL, name="改名后的大三角莫斯")
    resp = client.put("/api/materials/3", json=updated)
    assert resp.status_code == 200
    assert resp.json()["name"] == "改名后的大三角莫斯"
    assert client.get("/api/materials/3").json()["name"] == "改名后的大三角莫斯"

    resp = client.delete("/api/materials/3")
    assert resp.status_code == 200
    resp = client.get("/api/materials/3")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Material not found"


def test_missing_material_404_message_on_get_put_delete(client):
    resp = client.get("/api/materials/999")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Material not found"

    resp = client.put("/api/materials/999", json=NEW_MATERIAL)
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Material not found"

    resp = client.delete("/api/materials/999")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Material not found"


def test_categories_reflect_stored_values(client):
    client.post("/api/materials/", json=dict(NEW_MATERIAL, category="造景配件"))
    categories = client.get("/api/materials/categories").json()
    assert "造景配件" in categories
    for category in BUILTIN_CATEGORIES:
        assert category in categories

    data = client.get("/api/materials/", params={"category": "造景配件"}).json()
    assert len(data) == 1
    assert data[0]["category"] == "造景配件"


def test_non_integer_id_is_422_not_500(client):
    resp = client.get("/api/materials/abc")
    assert resp.status_code == 422
