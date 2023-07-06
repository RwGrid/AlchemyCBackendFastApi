from app.connection_to_postgre.models import program_name_alchemy
from fastapi import Depends
from fastapi import APIRouter
from sqlalchemy.orm import Session  # type: ignore
from app.connection_to_postgre import crud, schemas_sql_alchemy
from app.dependencies import verify_cookie
from app.SessionFactory import get_db

program_router = APIRouter(
    tags=["programs"],
    dependencies=[Depends(verify_cookie)],
    responses={404: {"description": "Not found"}},
)


@program_router.post("/CreateProgramN/")
async def create_program_name(
    program_name: schemas_sql_alchemy.ProgramsNameC, db: Session = Depends(get_db)
):
    """

    :param program_name:  the program name given by the user--->"morning show" str
    :param db: receives a db instance of sqlalchemy
    :param access_token: must have a decrypted valid token-->cookie jwt
    :return: SqlOpMsg the result of the operation -->{"status": "", "message":""}
    """
    # raise HTTPException(status_code=400, detail="program name already exists")
    return crud.create_program_name(db=db, program_name_pydantic=program_name)


@program_router.delete("/DeleteProgramN/{program_id}")
def delete_program(program_id: int, db: Session = Depends(get_db)):
    return crud.delete_program_name(db=db, program_id=program_id)


@program_router.get(
    "/GetProgramNs", response_model=list[schemas_sql_alchemy.ProgramsName]
)
async def get_program_names(db: Session = Depends(get_db)):
    programs: list[program_name_alchemy] = crud.get_programs_names(db)
    return programs
