from dotenv import load_dotenv
import os


load_dotenv()


class Settings:
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
    JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM")
