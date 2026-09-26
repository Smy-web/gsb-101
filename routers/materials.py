from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Material
from schemas import MaterialCreate, MaterialResponse

router = APIRouter(prefix="/api/materials", tags=["materials"])

MOCK_MATERIALS = [
    {
        "id": 1,
        "name": "圣诞莫斯",
        "category": "苔藓",
        "description": "圣诞莫斯是造景中最常用的苔藓之一，适合附着在沉木和石材上，形成自然的绿色覆盖层。生长速度适中，对水质要求不高。",
        "image_url": "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=christmas%20moss%20aquatic%20plant%20close%20up%20green&image_size=square",
        "properties": {
            "难度": "简单",
            "光照需求": "中等",
            "CO2需求": "低",
            "生长速度": "中等",
            "适宜温度": "20-28°C"
        },
        "price": "¥30/份",
        "origin": "南美"
    },
    {
        "id": 2,
        "name": "垂泪莫斯",
        "category": "苔藓",
        "description": "垂泪莫斯具有独特的下垂生长特性，枝条细长柔软，非常适合营造瀑布般的景观效果。在造景中常用于沉木的点缀。",
        "image_url": "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=weeping%20moss%20aquatic%20plant%20hanging%20green&image_size=square",
        "properties": {
            "难度": "中等",
            "光照需求": "中等",
            "CO2需求": "中等",
            "生长速度": "较慢",
            "适宜温度": "22-26°C"
        },
        "price": "¥45/份",
        "origin": "东南亚"
    },
    {
        "id": 3,
        "name": "大三角莫斯",
        "category": "苔藓",
        "description": "大三角莫斯叶片呈三角形，形态优美，是ADA造景中的经典素材。适合大面积铺设在沉木上，形成厚实的绿色景观。",
        "image_url": "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=java%20moss%20triangle%20shape%20aquatic%20plant&image_size=square",
        "properties": {
            "难度": "简单",
            "光照需求": "低-中等",
            "CO2需求": "低",
            "生长速度": "快",
            "适宜温度": "18-30°C"
        },
        "price": "¥25/份",
        "origin": "东南亚"
    },
    {
        "id": 4,
        "name": "紫柚沉木",
        "category": "沉木",
        "description": "紫柚木密度高，质地坚硬，入水即沉，不易腐烂。天然的棕褐色纹理极具观赏价值，是ADA风格造景的首选沉木。",
        "image_url": "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=driftwood%20purple%20hardwood%20aquarium%20decoration&image_size=square",
        "properties": {
            "材质": "紫柚木",
            "密度": "高",
            "沉水速度": "即沉",
            "黄水程度": "轻微",
            "适合缸体": "60cm以上"
        },
        "price": "¥80-¥200",
        "origin": "东南亚"
    },
    {
        "id": 5,
        "name": "杜鹃根",
        "category": "沉木",
        "description": "杜鹃根造型奇特，枝条纤细优美，非常适合营造自然森林的感觉。使用前需要充分浸泡去除单宁酸。",
        "image_url": "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=azalea%20root%20driftwood%20aquarium%20decoration&image_size=square",
        "properties": {
            "材质": "杜鹃根",
            "密度": "中等",
            "沉水速度": "需浸泡",
            "黄水程度": "中等",
            "适合缸体": "45cm以上"
        },
        "price": "¥50-¥150",
        "origin": "中国"
    },
    {
        "id": 6,
        "name": "珊瑚沉木",
        "category": "沉木",
        "description": "珊瑚沉木表面凹凸不平，形态如珊瑚礁，具有独特的视觉效果。适合营造岩洞、礁石等造景主题。",
        "image_url": "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=coral%20driftwood%20aquarium%20ornament%20texture&image_size=square",
        "properties": {
            "材质": "风化木",
            "密度": "高",
            "沉水速度": "即沉",
            "黄水程度": "低",
            "适合缸体": "30cm以上"
        },
        "price": "¥60-¥180",
        "origin": "非洲"
    },
    {
        "id": 7,
        "name": "火焰莫斯",
        "category": "苔藓",
        "description": "火焰莫斯向上生长，形态如燃烧的火焰，色彩翠绿鲜艳，是造景中的亮点素材，适合作为中景点缀。",
        "image_url": "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=flame%20moss%20aquatic%20plant%20fire%20shape&image_size=square",
        "properties": {
            "难度": "中等",
            "光照需求": "高",
            "CO2需求": "中等",
            "生长速度": "中等",
            "适宜温度": "22-28°C"
        },
        "price": "¥50/份",
        "origin": "南美"
    },
    {
        "id": 8,
        "name": "ADA水草泥",
        "category": "底床",
        "description": "日本ADA出品的专业水草泥，富含营养元素，能够长期稳定提供水草生长所需的养分，是专业造景的首选底床材料。",
        "image_url": "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=aquarium%20soil%20substrate%20ada%20aquasoil&image_size=square",
        "properties": {
            "类型": "水草泥",
            "颗粒大小": "2-3mm",
            "肥力": "高",
            "PH值": "6.0-6.5",
            "使用寿命": "1-2年"
        },
        "price": "¥180/9L",
        "origin": "日本"
    }
]

BUILTIN_CATEGORIES = ["苔藓", "沉木", "底床", "石材", "水草", "设备"]


def _ensure_seeded(db: Session):
    if db.query(Material).count() == 0:
        db.add_all([Material(**item) for item in MOCK_MATERIALS])
        db.commit()


def _normalize_filter(value):
    if value is None:
        return None
    value = value.strip()
    return value or None


@router.get("/", response_model=List[MaterialResponse])
def get_materials(category: str = None, db: Session = Depends(get_db)):
    _ensure_seeded(db)
    query = db.query(Material)
    category = _normalize_filter(category)
    if category is not None:
        query = query.filter(func.lower(func.trim(Material.category)) == category.lower())
    return query.order_by(Material.id).all()


@router.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    _ensure_seeded(db)
    stored = {row[0] for row in db.query(Material.category).distinct() if row[0]}
    extras = sorted(stored - set(BUILTIN_CATEGORIES))
    return BUILTIN_CATEGORIES + extras


@router.get("/{material_id}", response_model=MaterialResponse)
def get_material(material_id: int, db: Session = Depends(get_db)):
    _ensure_seeded(db)
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    return material


@router.post("/", response_model=MaterialResponse)
def create_material(material: MaterialCreate, db: Session = Depends(get_db)):
    _ensure_seeded(db)
    db_material = Material(**material.model_dump())
    db.add(db_material)
    db.commit()
    db.refresh(db_material)
    return db_material

@router.put("/{material_id}", response_model=MaterialResponse)
def update_material(material_id: int, material: MaterialCreate, db: Session = Depends(get_db)):
    _ensure_seeded(db)
    db_material = db.query(Material).filter(Material.id == material_id).first()
    if not db_material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    for key, value in material.model_dump().items():
        setattr(db_material, key, value)
    
    db.commit()
    db.refresh(db_material)
    return db_material

@router.delete("/{material_id}")
def delete_material(material_id: int, db: Session = Depends(get_db)):
    _ensure_seeded(db)
    db_material = db.query(Material).filter(Material.id == material_id).first()
    if not db_material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    db.delete(db_material)
    db.commit()
    return {"message": "Material deleted successfully"}
