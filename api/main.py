from fastapi import FastAPI
from .routes import router
from fastapi.middleware.cors import CORSMiddleware
from apify import Actor
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 🔄 Startup
    await Actor.init()
    yield
    # 🔚 Shutdown
    await Actor.exit()

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router)


@app.get("/")
def read_root():
    return {"Hello": "World"}