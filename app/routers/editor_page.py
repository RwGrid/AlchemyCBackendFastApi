from app.connection_to_postgre.models import editor_alchemy
from fastapi import Depends
from fastapi import APIRouter
from sqlalchemy.orm import Session  # type: ignore
from app.connection_to_postgre import crud, schemas_sql_alchemy
from app.dependencies import verify_cookie
from app.SessionFactory import get_db

editor_router = APIRouter(
    tags=["editor"],
    dependencies=[Depends(verify_cookie)],
    responses={404: {"description": "Not found"}},
)


@editor_router.post("/CreateEditor/")
async def create_graphic(
        editor: schemas_sql_alchemy.EditorC,
        db: Session = Depends(get_db)):
    return crud.create_editor(db=db, editor_pydantic=editor)


@editor_router.delete("/DeleteEditor/{editor_id}")
async def delete_graphic(
        editor_id: int,
        db: Session = Depends(get_db)
):
    return crud.delete_editor(db=db, editor_id=editor_id)


@editor_router.get("/GetEditor", response_model=list[schemas_sql_alchemy.Editor])
async def get_graphic(
        db: Session = Depends(get_db)
):
    editor_personnel: list[editor_alchemy] = crud.get_editor(db)
    return editor_personnel
