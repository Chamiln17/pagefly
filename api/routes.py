from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from .schemas import LandingPageParams, ShopifyURLRequest
from .scraper.shopify_scraper import scrape_shopify_data
from .generator import generate_landing_page
from .storage import page_store  
import random

router = APIRouter()

@router.post("/generate", response_class=HTMLResponse)
def generate_page(data: LandingPageParams):
    # 2. Create a unique preview key
    safe_name = data.product_name.lower().replace(" ", "-")
    random_suffix = random.randint(1000, 9999)
    page_key = f"{safe_name}_{random_suffix}"

    # 3. Store the HTML in memory
    page_store[page_key] = generate_landing_page(data)

    # 4. Return the preview link
    return JSONResponse({
        "preview_url": f"/preview/{page_key}",
    })
    
@router.get("/preview/{page_key}", response_class=HTMLResponse)
def preview_page(page_key: str):
    html = page_store.get(page_key)
    if not html:
        raise HTTPException(status_code=404, detail="Page not found")
    return html


@router.post("/scrape-shopify")
async def extract_product_data_and_generate(payload: ShopifyURLRequest):
    scraped = await scrape_shopify_data(payload.url)

    if not scraped["product_name"] or not scraped["product_price"] or not scraped["images"]:
        raise HTTPException(status_code=422, detail="Insufficient product data extracted.")

    # Create a LandingPageParams instance
    landing_data = LandingPageParams(
        product_name=scraped["product_name"],
        product_price=scraped["product_price"],
        currency=scraped["currency"],
        images=scraped["images"],
        is_hero=True,
        is_feature=True,
        is_testimonials=True,
        is_pricing=True,
        is_contact=True,
        is_footer=True,
        marketing_angle=payload.marketing_angle
    )

    # Create a unique key for preview
    safe_name = landing_data.product_name.lower().replace(" ", "-")
    random_suffix = random.randint(1000, 9999)
    page_key = f"{safe_name}_{random_suffix}"

    # Generate and store HTML
    html = generate_landing_page(landing_data)
    page_store[page_key] = html

    # Return preview info
    return JSONResponse({
        "preview_url": f"/preview/{page_key}",
    })