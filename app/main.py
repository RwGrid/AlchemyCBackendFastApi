import ujson
from fastapi.encoders import jsonable_encoder
# test youtube https://www.youtube.com/watch?v=aTYc_MML9Gs
from connection_to_postgre import crud, models, schemas_sql_alchemy
from connection_to_postgre.auth import AuthHandler
from connection_to_postgre.schemas_sql_alchemy import (
    AuthDetails,
    VisibleTabsC,

)
from SessionFactory import session_maker, get_db, engine

import datetime
import json
import ujson
import logging
from typing import Optional, List
from fastapi import Request, Cookie, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from starlette import status
from starlette.responses import JSONResponse
from fastapi import Depends, FastAPI, HTTPException, Response
from sqlalchemy.orm import Session  # type: ignore

# connect to postgres database with pydantic models
from elasticapm.contrib.starlette import make_apm_client, ElasticAPM
from connection_to_postgre.crud import get_user_display_name
from connection_to_postgre.models import (

    visible_tabs,
)
# from .connection_to_postgre import database
# from .connection_to_postgre.database import AlchemySession
# from .routers.TasksPages import tasks_router
# from .routers.episode_types_page import episode_types_router
# from .routers.guest_page import guests_router
# from .routers.hosts_page import hosts_router
# from .routers.insert_episodes_page import insert_episodes_router
# from .routers.manage_episodes_page import manage_episodes_router
# from .routers.program_page import program_router
# from .routers.roles_page import roles_router
# from .routers.users_page import users_router
# from .routers.graphic_page import graphic_router
# from .routers.editor_page import editor_router
# from .routers.actions_page import action_router
# from .routers.comments_page import comments_dashboard_router, comments_dashboard_router_experimenting
# from .connection_to_postgre import database
from connection_to_postgre.database import AlchemySession
from routers.TasksPages import tasks_router
from routers.episode_types_page import episode_types_router
from routers.guest_page import guests_router
from routers.hosts_page import hosts_router
from routers.insert_episodes_page import insert_episodes_router
from routers.manage_episodes_page import manage_episodes_router
from routers.program_page import program_router
from routers.roles_page import roles_router
from routers.users_page import users_router
from routers.graphic_page import graphic_router
from routers.editor_page import editor_router
from routers.actions_page import action_router
from routers.comments_page import comments_dashboard_router, comments_dashboard_router_experimenting

# SEE SOCIAL MEDIA MONITORING APPS
# MAKE THIS CODE HERE RUN ON THE FIRST TIME ONLY
# This is a ----------------Test Code----------------
# to truly refresh, delete the database itself
# try:
#     models.Base.metadata.drop_all(bind=engine)
# except Exception as ex:
#     print(str(ex))
# testing a commit
# testing a commit 2
# This is a ----------------END Test Code----------------

try:
    models.Base.metadata.create_all(bind=engine)
except Exception as ex:
    print(str(ex))
# ----------------------------------
import os

print("inserting common data into databases")
# try:
#     cmd = "python3 /home/ali/Desktop/ExtractJsonObjFromExcel/run_all.py"
#     asdf = os.system(cmd)
#     print("inserted base data")
# except Exception as exxz:
#     pass


logging.basicConfig(
    filename="app.log",
    filemode="w",
    format="%(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,
)
logging.info("------------------ " + str(datetime.datetime.now()) + "--------------")
logging.info("Started Logging")

from elastic_session import ElasticSearchSingelton

es = ElasticSearchSingelton().es_client
print("-----------------------Testing My Code--------------------")
print("-----------------------I ENDED Testing----------------------------")
app = FastAPI()
# app = FastAPI(json_dumps=ujson.dumps, json_loads=ujson.loads)
app.include_router(insert_episodes_router)
app.include_router(manage_episodes_router)

app.include_router(program_router)
app.include_router(guests_router)
app.include_router(hosts_router)
app.include_router(episode_types_router)

# Management and Settings
app.include_router(users_router)
app.include_router(roles_router)
app.include_router(graphic_router)
app.include_router(editor_router)
app.include_router(action_router)
app.include_router(tasks_router)
app.include_router(comments_dashboard_router)
app.include_router(comments_dashboard_router_experimenting)

# app.include_router()
origins = ["*"]
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
ORIGINS_LIST = [
    "http://localhost:3000",

]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS_LIST,
    allow_credentials=True,
    allow_origin_regex="192.168.*",
    allow_methods=["GET", "POST", "OPTIONS", "DELETE", "PUT"],
    # include additional methods as per the application demand
    allow_headers=["Content-Type", "Set-Cookie"],
)

apm_config = {
    "SERVICE_NAME": "alchemy_nova_watcher",
    "SERVER_URL": "http://0.0.0.0:8200",
}
apm = make_apm_client(apm_config)
app.add_middleware(ElasticAPM, client=apm)


# from app.connection_to_postgre.database import session_maker


@app.on_event("startup")
async def startup():
    is_connected: bool = await es.ping()
    try:
        await es.indices.create(index='data_alchemy2.1')
        print("creating elastic index from the start")
    except Exception as createdException:
        print("alchemy2.1 already exists, change mapping if u didn't" + str(createdException))
    assert (is_connected) == True
    if is_connected:
        print("> You have Successfully connected to Elasticsearch Instance (--)")
    if not is_connected:
        raise ValueError("ElasticSearch Prob ,Connection failed,Wrong IP,Change from virtual machine ")
    with open('./reinitialize_super_user.json') as reinit:
        init_super: dict = json.load(reinit)
        if init_super['reinitialize'] == "true":
            initialize_master_user()


# This gets called once the app is shutting down.
@app.on_event("shutdown")
async def app_shutdown():
    logging.warning("Ended Logging The Whole App")
    session_maker.close_all()
    await es.close()


def initialize_master_user():
    with open('./role_instantiation_for_new_tabs.json') as rol_inst:
        role_object: dict = json.load(rol_inst)
    db_init = AlchemySession().get_session_only()
    db_init = db_init()
    # created initial role
    user_object: dict = {
        "user_name": "12345",
        "user_display_name": "ali",
        "user_password": "echoX",
        "roles": [{"value": "roleXF", "label": "roleXF"}],
    }
    try:
        crud.delete_master_role(db_init, "roleXF")
    except Exception as exx:
        print(str(exx) + "no role to delete in the first place")
    try:
        crud.delete_master_user(db_init, "12345")
    except Exception as exx:
        print(str(exx) + "no user to delete in the first place")

    db_init.commit()
    crud.create_role(db_init, role_object)
    db_init.commit()
    crud.create_user(db_init, user_object)
    db_init.commit()
    db_init.close()


async def verify_cookie(access_token: Optional[str] = Cookie(None)):
    # https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-in-path-operation-decorators/
    if access_token is not None:
        token = access_token.replace("Bearer", "").strip("").replace(" ", "")

        res: dict = auth_handler.decode_token(token)
        if res["status_code"] == "401":
            raise HTTPException(
                status_code=401, detail="cookie is dead, long live a new one"
            )
        response = JSONResponse(content={"token": "good", "user": res["user"]})
        return response
    else:
        raise HTTPException(status_code=401, detail="no cookie given")


authenticated = APIRouter(dependencies=[Depends(verify_cookie)])


@app.get("/")
async def read_root():
    return {"status": "Happy"}


auth_handler: AuthHandler = AuthHandler()


#  must send the token in the authorization header

# @app.post('/register', status_code=201)
# def register(auth_details: AuthDetails):
#     # here we check in the database(postgre) if there exists a user similar to the user registration name that was sent
#     if any(x['username'] == auth_details.username for x in users):
#         raise HTTPException(status_code=400, detail='Username is taken')
#     hashed_password = auth_handler.get_password_hash(auth_details.password)
#     users.append({
#         'username': auth_details.username,
#         'password': hashed_password
#     })
#     # here we must add the user into the database postgres
#     return {"status": "successfully created a user "}


# https://www.howtoforge.com/how-to-create-locally-trusted-ssl-certificates-with-mkcert-on-ubuntu/ HTTPS
# https://www.howtoforge.com/how-to-create-locally-trusted-ssl-certificates-with-mkcert-on-ubuntu/
# https://pystar.substack.com/p/how-to-create-a-fake-certificate -------------------MUST FOLLOW SECURITY tips
# :https://stackoverflow.com/questions/8064318/how-to-read-a-httponly-cookie-using-javascript----------------
@app.post("/login")
def login(request: Request, auth_details: AuthDetails, db: Session = Depends(get_db)):
    # CONFIGURE HTTPS TO KNOW UR NEXT STEP USING mckcert
    # when a user logs in , he must ofc , send the username and password, what happens
    # we will check if the username exist in our database
    # if the user exists in the database or the password is a mismatch
    # we will raise an error for the front end
    # else it will continue and create a 'bearer' token for us
    users_fetched = crud.get_all_users(db)
    user = None
    for x in users_fetched:
        if x.user_name == auth_details.user_name:
            user = x
            break
    if (user is None) or (
            not auth_handler.verify_password(auth_details.user_password, user.user_password)
    ):
        raise HTTPException(status_code=401, detail="Invalid username and/or password")
    cookie_authorization = request.cookies.get("access_token")
    if cookie_authorization is not None:
        x = cookie_authorization.replace("Bearer", "").strip("").replace(" ", "")
        res = auth_handler.decode_token(x)
        if res["status_code"] == "401":
            token = auth_handler.encode_token(user.user_name)
            response = JSONResponse(
                content={"token": "good", "user": user.user_display_name}
            )
            response.set_cookie(
                key="access_token",
                httponly=True,
                secure=True,
                samesite="none",
                value=f"Bearer {token}",
            )  # set HttpOnly cookie in response
            for idx, header in enumerate(response.raw_headers):
                if header[0].decode("utf-8") == "set-cookie":
                    cookie = header[1].decode("utf-8")
                    if "SameSite=none" not in cookie:
                        cookie = cookie + "; SameSite=none"
                        response.raw_headers[idx] = (header[0], cookie.encode())
            return response
        # if auth_details.user_name != user.user_name:
        #     token = auth_handler.encode_token(user.user_name)
        #     response = JSONResponse(
        #         content={"token": "good", "user_display": user.user_display_name, "user_name": user.user_name}
        #     )
        #     response.set_cookie(
        #         key="access_token",
        #         httponly=True,
        #         secure=True,
        #         samesite="none",
        #         value=f"Bearer {token}",
        #     )  # set HttpOnly cookie in response
        #     for idx, header in enumerate(response.raw_headers):
        #         if header[0].decode("utf-8") == "set-cookie":
        #             cookie = header[1].decode("utf-8")
        #             if "SameSite=none" not in cookie:
        #                 cookie = cookie + "; SameSite=none"
        #                 response.raw_headers[idx] = (header[0], cookie.encode())
        #     return response
        response = JSONResponse(
            content={"token": "good", "user": user.user_display_name, "user_name": user.user_name}
        )
        return response
    else:
        token = auth_handler.encode_token(user.user_name)
        response = JSONResponse(
            content={"token": "good", "user_display": user.user_display_name, "user_name": user.user_name}
        )
        response.set_cookie(
            key="access_token",
            httponly=True,
            secure=True,
            samesite="none",
            value=f"Bearer {token}",
        )  # set HttpOnly cookie in response
        for idx, header in enumerate(response.raw_headers):
            if header[0].decode("utf-8") == "set-cookie":
                cookie = header[1].decode("utf-8")
                if "SameSite=none" not in cookie:
                    cookie = cookie + "; SameSite=none"
                    response.raw_headers[idx] = (header[0], cookie.encode())
        return response


@app.get("/logout", dependencies=[Depends(verify_cookie)])
async def logout(request: Request, response: Response):
    # deleting the cookie did not work
    # we set a new cookie with 1 sec
    response: JSONResponse = JSONResponse(content={"token": "ded", "user": "none"})
    expires = datetime.datetime.utcnow() + datetime.timedelta(seconds=1)
    response.set_cookie(
        key="access_token",
        value="",
        secure=True,
        httponly=True,
        samesite="none",
        expires=expires.strftime("%a, %d %b %Y %H:%M:%S GMT"),
    )
    return response


# TO MAKE IT WORK ON KIBANA :https://discuss.elastic.co/t/csp-errors-when-using-an-kibana-iframe/246096/12
@app.get("/get_cookie")
async def get_cookie(
        request: Request,
        access_token: dict = Depends(verify_cookie),
        db: Session = Depends(get_db),
):
    try:
        # to view the cookie in the parameter u need to set the variable name, same the key of the token which is in
        # our case (access_token) this is according to the following https://github.com/tiangolo/fastapi/issues/4029
        # https://stackoverflow.com/questions/63788083/how-to-check-if-a-cookie-is-set-in-fastapi
        cookie_authorization: str = request.cookies.get("access_token")
        # now each request by default, I will make it get the cookie currently in the browser and make wrapper around
        # the cookie. so that it will be a mandatory to have the cookie (correct bearer ) in the request. so after i
        # log in, I create  the cookie, and then on each request,I check if the current cookie is expired,
        # good or whatever, if it is good, then we re-route to the rest of the website and allow each request
        token: dict = json.loads(access_token.body)
        usr: dict = get_user_display_name(db=db, user_name=token["user"])
        return {
            "status": "200",
            "message": "cookie is valid ",
            "user_display": usr["user_display_name"],
            "user_name": usr["user_name"]
        }
        # some logic with cookie_authorization
    except Exception as e:
        return {"status": "FAILED", "message": "verifying cookie failed,invalid auth"}

        # raise HTTPException(
        #     status_code=status.HTTP_403_FORBIDDEN, detail="Invalid authentication"
        # )


# raise e sqlalchemy.exc.InvalidRequestError: One or more mappers failed to initialize - can't proceed with
# initialization of other mappers. Triggering mapper: 'mapped class users->users'. Original exception was: Error
# creating backref 'users' on relationship 'users.roles': property of that name exists on mapper 'mapped class
# roles->roles'

# sqlalchemy.exc.ArgumentError: Error creating backref 'users' on relationship 'users.roles': property of that name
# exists on mapper 'mapped class roles->roles'wq
@app.post("/CreateVisibleTabs/")
async def create_tabs(request: Request, db: Session = Depends(get_db)):
    visible_tabs_req: dict = await request.json()
    for headTab, visibleTab in visible_tabs_req.items():
        for key in visibleTab.keys():
            db_tab: visible_tabs = crud.get_tab_if_exists(
                db, tab_name=visibleTab[key]["inner_value"], tab_head_name=headTab
            )
            if db_tab:
                print("tab already inserted")
                continue
            else:
                print("tab inserted successfully")
                # raise HTTPException(status_code=400, detail="tab already exists")
            tab = dict()
            tab["tab_name"] = visibleTab[key]["inner_value"]
            tab["head_tab_name"] = headTab
            tab["tab_desc"] = visibleTab[key]["desc"]
            m = VisibleTabsC(
                tab_name=tab["tab_name"],
                head_tab_name=tab["head_tab_name"],
                tab_desc=tab["tab_desc"],
            )
            crud.create_tab(db=db, visible_tab_pydantic=m)
    return {"status": "SUCCESS", "message": "inserted visible tabs"}


@app.get("/GetNotifications")
async def get_graphic(
        db: Session = Depends(get_db), access_token: dict = Depends(verify_cookie)
):
    token: dict = json.loads(access_token.body)
    current_user = crud.get_user_by_username(db=db, user_name=token["user"])
    sent_actions = crud.get_send_actions(db, current_user)
    json_compatible_item_data = jsonable_encoder(sent_actions)
    return JSONResponse(content=json_compatible_item_data)
