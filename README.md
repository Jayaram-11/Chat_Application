# Chat Application

A simple real-time chat application backend built with **FastAPI**,
**PostgreSQL**, **JWT authentication**, and **WebSockets**.

The application is designed around three chat rooms. Users create an
account and log in, open a room to view previous messages, and join the
room to participate in real-time messaging.

> **Current status:** Backend V1 is implemented. Flutter frontend
> development is the next step.

## Features

-   User account creation
-   User login with password hashing
-   JWT-based authentication
-   5-day JWT expiration
-   Three chat rooms
-   Real-time messaging using WebSockets
-   Room-based connection management
-   Persistent message storage in PostgreSQL
-   Retrieval of previous room messages
-   Username and timestamp information for stored messages

## Tech Stack

-   **Backend:** Python, FastAPI
-   **Database:** PostgreSQL
-   **Authentication:** JWT
-   **Password hashing:** bcrypt
-   **Real-time communication:** WebSockets
-   **Planned frontend:** Flutter

## Architecture

The backend uses PostgreSQL for persistent application data and an
in-memory connection manager for active WebSocket connections.

``` text
                         FastAPI Backend
                              |
              +---------------+---------------+
              |               |               |
          Authentication   REST APIs      WebSockets
              |               |               |
             JWT        Message History    ConnectionManager
                              |               |
                              +-------+-------+
                                      |
                                  PostgreSQL
                                      |
                    +-----------------+-----------------+
                    |                 |                 |
                  USERS          CHAT_ROOMS         MESSAGES
```

### Database

The application uses three main tables:

#### USERS

Stores registered users.

  Column          Purpose
  --------------- ----------------------
  UID             Unique user ID
  EMAIL           User email
  NAME            Display name
  PASSWORD_HASH   Bcrypt password hash

#### CHAT_ROOMS

Stores chat rooms.

  Column      Purpose
  ----------- ------------------
  ROOM_ID     Unique room ID
  ROOM_NAME   Unique room name

#### MESSAGES

Stores persistent chat history.

  Column       Purpose
  ------------ ------------------------------
  MESSAGE_ID   Unique message ID
  ROOM_ID      Room containing the message
  UID          User who sent the message
  MESSAGE      Message content
  TIMESTAMP    Time the message was created

## Authentication Flow

``` text
Create Account
      |
      v
Store user + password hash
      |
      v
Login
      |
      v
Verify credentials
      |
      v
Generate JWT
      |
      v
JWT contains UID + name + expiration
```

The JWT is then used to authenticate WebSocket connections.

## WebSocket Flow

When a user joins a room:

``` text
Flutter Client
     |
     | WebSocket + JWT
     v
/chat/{room_name}
     |
     v
Validate JWT
     |
     v
Resolve room name -> room ID
     |
     v
Add connection to room
```

When a message is sent:

``` text
Client
  |
  | WebSocket message
  v
FastAPI
  |
  +----> Save message to PostgreSQL
  |
  +----> Broadcast message to connected users
```

The connection manager keeps track of active WebSocket connections by
room:

``` text
Room 1
 ├── User A -> WebSocket
 └── User B -> WebSocket

Room 2
 └── User C -> WebSocket

Room 3
 └── User D -> WebSocket
```

## Message History

Previous messages are retrieved through:

``` text
GET /rooms/{room_id}/messages
```

The response includes:

-   Message ID
-   User ID
-   Username
-   Message
-   Timestamp

Messages are returned in chronological order.

## API Endpoints

### Health Check

``` http
GET /
```

### Create Account

``` http
POST /create-account
```

Example request:

``` json
{
  "name": "Jay",
  "email": "jay@example.com",
  "password": "Password@123"
}
```

### Login

``` http
POST /login
```

The login endpoint uses OAuth2 form fields:

``` text
username = user email
password = user password
```

A successful login returns a JWT access token.

### Retrieve Room Messages

``` http
GET /rooms/{room_id}/messages
```

### WebSocket

``` text
/chat/{room_name}
```

The WebSocket connection requires a valid JWT and an existing room.

## Project Structure

``` text
Chat_Application/
│
├── main.py              # FastAPI routes and WebSocket endpoint
├── database.py          # PostgreSQL connection and database operations
├── security.py          # JWT creation and validation
├── validation.py        # Account and password validation
├── models.py            # Pydantic request models
├── test_db.py           # Database tests
│
├── .env.example         # Environment variable template
├── .gitignore           # Git ignore rules
└── README.md
```

## Setup

### 1. Clone the repository

``` bash
git clone https://github.com/Jayaram-11/Chat_Application.git
cd Chat_Application
```

### 2. Create a virtual environment

Windows:

``` bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

Install the Python packages required by the project, including FastAPI,
Uvicorn, PostgreSQL support, JWT, bcrypt, dotenv, email validation, and
form-data support.

### 4. Configure environment variables

Create a `.env` file based on `.env.example`:

``` env
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=
SECRET_KEY=
```

Do **not** commit the real `.env` file.

### 5. Configure PostgreSQL

Create a PostgreSQL database and provide its connection details in
`.env`.

The application's database layer contains the schema definitions for:

-   `USERS`
-   `CHAT_ROOMS`
-   `MESSAGES`

Populate the required chat rooms before using the chat functionality.

### 6. Run the backend

``` bash
uvicorn main:app --reload
```

The API will be available at:

``` text
http://127.0.0.1:8000
```

FastAPI's interactive API documentation is available at:

``` text
http://127.0.0.1:8000/docs
```

## Testing

The backend should be tested before connecting the Flutter frontend.

Testing should cover:

-   Account creation
-   Login
-   JWT validation and expiration
-   PostgreSQL user operations
-   Room lookup
-   Message persistence
-   Message history retrieval
-   WebSocket connections
-   Room isolation
-   Broadcasting
-   Disconnect handling
-   End-to-end message persistence

## Planned Flutter Frontend

The Flutter client will provide:

``` text
Login / Create Account
          |
          v
      Room List
          |
          v
   Select a Room
          |
          +----> Load Previous Messages
          |
          v
        JOIN
          |
          v
   WebSocket Connection
          |
          v
   Real-time Chat
```

## Future Improvements

Possible future additions include:

-   Refresh tokens
-   Automatic WebSocket reconnection
-   Online/offline presence
-   Typing indicators
-   Message delivery/read status
-   Message pagination
-   Push notifications
-   Message deletion/editing
-   Improved error handling
-   Production deployment
-   PostgreSQL connection pooling

These are intentionally outside the current V1 scope.

## License

This project is currently a personal learning/portfolio project.
