import jwt
# jwt can be used by installing pyjwt
from fastapi import HTTPException, Security

from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# the 'HTTPException' will be used to raise invalid exception in case of invalid bearer token by using the status
# code and the error  message 'Security' will be used a dependency injection library and will highlight routes that
# required authorization header, provide a way to enter a bearer there 'HTTPBearer' will be used as part of the
# dependency injection to ensure a valid auth header has been provided when calling the endpoint
# 'HTTPAuthorizationCredentials' will be the type returned from the dependency injection

from passlib.context import CryptContext
# the "passlib.context" will be used to hash the passwords

from datetime import datetime, timedelta

# "datetime" and "timedelta" will be used to set the time range for the authenticity of the token
from starlette.responses import JSONResponse


class AuthHandler():
    security = HTTPBearer()
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    secret = 'MYSECALFxc2f'

    def get_password_hash(self, password):
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password, hashed_password):
        return self.pwd_context.verify(plain_password, hashed_password)

    def encode_token(self, user_id):
        payload = {
            'exp': datetime.utcnow() + timedelta(days=2, minutes=0),
            'iat': datetime.utcnow(),
            'sub': user_id
        }
        # the 'exp' is the expiry date of the bearer jwt token, expiry time in test is 5 minutes
        # we encode our token with a 'secret' field, which is the 'key' for the AES256 algo
        # 'iat' is 'issued at time'
        # The 'sub' (subject) property contains the unique user identifier of the user who signed in.
        # We'll extract that and store it in the session, which will indicate to our app that the user is signed in.
        return jwt.encode(payload, self.secret, algorithm='HS256')

    def decode_token(self, token):
        try:
            payload = jwt.decode(token, self.secret, algorithms=['HS256'])
            return {"status_code": "200", 'user': payload['sub']}
        except jwt.ExpiredSignatureError:
            return {"status_code": "401", 'detail': 'Signature has expired'}
            # raise HTTPException(status_code=401, detail='Signature has expired')
        except jwt.InvalidTokenError as e:
            return {"status_code": "401", 'detail': 'Invalid Token'}
            # raise HTTPException(status_code=401, detail='Invalid Token')

    # the final function is the dependency injection wrapper for our code, where any route,will need to pass the
    # 'authorization bearer' in the http request
    # here i must make the auth wrapper accept from the request, to get the request cookie and decode it instead of now ,now it gets from the authorization header
    # solution : https://github.com/tiangolo/fastapi/issues/480
    def auth_cookie_wrapper(self, request):
        cookie_authorization: str = request.cookies.get("access_token")
        if cookie_authorization != None:
            x = cookie_authorization.replace('Bearer', '').strip('').replace(' ', '')

            res = self.decode_token(x)
            response = JSONResponse(content={'token': 'good','user':res['sub']})
            return response

    def auth_wrapper(self, auth: HTTPAuthorizationCredentials = Security(security)):
        return self.decode_token(auth.credentials)
