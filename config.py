# config.py
import os
from dotenv import load_dotenv

class Config:
    def __init__(self):
        load_dotenv()
        self.STEAM_API_KEY = os.getenv("STEAM_API_KEY")

cfg = Config()