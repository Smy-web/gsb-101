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
    engine = create_engine(
        f"sqlite:///{tmp_path}/test.db",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    app = FastAPI()
    app.include_router(materials_router)
    app.include_router(cases_router)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


NEW_MATERIAL = {
    "name": "测试莫斯",
    "category": "苔藓",
    "description": "测试用素材，不请求任何外链图片。",
    "image_url": "https://example.com/test-material.png",
    "properties": {"难度": "简单"},
    "price": "¥10/份",
    "origin": "中国",
}

NEW_CASE = {
    "title": "测试案例 - 45cm造景",
    "style": "自然风",
    "description": "测试用案例，不请求任何外链图片。",
    "thumbnail_url": "https://example.com/test-case.png",
    "gallery_urls": [],
    "materials_used": ["杜鹃根"],
    "plants": ["莫斯"],
    "difficulty": "简单",
    "tank_size": "45cm × 30cm × 30cm",
}
