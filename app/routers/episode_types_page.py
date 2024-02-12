from app.connection_to_postgre.models import episode_type_alchemy
from fastapi import Depends
from fastapi import APIRouter
from sqlalchemy.orm import Session  # type: ignore
# from ..connection_to_postgre import crud, schemas_sql_alchemy
# from ..dependencies import verify_cookie
from app.connection_to_postgre import crud, schemas_sql_alchemy
from app.dependencies import verify_cookie
from app.SessionFactory import get_db

episode_types_router = APIRouter(
    tags=["episode_types"],
    dependencies=[Depends(verify_cookie)],
    responses={404: {"description": "Not found"}},
)


@episode_types_router.post("/CreateEpisodeT/")
async def create_episode_type(
        episode_type: schemas_sql_alchemy.EpisodesTypeC,
        db: Session = Depends(get_db)):
    return crud.create_episode_type(db=db, episode_type_pydantic=episode_type)


@episode_types_router.delete("/DeleteEpisodeT/{episode_type_id}")
async def delete_episode_type(
        episode_type_id: int,
        db: Session = Depends(get_db)
):
    return crud.delete_episode_type(db=db, episode_type_id=episode_type_id)


@episode_types_router.get("/GetEpisodesT", response_model=list[schemas_sql_alchemy.EpisodesType])
async def get_episode_types(
        db: Session = Depends(get_db)
):
    episode_types: list[episode_type_alchemy] = crud.get_episode_types(db)
    return episode_types
