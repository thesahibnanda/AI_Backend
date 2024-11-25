import logging
from fastapi import FastAPI
from pydantic import BaseModel, EmailStr
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.requests import Request
import time
from models_groq import Model
from send_mail import send_email
from config import Config

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],  
)

class AppRequest(BaseModel):
    prompt: str


class SubmitKey(BaseModel):
    key: str
    name: str
    email: EmailStr 
    

rate_limit_store = {}
def rate_limiter(request: Request, limit: int, time_window: int):
    client_ip = request.client.host
    current_time = time.time()

    if client_ip not in rate_limit_store:
        rate_limit_store[client_ip] = []


    rate_limit_store[client_ip] = [
        timestamp for timestamp in rate_limit_store[client_ip] if current_time - timestamp < time_window
    ]

    if len(rate_limit_store[client_ip]) >= limit:
        return JSONResponse(status_code=429, content={
                    "is_error": False,
                    "answer": "Rate limit exceeded, try again later",
                    "got_key": False,
                    "key_script": "",
                })


    rate_limit_store[client_ip].append(current_time)
    return None

@app.get("/heathz")
async def health_check():
    return JSONResponse(
        status_code=200,
        content={"is_error": False, "message": "OK"},
    )

@app.post("/answer")
async def ask_bot(req: AppRequest, request: Request):
    limiter = rate_limiter(request, 10, 60)
    if limiter:
        return limiter
    try:
        logger.info(f"Processing prompt: {req.prompt}")
        answer = Model.answer(req.prompt)
        
        if Config.WORD.lower() in answer.lower():
            logger.info(f"Answer contains '{Config.WORD}', returning with key.")
            return JSONResponse(
                status_code=200,
                content={
                    "is_error": False,
                    "answer": answer,
                    "got_key": True,
                    "key_script": Config.KEY,
                },
            )
        else:
            logger.info(f"Answer does not contain '{Config.WORD}', returning without key.")
            return JSONResponse(
                status_code=200,
                content={
                    "is_error": False,
                    "answer": answer,
                    "got_key": False,
                    "key_script": "",
                },
            )
    except Exception as e:
        logger.error(f"Error processing prompt: {str(e)}")
        return JSONResponse(
            status_code=500, content={"is_error": True, "message": str(e)}
        )


@app.post("/submit_key")
async def submit_key(req: SubmitKey):
    try:
        logger.info(f"Received key submission from {req.name} ({req.email})")
        
        if req.key == Config.KEY:
            logger.info("Key is valid, sending confirmation email.")
            send_email(
                Config.REC_MAIL,
                f"{req.name} Found the Code",
                f"Email: {req.email}",
            )
            return JSONResponse(
                content={"is_error": False, "message": "Thanks, We Will Contact Soon"},
                status_code=200,
            )
        else:
            logger.warning("Invalid key submitted.")
            send_email(
                Config.REC_MAIL,
                f"{req.name} Submitted an Incorrect Key",
                f"Email: {req.email}",
            )
            return JSONResponse(
                content={"is_error": True, "message": "Wrong Key"},
                status_code=403,
            )
    except Exception as e:
        logger.error(f"Error during key submission: {str(e)}")
        return JSONResponse(
            status_code=500, content={"is_error": True, "message": str(e)}
        )
