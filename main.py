import logging
from fastapi import FastAPI, HTTPException, status,Depends
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse
from starlette.websockets import WebSocket, WebSocketDisconnect

from models import CreateAccount
from validation import validate_account,validate_login,email_password_validation,validate_room_name
from database import fetch_room_id,save_message,get_messages,insert_room
from security import encode_jwt,decode_jwt
app = FastAPI()

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:8000/chat");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


@app.get("/",status_code=status.HTTP_200_OK)
def health_check():
    return HTMLResponse(html)



@app.post("/create-account",status_code=status.HTTP_201_CREATED)
async def create_account(data: CreateAccount):
    email = data.email
    password = data.password
    name=data.name
    valid_data = email_password_validation(email,password)
    if not valid_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success":False,
                "error":{
                    "code":"INCORRECT_FORMAT",
                    "message":"Email or password is not in correct format"
                }
            }
        )
    success= validate_account(email,name,password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "success":False,
                "error":{
                    "code":"USER_EXIST",
                    "message":"User already exists"
                }
            }
        )
    return {
        "success":True,
        "data":{
            "name":name,
        },
        "message":"User created successfully"
    }


@app.post("/login",status_code=status.HTTP_201_CREATED)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    email = form_data.username
    password = form_data.password
    success=validate_login(email,password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success":False,
                "error":{
                    "code":"INVALID_LOGIN",
                    "message":"Email or password is invalid"
                }
            }
        )
    jwt_token = encode_jwt(email)
    return {
        "success":True,
        "access_token":jwt_token,
        "token_type":"bearer",
        "message":"Login Successful"
    }


@app.post("/create-room/{room_name}",status_code=status.HTTP_201_CREATED)
async def create_room(room_name:str,payload=Depends(decode_jwt())):
    room_name_validated=validate_room_name(room_name)
    if not room_name_validated:
        raise HTTPException(
            status_code=status.HTTP_411_LENGTH_REQUIRED,
            detail={
                "success":False,
                "error":{
                    "code":"INCORRECT_FORMAT",
                    "message": "Room name length should be between 0 and 32"
                }
            }
        )
    room_details_stored=insert_room(room_name)
    if not room_details_stored:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "success":False,
                "error":{
                    "code":"ROOM_ALREADY_EXISTS",
                    "message":"Room already exists"
                }
            }
        )
    if room_details_stored is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success":False,
                "error":{
                    "code":"SERVER_ERROR",
                    "message": "error from server side"
                }
            }
        )
    return {
        "success":True,
        "data":{},
        "message":"Room created successfully"
    }

@app.get("/rooms/{room_id}/messages",status_code=status.HTTP_200_OK)
async  def retrieve_room_messages(room_id:int,payload=Depends(decode_jwt)):
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success":False,
                "error":{
                    "code":"NOT_LOGGED_IN",
                    "message":"you need to login to access rooms"
                }
            }
        )
    data_stored=get_messages(room_id)
    if data_stored is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success":False,
                "error":{
                    "code":"COULD_NOT_RETRIEVE_DATA",
                    "message": "messages could not be retrieved from DB"
                }
            }
        )
    return {
        "success":True,
        "data":{
            "message_data":data_stored
        },
        "message": "Data retrieved successfully"
    }

class ConnectionManager:
    def __init__(self):
        self.room_connections={}
        self.websocket_info={}


    async def connect(self,websocket:WebSocket,user_id:int,room_id: str):
        await websocket.accept()

        ''''If this condition not used then all users might appear in all rooms'''
        if not room_id in self.room_connections:
            self.room_connections[room_id]={}

        self.room_connections[room_id][user_id]=websocket

        self.websocket_info[websocket]={"room_ID":room_id,"user_id":user_id}


    def disconnect(self,websocket:WebSocket):
        room_id=self.websocket_info[websocket]["room_ID"]
        user_id=self.websocket_info[websocket]["user_id"]
        self.websocket_info.pop(websocket)
        self.room_connections[room_id].pop(user_id)

    async def send_message(self,websocket:WebSocket,message:str):
        await websocket.send_text(message)

    async def broadcast(self,room_id:int,message:str):
        for conn in self.room_connections[room_id].values():
            await conn.send_text(message)

manager=ConnectionManager()

@app.websocket("/chat/{room_name}")
async def chat(websocket: WebSocket,room_name:str,payload=Depends(decode_jwt)):
    ## means JWT expired or invalid
    if payload is None:
        await websocket.close(code=1008)
        return

    user_id=payload["uid"]
    user_name=payload["name"]
    room_id=fetch_room_id(room_name) # from DB


    ## if a room doesnt exist
    if room_id is None:
        await websocket.close(code=1008)
        return
    await manager.connect(websocket,user_id,room_id)
    try:
        while True:
            data=await websocket.receive_text()
            save_message(room_id,user_id,data)
            #await manager.send_message(websocket,f"Message was: {data}")
            await manager.broadcast(room_id,f" {user_name} said {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(room_id,f" {user_name} got disconnected")



## TODO: Frontedn UI using Flutter