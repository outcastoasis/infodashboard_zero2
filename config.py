from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("API_KEY")
CITY = "Menzingen,CH"
LANG = "de"
UNITS = "metric"