from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Literal


class LandingPageParams(BaseModel):
    images: List[HttpUrl] = Field(..., min_length=1, max_length=6)
    product_name: str
    product_price: float
    currency: Literal["DZD", "EUR", "USD"]
    is_hero: Optional[bool] = False
    is_feature: Optional[bool] = False
    is_testimonials: Optional[bool] = False
    is_pricing: Optional[bool] = False
    is_contact: Optional[bool] = False
    is_footer: Optional[bool] = False
    marketing_angle: Optional[str] = None
    language: str = "ar"


class ShopifyURLRequest(BaseModel):
    url: HttpUrl
    marketing_angle: Optional[str] = None
