import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .routes import router as image_router

def init_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] [%(filename)s] %(message)s ",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger(__name__)

# App
logger = init_logging()
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Importiere und füge die Routen hinzu
app.include_router(image_router)

# Serviere statische Dateien auf Root-Ebene
app.mount("/", StaticFiles(directory="src/static", html=True), name="static")

