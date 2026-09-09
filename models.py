from pydantic import BaseModel

class CreateAccount(BaseModel):
    name:str
    email:str
    password:str