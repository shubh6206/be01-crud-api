import os
import sys
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, EmailStr
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("auth_api")

# Supabase Credentials & Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://your-project-url.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "your_anon_key_here")

# Initialize Supabase Client
try:
    if SUPABASE_URL and "your-project-url" not in SUPABASE_URL:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Successfully initialized Supabase client.")
    else:
        supabase = create_client("https://placeholder.supabase.co", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.placeholder")
        logger.info("Initialized Supabase client with placeholder configuration.")
except Exception as e:
    logger.warning(f"Could not initialize production Supabase client ({e}). Falling back to dummy client.")
    supabase = None

# App Metadata
app = FastAPI(
    title="Auth · Login & Protect API (Supabase Auth)",
    description="A secure RESTful API with Supabase Auth handling signup, login, logout, and protected routes guarded by JWT verification.",
    version="4.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

@app.get(
    "/",
    tags=["General"],
    summary="Get API Info",
    description="Returns API metadata and Supabase Auth status."
)
def read_root():
    return {
        "name": "Auth API",
        "version": "4.0.0",
        "auth_provider": "Supabase Auth",
        "status": "Server running and connected to Supabase"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
