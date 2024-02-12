from app.connection_to_postgre.models import editor_alchemy
from fastapi import Depends
from fastapi import APIRouter
from sqlalchemy.orm import Session  # type: ignore
from app.connection_to_postgre import crud, schemas_sql_alchemy
from app.dependencies import verify_cookie
from app.SessionFactory import get_db

action_router = APIRouter(
    tags=["action"],
    dependencies=[Depends(verify_cookie)],
    responses={404: {"description": "Not found"}},
)


@action_router.post("/CreateAction")
async def create_graphic(
        action: schemas_sql_alchemy.UserActionC,
        db: Session = Depends(get_db)):
    return crud.create_action(db=db, action_pydantic=action)


@action_router.delete("/DeleteAction/{action_id}")
async def delete_graphic(
        action_id: int,
        db: Session = Depends(get_db)
):
    return crud.delete_action(db=db, action_id=action_id)


@action_router.get("/GetAction", response_model=list[schemas_sql_alchemy.UserAction])
async def get_graphic(
        db: Session = Depends(get_db)
):
    actions = crud.get_action(db)
    return actions
