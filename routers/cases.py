from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from database import get_db
from models import CaseStudy
from schemas import CaseStudyCreate, CaseStudyResponse

router = APIRouter(prefix="/api/cases", tags=["cases"])

BUILTIN_STYLES = ["ADA自然风格", "Iwagumi石景风格", "荷兰景风格", "凹形构图风格", "凸形构图风格", "中式山水风格"]

MOCK_CASES = [
    {
        "id": 1,
        "title": "幽林秘境 - 60cm ADA自然造景",
        "style": "ADA自然风格",
        "description": "以紫柚沉木为主景，搭配圣诞莫斯和垂泪莫斯，营造幽深的水下森林景观。采用经典的黄金分割构图，前低后高的底床坡度创造出强烈的视觉纵深感。",
        "thumbnail_url": "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=ada%20aquascape%20nature%20aquarium%2060cm%20forest%20style%20driftwood%20moss&image_size=landscape_16_9",
        "gallery_urls": [
            "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=aquascape%20full%20view%20planted%20tank%20beautiful&image_size=landscape_16_9",
            "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=aquarium%20driftwood%20moss%20close%20up%20detail&image_size=landscape_16_9",
            "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=aquatic%20plants%20carpet%20foreground%20aquascape&image_size=landscape_16_9"
        ],
        "materials_used": ["紫柚沉木", "ADA水草泥", "青龙石", "圣诞莫斯", "垂泪莫斯"],
        "plants": ["迷你矮珍珠", "宫廷草", "水榕", "黑木蕨", "细叶铁"],
        "difficulty": "中等",
        "tank_size": "60cm × 30cm × 36cm",
        "created_at": "2024-01-15T10:30:00"
    },
    {
        "id": 2,
        "title": "山谷回响 - 90cm石景造景",
        "style": "Iwagumi石景风格",
        "description": "以青龙石构建山谷造型，三块主石呈现经典的三石构图。前景种植迷你牛毛毡，后景搭配大型水草，营造开阔的山谷空间感。",
        "thumbnail_url": "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=iwagumi%20style%20aquascape%20stone%20layout%2090cm%20valley&image_size=landscape_16_9",
        "gallery_urls": [
            "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=aquascape%20stone%20mountain%20valley%20layout&image_size=landscape_16_9",
            "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=seiryu%20stone%20aquarium%20arrangement%20detail&image_size=landscape_16_9"
        ],
        "materials_used": ["青龙石", "ADA水草泥", "化妆沙"],
        "plants": ["迷你牛毛毡", "箦藻", "百叶草", "红蝴蝶"],
        "difficulty": "困难",
        "tank_size": "90cm × 45cm × 45cm",
        "created_at": "2024-02-20T14:00:00"
    },
    {
        "id": 3,
        "title": "热带雨林 - 45cm小型造景",
        "style": "荷兰景风格",
        "description": "为小型水族箱设计的雨林风格造景，多种水草层次分明，色彩丰富。适合放置在桌面或书房，成为空间中的一抹绿意。",
        "thumbnail_url": "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=dutch%20style%20aquascape%2045cm%20small%20tank%20colorful%20plants&image_size=landscape_16_9",
        "gallery_urls": [
            "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=small%20aquarium%20planted%20tank%20desktop&image_size=landscape_16_9",
            "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=colorful%20aquatic%20plants%20arrangement%20dutch%20style&image_size=landscape_16_9"
        ],
        "materials_used": ["杜鹃根", "ADA水草泥", "火山石"],
        "plants": ["莫斯", "水榕", "辣椒榕", "小水兰", "绿菊"],
        "difficulty": "简单",
        "tank_size": "45cm × 30cm × 30cm",
        "created_at": "2024-03-10T09:15:00"
    },
    {
        "id": 4,
        "title": "珊瑚礁梦 - 120cm大型造景",
        "style": "凹形构图风格",
        "description": "120cm大型水族箱，采用凹形构图，两侧高耸的沉木和水草形成拱门效果，中间留出开阔的游动空间。适合饲养中小型灯鱼群。",
        "thumbnail_url": "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=concave%20style%20aquascape%20120cm%20large%20tank%20archway&image_size=landscape_16_9",
        "gallery_urls": [
            "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=large%20aquarium%20120cm%20planted%20tank%20school%20of%20fish&image_size=landscape_16_9",
            "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=aquascape%20archway%20driftwood%20plants&image_size=landscape_16_9"
        ],
        "materials_used": ["珊瑚沉木", "ADA水草泥", "松皮石"],
        "plants": ["大三角莫斯", "水兰", "珍珠草", "红宫廷", "绿宫廷"],
        "difficulty": "中等",
        "tank_size": "120cm × 50cm × 50cm",
        "created_at": "2024-04-05T16:45:00"
    },
    {
        "id": 5,
        "title": "东方意境 - 75cm山水造景",
        "style": "中式山水风格",
        "description": "借鉴中国传统山水画的构图理念，用石材和沉木营造远山近水的意境。留白得当，意境深远，体现东方美学的韵味。",
        "thumbnail_url": "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=chinese%20landscape%20style%20aquascape%2075cm%20zen%20garden&image_size=landscape_16_9",
        "gallery_urls": [
            "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=zen%20aquarium%20mountain%20water%20style&image_size=landscape_16_9",
            "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=minimalist%20aquascape%20asian%20style&image_size=landscape_16_9"
        ],
        "materials_used": ["龟纹石", "ADA水草泥", "化妆沙", "紫柚沉木"],
        "plants": ["火焰莫斯", "凤尾苔", "水榕", "细叶铁皇冠"],
        "difficulty": "中等",
        "tank_size": "75cm × 40cm × 40cm",
        "created_at": "2024-05-12T11:30:00"
    }
]

def _ensure_seeded(db: Session) -> None:
    if db.query(CaseStudy).count() > 0:
        return
    for item in MOCK_CASES:
        data = dict(item)
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        db.add(CaseStudy(**data))
    db.commit()


def _normalize(value: str) -> str:
    return value.strip().lower()


@router.get("/", response_model=List[CaseStudyResponse])
def get_cases(style: str = None, difficulty: str = None, db: Session = Depends(get_db)):
    _ensure_seeded(db)
    query = db.query(CaseStudy)
    if style is not None and style.strip():
        query = query.filter(func.lower(CaseStudy.style) == _normalize(style))
    if difficulty is not None and difficulty.strip():
        query = query.filter(func.lower(CaseStudy.difficulty) == _normalize(difficulty))
    return query.order_by(CaseStudy.id).all()

@router.get("/styles")
def get_styles(db: Session = Depends(get_db)):
    _ensure_seeded(db)
    values = {row[0] for row in db.query(CaseStudy.style).distinct() if row[0]}
    extras = sorted(value for value in values if value not in BUILTIN_STYLES)
    return BUILTIN_STYLES + extras

@router.get("/{case_id}", response_model=CaseStudyResponse)
def get_case(case_id: int, db: Session = Depends(get_db)):
    _ensure_seeded(db)
    case = db.query(CaseStudy).filter(CaseStudy.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case study not found")
    return case

@router.post("/", response_model=CaseStudyResponse)
def create_case(case: CaseStudyCreate, db: Session = Depends(get_db)):
    _ensure_seeded(db)
    db_case = CaseStudy(**case.model_dump())
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    return db_case

@router.put("/{case_id}", response_model=CaseStudyResponse)
def update_case(case_id: int, case: CaseStudyCreate, db: Session = Depends(get_db)):
    _ensure_seeded(db)
    db_case = db.query(CaseStudy).filter(CaseStudy.id == case_id).first()
    if not db_case:
        raise HTTPException(status_code=404, detail="Case study not found")

    for key, value in case.model_dump().items():
        setattr(db_case, key, value)

    db.commit()
    db.refresh(db_case)
    return db_case

@router.delete("/{case_id}")
def delete_case(case_id: int, db: Session = Depends(get_db)):
    _ensure_seeded(db)
    db_case = db.query(CaseStudy).filter(CaseStudy.id == case_id).first()
    if not db_case:
        raise HTTPException(status_code=404, detail="Case study not found")

    db.delete(db_case)
    db.commit()
    return {"message": "Case study deleted successfully"}
