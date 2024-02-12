import json
from time import sleep
from typing import List

from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse

from app.connection_to_postgre.models import users, visible_tabs
from fastapi import APIRouter, Depends, HTTPException
from fastapi import Request, Cookie, APIRouter
from sqlalchemy.orm import Session  # type: ignore
from app.connection_to_postgre.schemas_sql_alchemy import Users, Roles, VisibleTabs
from app.connection_to_postgre import crud
from app.dependencies import verify_cookie
from app.SessionFactory import get_db

# the 'tags' in the router are important for-> These "tags" are especially useful for the automatic interactive
# documentation systems
roles_router = APIRouter(
    tags=["roles"],
    dependencies=[Depends(verify_cookie)],
    responses={404: {"description": "Not found"}},
)


@roles_router.get("/get_visible_tabs", response_model=list[VisibleTabs])
async def get_visible_tabs(db: Session = Depends(get_db)):
    db_visible_tabs: visible_tabs = crud.get_all_visible_tabs_full_info(db)
    return db_visible_tabs


@roles_router.get("/GetRole/{role_id}", response_model=Roles)
async def get_role_by_id(role_id: int, db: Session = Depends(get_db)):
    db_users = crud.get_role(db, role_id)
    json_compatible_item_data = jsonable_encoder(db_users)
    return JSONResponse(content=json_compatible_item_data)


@roles_router.get("/GetRoleFull/{role_id}")
async def get_role_full(role_id: int, db: Session = Depends(get_db)):
    db_role = crud.get_full_role(db, role_id)
    return db_role


@roles_router.get("/GetRoles", response_model=List[Roles])
async def get_roles_all(db: Session = Depends(get_db)):
    db_roles = crud.get_all_roles(db)
    return db_roles


@roles_router.delete("/DeleteRole/{role_id}")
def delete_host(
    role_id: int,
    db: Session = Depends(get_db),
):
    return crud.delete_role(db=db, role_id=role_id)


@roles_router.post("/CreateRole")
async def create_role(
    request: Request,
    db: Session = Depends(get_db),
):
    role_object_req = await request.json()
    creating_role_msg = crud.create_role(db, role_object_req)
    return creating_role_msg


@roles_router.post("/UpdateRole/{role_id}")
async def update_role(
    role_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    # I must give the newly created role , the list  of the old users
    role_object_req = await request.json()
    crud.update_role(db,role_object_req,role_id)
    # crud.delete_role(db, role_id)
    # sleep(0.2)
    # crud.create_role(db, role_object_req)
    return {"status": "SUCCESS", "message": "Updated Successfully"}
