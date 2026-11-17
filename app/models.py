import enum
from sqlalchemy import String, ForeignKey, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class UserRole(str, enum.Enum):
    TECNICO = "tecnico"
    EMPLEADO = "empleado"


class TicketPriority(str, enum.Enum):
    BAJO = "bajo"
    MEDIO = "medio"
    ALTO = "alto"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"), nullable=False)
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="owner")


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    prioridad: Mapped[TicketPriority] = mapped_column(
        Enum(TicketPriority, name="ticket_priority"),
        nullable=False,
        default=TicketPriority.MEDIO,
        server_default=TicketPriority.MEDIO.value,
    )
    owner: Mapped["User"] = relationship(back_populates="tickets")
