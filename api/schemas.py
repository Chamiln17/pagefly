from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class LandingPageParams(BaseModel):
    images: list[HttpUrl] = Field(..., min_length=1, max_length=6)
    product_name: str
    product_price: float
    currency: Literal["DZD", "EUR", "USD"]
    is_hero: bool | None = False
    is_feature: bool | None = False
    is_testimonials: bool | None = False
    is_pricing: bool | None = False
    is_contact: bool | None = False
    is_footer: bool | None = False
    marketing_angle: str | None = None
    language: str = "ar"


class ShopifyURLRequest(BaseModel):
    url: HttpUrl
    marketing_angle: str | None = None
