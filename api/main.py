from fastapi import FastAPI
from .routes import router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Astro Page Generator")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080/"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router)

@app.get("/")
def read_root():
    return {"Hello": "World"}