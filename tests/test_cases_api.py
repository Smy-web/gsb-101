from tests.conftest import NEW_CASE

BUILTIN_STYLES = ["ADA自然风格", "Iwagumi石景风格", "荷兰景风格", "凹形构图风格", "凸形构图风格", "中式山水风格"]


def test_styles_endpoint_available_and_contains_builtin_six(client):
    resp = client.get("/api/cases/styles")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    for style in BUILTIN_STYLES:
        assert style in data


def test_styles_not_swallowed_by_detail_route(client):
    resp = client.get("/api/cases/styles")
    assert resp.status_code != 422
    assert resp.status_code == 200


def test_list_returns_seed_data_ordered_by_id(client):
    resp = client.get("/api/cases/")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 5
    assert [c["id"] for c in data] == list(range(1, 6))
    assert data[0]["title"].startswith("幽林秘境")
    assert data[0]["created_at"] == "2024-01-15T10:30:00"


def test_filter_by_style_returns_only_matches(client):
    resp = client.get("/api/cases/", params={"style": "荷兰景风格"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert all(c["style"] == "荷兰景风格" for c in data)


def test_filter_no_match_returns_empty_list(client):
    resp = client.get("/api/cases/", params={"style": "凸形构图风格"})
    assert resp.status_code == 200
    assert resp.json() == []


def test_filter_style_case_insensitive(client):
    resp = client.get("/api/cases/", params={"style": "ada自然风格"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["style"] == "ADA自然风格"


def test_filter_strips_surrounding_whitespace(client):
    resp = client.get("/api/cases/", params={"style": " 荷兰景风格 "})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["style"] == "荷兰景风格"


def test_filter_empty_string_means_no_filter(client):
    resp = client.get("/api/cases/", params={"style": ""})
    assert resp.status_code == 200
    assert len(resp.json()) == 5


def test_filter_by_difficulty(client):
    resp = client.get("/api/cases/", params={"difficulty": "中等"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3
    assert all(c["difficulty"] == "中等" for c in data)


def test_filter_style_and_difficulty_combined(client):
    resp = client.get("/api/cases/", params={"style": "荷兰景风格", "difficulty": "中等"})
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_keeps_existing_records_visible_and_no_id_collision(client):
    resp = client.post("/api/cases/", json=NEW_CASE)
    assert resp.status_code == 200
    new_id = resp.json()["id"]
    assert new_id > 5

    listing = client.get("/api/cases/").json()
    assert len(listing) == 6
    assert {c["id"] for c in listing} == set(range(1, 6)) | {new_id}

    first = client.get("/api/cases/1").json()
    assert first["title"].startswith("幽林秘境")
    created = client.get(f"/api/cases/{new_id}").json()
    assert created["title"] == "测试案例 - 45cm造景"


def test_new_style_appears_in_styles_and_is_filterable(client):
    client.post("/api/cases/", json=NEW_CASE)
    styles = client.get("/api/cases/styles").json()
    assert "自然风" in styles
    for style in BUILTIN_STYLES:
        assert style in styles

    data = client.get("/api/cases/", params={"style": "自然风"}).json()
    assert len(data) == 1
    assert data[0]["style"] == "自然风"


def test_detail_update_delete_visibility_consistent(client):
    resp = client.get("/api/cases/3")
    assert resp.status_code == 200
    assert resp.json()["title"].startswith("热带雨林")

    updated = dict(NEW_CASE, title="改名后的雨林造景")
    resp = client.put("/api/cases/3", json=updated)
    assert resp.status_code == 200
    assert resp.json()["title"] == "改名后的雨林造景"
    assert client.get("/api/cases/3").json()["title"] == "改名后的雨林造景"

    resp = client.delete("/api/cases/3")
    assert resp.status_code == 200
    resp = client.get("/api/cases/3")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Case study not found"


def test_missing_case_404_message_on_get_put_delete(client):
    resp = client.get("/api/cases/999")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Case study not found"

    resp = client.put("/api/cases/999", json=NEW_CASE)
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Case study not found"

    resp = client.delete("/api/cases/999")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Case study not found"


def test_non_integer_id_is_422_not_500(client):
    resp = client.get("/api/cases/abc")
    assert resp.status_code == 422
