from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
import aiohttp
import os
from pydantic import BaseModel

app = FastAPI()
templates = Jinja2Templates(directory="templates")

class Email(BaseModel):
    recipient: str
    subject: str
    body: str

async def get_session():
    # Simulace autentizace (zde by měl být JWT nebo session z identity)
    return {"username": "admin"}

@app.get("/", response_class=HTMLResponse)
async def login(request: Request, session: dict = Depends(get_session)):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", response_class=HTMLResponse)
async def login_post(request: Request, email: str = Form(...), password: str = Form(...)):
    # Simulace ověření proti identity
    if email == "admin@example.com" and password == "admin":
        # Přesměrování na dashboard po přihlášení
        return RedirectResponse(url="/dashboard", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "error": "Neplatné přihlašovací údaje"})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, session: dict = Depends(get_session)):
    # Načtení e-mailů (simulace z storage)
    emails = []  # Nahraď fetch z storage, např. http://storage:8002/emails
    return templates.TemplateResponse("index.html", {"request": request, "username": session["username"], "emails": emails})

@app.post("/send", response_class=HTMLResponse)
async def send_email(request: Request, recipient: str = Form(...), subject: str = Form(...), body: str = Form(...)):
    email = Email(recipient=recipient, subject=subject, body=body)
    async with aiohttp.ClientSession() as session:
        async with session.post("http://smtp:8000/send", json=email.dict()) as response:
            if response.status == 200:
                return RedirectResponse(url="/dashboard", status_code=303)
            return templates.TemplateResponse("index.html", {"request": request, "error": "Chyba odeslání"})
    return templates.TemplateResponse("index.html", {"request": request, "error": "Chyba připojení"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)