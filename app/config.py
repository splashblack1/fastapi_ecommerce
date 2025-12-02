import os
from dotenv import load_dotenv


load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY must be set")
DATABASE_URL = os.getenv("DATABASE_URL")
ALGORITHM = "HS256"
