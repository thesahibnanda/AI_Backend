import os 
import json

class Config:
    GROQ_API_KEYS = json.loads(os.getenv("GROQ_API_KEYS"))
    KEY=json.loads(os.getenv("KEY"))[0]
    SENDER_MAIL=json.loads(os.getenv("SENDERS_MAIL"))[0]
    SENDER_PASS=json.loads(os.getenv("SENDER_PASS"))[0]
    REC_MAIL=json.loads(os.getenv("REC_MAIL"))[0]
    WORD=json.loads(os.getenv("WORD"))[0]