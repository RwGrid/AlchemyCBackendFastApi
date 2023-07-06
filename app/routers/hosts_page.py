from app.connection_to_postgre.models import  host_names_alchemy
from fastapi import  Depends
from fastapi import APIRouter
from sqlalchemy.orm import Session  # type: ignore
# from ..connection_to_postgre import crud, schemas_sql_alchemy
# from ..dependencies import verify_cookie
from app.connection_to_postgre import crud, schemas_sql_alchemy
from app.dependencies import verify_cookie
from app.SessionFactory import get_db

hosts_router = APIRouter(
    tags=["hosts"],
    dependencies=[Depends(verify_cookie)],
    responses={404: {"description": "Not found"}},
)


# -------------------host-----------------------


@hosts_router.post("/CreateHost")
async def create_host(
        host: schemas_sql_alchemy.HostsBaseC,
        db: Session = Depends(get_db),
):
    db_host: host_names_alchemy = crud.get_host_name_if_exists(
        db, host_name=host.host_name
    )

    if db_host:
        return {"status": "WARNING", "message": "Record Exists"}
        # raise HTTPException(status_code=400, detail="host name already exists")
    # add a log that I created a new hostname
    operation_msg = crud.create_host_names(db=db, host_names_pydantic=host)
    return operation_msg


@hosts_router.delete("/DeleteHost/{host_id}")
async def delete_host(host_id: int, db: Session = Depends(get_db)):
    return crud.delete_host(db=db, host_id=host_id)


@hosts_router.get(
    "/GetHosts",
    response_model=list[schemas_sql_alchemy.Hosts],
)
async def get_hosts(db: Session = Depends(get_db)):
    hosts: host_names_alchemy = crud.get_hosts(db)
    return hosts
