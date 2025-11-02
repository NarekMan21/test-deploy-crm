from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from database import Base

class UserRole(str, enum.Enum):
    admin = "admin"
    logist = "logist"
    work = "work"

class OrderStatus(str, enum.Enum):
    draft = "draft"  # Черновик, создан админом
    pending_confirmation = "pending_confirmation"  # Ожидает подтверждения админов
    confirmed = "confirmed"  # Подтвержден, логистика может добавлять детали
    in_progress = "in_progress"  # В работе у мастерской
    ready = "ready"  # Готов к доставке
    delivered = "delivered"  # Доставлен

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(Integer, unique=True, nullable=True)  # 1-9999, присваивается при подтверждении
    customer_name = Column(String, nullable=False)
    customer_phone = Column(String, nullable=False)
    customer_address = Column(Text, nullable=False)
    phone_agreement_notes = Column(Text, nullable=True)
    customer_requirements = Column(Text, nullable=True)
    deadline = Column(DateTime, nullable=True)
    price = Column(Integer, nullable=True)
    material_photo = Column(String, nullable=True)  # Путь к файлу
    furniture_photo = Column(String, nullable=True)  # Путь к файлу
    status = Column(Enum(OrderStatus), default=OrderStatus.draft)
    created_by = Column(Integer, ForeignKey("users.id"))
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])

    # History of edits
    edit_history = relationship("OrderEditHistory", back_populates="order")

class OrderEditHistory(Base):
    __tablename__ = "order_edit_history"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String, nullable=False)  # create, update, confirm, etc.
    field_changes = Column(Text, nullable=True)  # JSON string of changes
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    order = relationship("Order", back_populates="edit_history")
    user = relationship("User")