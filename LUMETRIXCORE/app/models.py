import datetime
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120), default="")
    password_hash: Mapped[str] = mapped_column(String(255))
    # BYO tokens (cifrados)
    claude_token_enc: Mapped[str] = mapped_column(Text, default="")
    resend_token_enc: Mapped[str] = mapped_column(Text, default="")
    # Identidad de remitente
    from_name: Mapped[str] = mapped_column(String(120), default="")
    from_email: Mapped[str] = mapped_column(String(255), default="")
    template: Mapped[str] = mapped_column(String(40), default="minimal")
    # Suscripción (Hotmart)
    subscription_status: Mapped[str] = mapped_column(String(30), default="active")
    hotmart_subscriber_id: Mapped[str] = mapped_column(String(120), default="")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

class Campaign(Base):
    __tablename__ = "campaigns"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="generated")  # generated|sending|paused|done|error
    mode: Mapped[str] = mapped_column(String(20), default="auto")  # auto|tsl|crosssell
    blocks_json: Mapped[str] = mapped_column(Text, default="[]")  # salida ÚNICA consolidada
    report_json: Mapped[str] = mapped_column(Text, default="{}")
    total: Mapped[int] = mapped_column(Integer, default=0)
    sent: Mapped[int] = mapped_column(Integer, default=0)
    failed: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

class Recipient(Base):
    __tablename__ = "recipients"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"), index=True)
    email: Mapped[str] = mapped_column(String(255), index=True)
    state: Mapped[str] = mapped_column(String(20), default="queued")  # queued|sent|failed|skipped
    provider_id: Mapped[str] = mapped_column(String(120), default="")

class Suppression(Base):
    __tablename__ = "suppression"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    email: Mapped[str] = mapped_column(String(255), index=True)
    reason: Mapped[str] = mapped_column(String(40), default="unsubscribe")

class ConfigFile(Base):
    __tablename__ = "config_files"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    kind: Mapped[str] = mapped_column(String(30))  # catalogo|afinidad|config
    content: Mapped[str] = mapped_column(Text, default="")
