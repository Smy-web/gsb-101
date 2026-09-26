import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from routers.materials import router as materials_router
from routers.cases import router as cases_router


@pytest.fixture()
def client(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(materials_router)
    app.include_router(cases_router)
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client


def make_material_payload(**overrides):
    payload = {
        "name": "测试素材",
        "category": "设备",
        "description": "测试用素材描述",
        "image_url": "https://example.com/image.png",
        "properties": {"难度": "简单"},
        "price": "¥10/份",
        "origin": "中国",
    }
    payload.update(overrides)
    return payload


def make_case_payload(**overrides):
    payload = {
        "title": "测试案例",
        "style": "自然风",
        "description": "测试用案例描述",
        "thumbnail_url": "https://example.com/thumb.png",
        "gallery_urls": ["https://example.com/1.png"],
        "materials_used": ["测试素材"],
        "plants": ["测试水草"],
        "difficulty": "简单",
        "tank_size": "30cm × 30cm × 30cm",
    }
    payload.update(overrides)
    return payload
