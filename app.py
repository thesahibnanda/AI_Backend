import logging
from fastapi import FastAPI
from pydantic import BaseModel, EmailStr
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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

@app.get("/heathz")
async def health_check():
    return JSONResponse(
        status_code=200,
        content={"is_error": False, "message": "OK"},
    )

@app.post("/answer")
async def ask_bot(req: AppRequest):
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
            logger.info(f"Answer does not contain 'fortan', returning without key.")
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
