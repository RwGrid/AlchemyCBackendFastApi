from app.connection_to_postgre.models import graphic_alchemy
from fastapi import Depends
from fastapi import APIRouter
from sqlalchemy.orm import Session  # type: ignore
from app.connection_to_postgre import crud, schemas_sql_alchemy
from app.dependencies import verify_cookie
from app.SessionFactory import get_db

graphic_router = APIRouter(
    tags=["graphic"],
    dependencies=[Depends(verify_cookie)],
    responses={404: {"description": "Not found"}},
)


@graphic_router.post("/CreateGraphic/")
async def create_graphic(
        graphic: schemas_sql_alchemy.GraphicC,
        db: Session = Depends(get_db)):
    return crud.create_graphic(db=db, graphic_pydantic=graphic)


@graphic_router.delete("/DeleteGraphic/{graphic_id}")
async def delete_graphic(
        graphic_id: int,
        db: Session = Depends(get_db)
):
    return crud.delete_graphic(db=db, graphic_id=graphic_id)


@graphic_router.get("/GetGraphic", response_model=list[schemas_sql_alchemy.Graphic])
async def get_graphic(
        db: Session = Depends(get_db)
):
    graphic_personnel: list[graphic_alchemy] = crud.get_graphic(db)
    return graphic_personnel
