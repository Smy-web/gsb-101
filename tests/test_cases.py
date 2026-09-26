from conftest import make_case_payload

BUILTIN_STYLES = [
    "ADA自然风格",
    "Iwagumi石景风格",
    "荷兰景风格",
    "凹形构图风格",
    "凸形构图风格",
    "中式山水风格",
]


def test_styles_endpoint_returns_builtin_six(client):
    response = client.get("/api/cases/styles")
    assert response.status_code == 200
    for style in BUILTIN_STYLES:
        assert style in response.json()


def test_styles_not_swallowed_by_detail_route(client):
    response = client.get("/api/cases/styles")
    assert response.status_code != 422
    assert isinstance(response.json(), list)


def test_list_default_returns_five_seeds_ordered_by_id(client):
    response = client.get("/api/cases/")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 5
    assert [item["id"] for item in items] == sorted(item["id"] for item in items)
    assert isinstance(items[0]["created_at"], str)


def test_list_without_trailing_slash_redirects(client):
    response = client.get("/api/cases", follow_redirects=False)
    assert response.status_code == 307
    followed = client.get("/api/cases")
    assert followed.status_code == 200
    assert len(followed.json()) == 5


def test_filter_style_match_returns_only_that_style(client):
    response = client.get("/api/cases/", params={"style": "荷兰景风格"})
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert all(item["style"] == "荷兰景风格" for item in items)


def test_filter_style_case_insensitive(client):
    response = client.get("/api/cases/", params={"style": "ada自然风格"})
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert items[0]["style"] == "ADA自然风格"


def test_filter_style_strips_whitespace(client):
    response = client.get("/api/cases/", params={"style": " 荷兰景风格 "})
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_filter_no_match_returns_empty_list(client):
    response = client.get("/api/cases/", params={"style": "自然风"})
    assert response.status_code == 200
    assert response.json() == []


def test_filter_empty_string_treated_as_no_filter(client):
    response = client.get("/api/cases/", params={"style": ""})
    assert response.status_code == 200
    assert len(response.json()) == 5


def test_filter_difficulty_match(client):
    response = client.get("/api/cases/", params={"difficulty": "简单"})
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert all(item["difficulty"] == "简单" for item in items)


def test_create_keeps_existing_visible_and_avoids_id_collision(client):
    response = client.post("/api/cases/", json=make_case_payload())
    assert response.status_code == 200
    created = response.json()
    assert created["id"] not in range(1, 6)

    items = client.get("/api/cases/").json()
    assert len(items) == 6
    assert created["id"] in [item["id"] for item in items]

    first = client.get("/api/cases/1").json()
    assert first["title"] == "幽林秘境 - 60cm ADA自然造景"


def test_detail_update_delete_consistent_for_seed_record(client):
    detail = client.get("/api/cases/3")
    assert detail.status_code == 200
    assert detail.json()["style"] == "荷兰景风格"

    updated = client.put(
        "/api/cases/3", json=make_case_payload(title="改名案例", style="荷兰景风格")
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "改名案例"

    deleted = client.delete("/api/cases/3")
    assert deleted.status_code == 200

    gone = client.get("/api/cases/3")
    assert gone.status_code == 404
    assert gone.json()["detail"] == "Case study not found"


def test_missing_case_404_wording(client):
    for method in ("get", "delete"):
        response = getattr(client, method)("/api/cases/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Case study not found"
    response = client.put("/api/cases/999", json=make_case_payload())
    assert response.status_code == 404
    assert response.json()["detail"] == "Case study not found"


def test_non_integer_id_still_422(client):
    response = client.get("/api/cases/abc")
    assert response.status_code == 422


def test_styles_sync_with_actual_values(client):
    client.post("/api/cases/", json=make_case_payload(style="自然风"))
    styles = client.get("/api/cases/styles").json()
    assert "自然风" in styles
    for style in BUILTIN_STYLES:
        assert style in styles


def test_new_style_record_is_filterable(client):
    client.post("/api/cases/", json=make_case_payload(style="自然风"))
    items = client.get("/api/cases/", params={"style": "自然风"}).json()
    assert len(items) == 1
    assert items[0]["style"] == "自然风"
