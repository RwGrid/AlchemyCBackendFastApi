from http.client import HTTPException
from typing import Optional
from fastapi import Request, Cookie, APIRouter
from starlette.responses import JSONResponse
from app.connection_to_postgre.auth import AuthHandler
from app.connection_to_postgre.database import AlchemySession

# from app.connection_to_postgre.database import SessionLocal, engine

auth_handler: AuthHandler = AuthHandler()


# SessionLocal = AlchemySession().get_session()

async def verify_cookie(access_token: Optional[str] = Cookie(None)):
    # https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-in-path-operation-decorators/
    if access_token is not None:
        token = access_token.replace('Bearer', '').strip('').replace(' ', '')
        res: dict = auth_handler.decode_token(token)
        if res['status_code'] == '401':
            raise HTTPException(status_code=401, detail='cookie is dead, long live a new one')
        response = JSONResponse(content={'token': 'good', 'user': res['user']})
        return response
    else:
        raise HTTPException(status_code=401, detail='no cookie given')
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     except Exception:
#         db.rollback()
#         raise
#     else:
#         db.commit()
#     finally:
#         db.close()
