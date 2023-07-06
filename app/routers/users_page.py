import json
from typing import List

from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse

from app.connection_to_postgre.models import users
from fastapi import APIRouter, Depends, HTTPException
from fastapi import Request, Cookie, APIRouter
from sqlalchemy.orm import Session  # type: ignore
from app.connection_to_postgre.schemas_sql_alchemy import Users, UsersSchema
from app.connection_to_postgre import crud
from app.dependencies import verify_cookie
from app.SessionFactory import get_db

# the 'tags' in the router are important for-> These "tags" are especially useful for the automatic interactive
# documentation systems
users_router = APIRouter(
    tags=["user"],
    dependencies=[Depends(verify_cookie)],
    responses={404: {"description": "Not found"}},
)



@users_router.post("/CreateUser")
async def create_user(request: Request, db: Session = Depends(get_db), ):
    user_object_req = await request.json()
    status_response = crud.create_user(db, user_object_req)
    return status_response


@users_router.get("/GetUsers", response_model=List[UsersSchema])
async def get_users(db: Session = Depends(get_db)):
    # db_users: users = crud.get_all_users(db)
    db_users: users = crud.get_users_with_roles(db)
    return db_users
# @users_router.get("/GetUsers", response_model=List[Users])
# async def get_users(db: Session = Depends(get_db)):
#     db_users: users = crud.get_all_users(db)
#     return db_users

@users_router.delete("/DeleteUser/{user_id}")
def delete_host(user_id: int, db: Session = Depends(get_db), access_token: dict = Depends(verify_cookie)):
    token: dict = json.loads(access_token.body)
    return crud.delete_user(db=db, user_id=user_id, username_from_cookie=token['user'])


@users_router.get("/GetUser/{user_id}", response_model=Users)
async def get_user_by_id(
        user_id: int,
        db: Session = Depends(get_db)
):
    db_users: dict = crud.get_user(db, user_id)
    json_compatible_item_data = jsonable_encoder(db_users)
    return JSONResponse(content=json_compatible_item_data)


@users_router.get("/GetUserByN/")
async def get_user_by_n(db: Session = Depends(get_db),
                        access_token: dict = Depends(verify_cookie),
                        ):
    token = json.loads(access_token.body)
    db_users = crud.get_user_by_name(db, token["user"])
    json_compatible_item_data = jsonable_encoder(db_users)
    return JSONResponse(content=json_compatible_item_data)


@users_router.post("/update_user/{user_id}")
async def update_user(
        user_id: int,
        request: Request,
        db: Session = Depends(get_db)
):
    user_object_update: dict = await request.json()
    operation_result = crud.update_user(db, user_id, user_object_update)
    return operation_result
