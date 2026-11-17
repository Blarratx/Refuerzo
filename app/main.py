from typing import Annotated
import bcrypt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Ticket, TicketPriority, User, UserRole

app = FastAPI()
security = HTTPBasic()


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    role: UserRole
    password: str = Field(min_length=6, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    role: UserRole


class TicketCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    prioridad: TicketPriority = TicketPriority.MEDIO


class TicketUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, min_length=1)
    prioridad: TicketPriority | None = None


class TicketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: str
    prioridad: TicketPriority
    user_id: int


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode()[:72], bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode()[:72], hashed.encode())


def get_current_user(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    user = db.execute(select(User).where(User.username == credentials.username)).scalar_one_or_none()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
    return user


@app.post("/users/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(user_in: UserCreate, db: Annotated[Session, Depends(get_db)]):
    if db.execute(select(User).where(User.username == user_in.username)).scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Usuario ya existe")
    user = User(username=user_in.username, hashed_password=hash_password(user_in.password), role=user_in.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.get("/users/me", response_model=UserOut)
def read_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user


@app.post("/tickets/", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def create_ticket(
    ticket_in: TicketCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    ticket = Ticket(**ticket_in.model_dump(), user_id=current_user.id)
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


@app.get("/tickets/", response_model=list[TicketOut])
def list_tickets(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return list(db.execute(select(Ticket)).scalars().all())


@app.get("/tickets/{ticket_id}", response_model=TicketOut)
def get_ticket(
    ticket_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    return ticket


@app.patch("/tickets/{ticket_id}", response_model=TicketOut)
def update_ticket(
    ticket_id: int,
    ticket_in: TicketUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    for field, value in ticket_in.model_dump(exclude_unset=True).items():
        setattr(ticket, field, value)
    db.commit()
    db.refresh(ticket)
    return ticket


@app.delete("/tickets/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket(
    ticket_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    db.delete(ticket)
    db.commit()
