import datetime
import uuid

import jwt
import os
import logging
from dotenv import load_dotenv
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from database import fetch_name,fetch_userID

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")



def encode_jwt(email):
    uid=fetch_userID(email)
    name=fetch_name(email)
    exp=datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(days=5)
    payload={
        "uid":uid,
        "name":name,
        "exp":exp
    }
    return jwt.encode(payload,SECRET_KEY,algorithm="HS256")

def decode_jwt(token:str =Depends(oauth2_scheme)):
    try:
        decoded_payload=jwt.decode(token,SECRET_KEY,algorithms=["HS256"])
        return decoded_payload
    except jwt.ExpiredSignatureError:
        logger.error("Expired token")
        return None
    except jwt.InvalidTokenError:
        logger.error("Invalid token")
        return None

# call this in Webscoket
def decode_jwt_raw(token:str):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=["HS256"]
        )
        return payload

    except jwt.ExpiredSignatureError:
        return None

    except jwt.InvalidTokenError:
        return None