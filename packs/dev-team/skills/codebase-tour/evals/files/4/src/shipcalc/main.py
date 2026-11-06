from fastapi import FastAPI

from shipcalc.api.routes import router
from shipcalc.config import load_settings

settings = load_settings()
app = FastAPI(title="shipcalc")
app.include_router(router)
