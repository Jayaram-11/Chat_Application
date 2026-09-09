import logging
import re
import bcrypt
from email_validator import validate_email,EmailNotValidError
from database import insert_user,check_user_exists,fetch_hashed_password

def email_validator(email: str):
    try:
        is_email_valid = validate_email(email,check_deliverability=False)
        if is_email_valid:
            return True
        return False

    except EmailNotValidError as e:
        logging.info("Email not valid")
        return False


def validate_password(password: str)->bool:
    if re.match(r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*])(A-za-z\d!@#$%^&*){5,}$",password):
        return True
    return False

def email_password_validation(email:str,password:str)->bool:
    return validate_email(email) and validate_password(password)

def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"),bcrypt.gensalt())

def check_password(password, hashed_password):
    return bcrypt.checkpw(password.encode("utf-8"),hashed_password)

def validate_account(email:str,name:str,password:str)->bool:

    hashed_password=hash_password(password)
    success=insert_user(email,name,hashed_password)
    return success


def validate_login(email:str,password:str)->bool:
    valid_email=check_user_exists(email)
    if not valid_email:
        return False
    hashed_password = fetch_hashed_password(email)
    valid_password=check_password(password, hashed_password)
    if not valid_password:
        return False
    return True

