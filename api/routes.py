import random

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import HTMLResponse

from .generator import get_graph, initial_state
from .schemas import LandingPageParams, ShopifyURLRequest
from .scraper.shopify_scraper import (
    ScrapedProduct,
    ScrapeError,
    http_client,
    scrape_shopify_data,
)
from .storage import page_store

router = APIRouter()


def generate_and_store(data: LandingPageParams, graph) -> dict:
    """Run the graph; store the page and return its preview link, or raise 502."""
    state = graph.invoke(initial_state(data))
    html = state.get("generated_html")
    if state.get("error_message") or not html:
        raise HTTPException(
            status_code=502,
            detail=state.get("error_message") or "Graph returned no HTML.",
        )
    safe_name = data.product_name.lower().replace(" ", "-")
    page_key = f"{safe_name}_{random.randint(1000, 9999)}"
    page_store[page_key] = html
    return {"preview_url": f"/preview/{page_key}"}


@router.post("/generate")
def generate_page(data: LandingPageParams, graph=Depends(get_graph)):
    return generate_and_store(data, graph)


@router.get("/preview/{page_key}", response_class=HTMLResponse)
def preview_page(page_key: str):
    html = page_store.get(page_key)
    if not html:
        raise HTTPException(status_code=404, detail="Page not found")
    return html


@router.post("/scrape-shopify")
async def extract_product_data_and_generate(
    payload: ShopifyURLRequest,
    graph=Depends(get_graph),
    client: httpx.AsyncClient = Depends(http_client),
):
    try:
        scraped: ScrapedProduct = await scrape_shopify_data(str(payload.url), client)
    except ScrapeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # ScrapedProduct's str currency and image URLs become the model's Literal and
    # HttpUrl fields here, at validation.
    landing_data = LandingPageParams.model_validate(
        {
            **scraped,
            "is_hero": True,
            "is_feature": True,
            "is_testimonials": True,
            "is_pricing": True,
            "is_contact": True,
            "is_footer": True,
            "marketing_angle": payload.marketing_angle,
        }
    )
    # The graph is synchronous and slow; keep it off the event loop.
    return await run_in_threadpool(generate_and_store, landing_data, graph)
