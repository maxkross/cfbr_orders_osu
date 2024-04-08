from dotenv import dotenv_values
from pathlib import Path

config = dotenv_values('.env')

POSTGAME = None # "Yay!" or "Boo!" or None

DOMAIN = config['DOMAIN']
HTTP_PORT = config['HTTP_PORT']
BASE_URL = f"http://{DOMAIN}:{HTTP_PORT}"
REDDIT_CALLBACK_ROUTE = "/reddit_callback"
DISCORD_CALLBACK_ROUTE = "/discord_callback"
REDIRECT_URI = f"{BASE_URL}{REDDIT_CALLBACK_ROUTE}"
DISCORD_REDIRECT_URI = f"{BASE_URL}{DISCORD_CALLBACK_ROUTE}"
CONFIRM_URL = f"{BASE_URL}/?confirmed="

CFBR_REST_API = "https://collegefootballrisk.com/api"
CFBR_MOVE_DEEPLINK = "https://collegefootballrisk.com/#MyMove"

REDDIT_AUTH_URI = "https://ssl.reddit.com/api/v1/authorize"
REDDIT_ACCOUNT_URI = "https://oauth.reddit.com/api/v1/me"
REDDIT_TOKEN_URI = "https://ssl.reddit.com/api/v1/access_token"

DISCORD_AUTH_URI = "https://discord.com/oauth2/authorize"
DISCORD_TOKEN_URI = "https://discord.com/api/oauth2/token"
DISCORD_ACCOUNT_URI = "https://discord.com/api/users/@me"

ROOT = Path(__file__).parent
DB = f"{ROOT}/files/cfbrisk.db"
LOG_FILE = f"{ROOT}/files/log.txt"

THE_GOOD_GUYS = config['THE_GOOD_GUYS']
GOOD_GUYS_DISCORD_LINK = config['GOOD_GUYS_DISCORD_LINK']

REDDIT_CLIENT_ID = config['REDDIT_CLIENT_ID']
REDDIT_CLIENT_SECRET = config['REDDIT_CLIENT_SECRET']

DISCORD_CLIENT_ID = config['DISCORD_CLIENT_ID']
DISCORD_CLIENT_SECRET = config['DISCORD_CLIENT_SECRET']
