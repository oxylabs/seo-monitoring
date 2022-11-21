import os
from dotenv import load_dotenv

# load environment variables
load_dotenv('.env')

# read environment variable into python variable
SERP_TARGET = os.getenv("SERP_TARGET")
SERP_DOMAIN = os.getenv("SERP_DOMAIN")
SERP_PARSE_RESULT = bool(os.getenv("SERP_PARSE_RESULT"))
SERP_LANGUAGE = os.getenv("SERP_LANGUAGE")
SERP_PAGES = int(os.getenv("SERP_PAGES", 10))
INPUT_KEYWORDS = os.getenv("INPUT_KEYWORDS")
INPUT_PROCESSED = os.getenv("INPUT_PROCESSED")
OUTPUT_KEYWORDS = os.getenv("OUTPUT_KEYWORDS")
OUTPUT_FILE_TYPE = os.getenv("OUTPUT_FILE_TYPE", "xlsx")
OUTPUT_FILE_NAME = os.getenv("OUTPUT_FILE_NAME", "keywords_serps")
INPUT_POLL_TIME = int(os.getenv("INPUT_POLL_TIME", 5))
OXY_SERPS_AUTH_USERNAME = os.getenv("OXY_SERPS_AUTH_USERNAME")
OXY_SERPS_AUTH_PASSWORD = os.getenv("OXY_SERPS_AUTH_PASSWORD")
