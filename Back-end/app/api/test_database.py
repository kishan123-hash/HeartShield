from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database.database import get_db

__test__ = False


router = APIRouter(
    prefix="/database",
    tags=["Database"]
)


@router.get("/test")
def test_database(
    db: Session = Depends(get_db)
):

    result = db.execute(
        text("SELECT 1")
    )

    return {
        "database": result.scalar()
    }