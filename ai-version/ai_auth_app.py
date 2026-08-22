# AI Version 1 - Quarantine Implementation (Stage 7)
import os
from fastapi import FastAPI, Header, HTTPException, Depends
from pydantic import BaseModel
from supabase import create_client

app = FastAPI()
supabase = create_client(os.getenv("SUPABASE_URL", ""), os.getenv("SUPABASE_KEY", ""))

class AuthData(BaseModel):
    email: str
    password: str

@app.post("/auth/signup")
def signup(data: AuthData):
    res = supabase.auth.sign_up({"email": data.email, "password": data.password})
    return res

@app.post("/auth/login")
def login(data: AuthData):
    res = supabase.auth.sign_in_with_password({"email": data.email, "password": data.password})
    return res

@app.get("/public/info")
def public_info():
    return {"message": "Welcome stranger! This info is public."}

@app.get("/protected/profile")
def profile(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing header")
    token = authorization.replace("Bearer ", "")
    user = supabase.auth.get_user(token)
    return user
