from dataclasses import dataclass, field
from typing import Literal
from pydantic import BaseModel, Field


class Stock(BaseModel):
    size: str
    quantity: int


class Product(BaseModel):
    product_id: str
    name: str
    garment_type: str
    description: str
    colors: list[str]
    search_tags: list[str]
    image_url: str
    price: float
    inventory: list[Stock] = Field(default_factory=list)
    total_stock: int = 0


class UserPublic(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str


class AuthInput(BaseModel):
    email: str
    password: str


class RegisterInput(AuthInput):
    first_name: str
    last_name: str


class AuthResponse(BaseModel):
    token: str
    user: UserPublic


class ChatInput(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    product_id: str | None = None


class ChatMessage(BaseModel):
    role: Literal['user', 'assistant']
    content: str
    products: list[Product] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str
    products: list[Product] = Field(default_factory=list)


@dataclass
class AgentDeps:
    user_name: str | None = None
    user_email: str | None = None
    product_id: str | None = None
    tool_events: list[dict] = field(default_factory=list)
