from ast import keyword

from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import Session

from .database import Base


class Keyword(Base):
    __tablename__ = "keywords"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String, unique=True)
    count = Column(Integer, default=1)

    def __str__(self):
        return self.keyword


def create_keyword_or_increase(db: Session, keyword: str):
    db_keyword = db.query(Keyword).filter(Keyword.keyword == keyword).first()

    if db_keyword:
        db_keyword.count += 1
    else:
        db_keyword = Keyword(keyword=keyword)

    db.add(db_keyword)
    db.commit()
    return db_keyword


def get_keyword_count(db: Session, keyword: str) -> int:
    db_keyword = db.query(Keyword).filter(Keyword.keyword == keyword).first()
    return db_keyword.count if db_keyword else 0


def get_keywords(db: Session):
    return db.query(Keyword).all()


def get_top_keywords(db: Session, offset: int = 5):
    return db.query(Keyword).order_by(Keyword.count.desc()).limit(offset).all()
