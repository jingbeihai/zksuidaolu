import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import settings
from logging_config import setup_logging

setup_logging()

app = FastAPI(title=settings.APP_TITLE)

app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY,
                   session_cookie=settings.SESSION_COOKIE,
                   max_age=settings.SESSION_MAX_AGE)

app.mount("/static", StaticFiles(directory="static"), name="static")

from routers import auth, device, process, schedule, production, tv, user, log, backup
app.include_router(auth.router)
app.include_router(device.router)
app.include_router(process.router)
app.include_router(schedule.router)
app.include_router(production.router)
app.include_router(tv.router)
app.include_router(user.router)
app.include_router(log.router)
app.include_router(backup.router)

@app.get("/")
async def root():
    return RedirectResponse(url="/login")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT, reload=False)
