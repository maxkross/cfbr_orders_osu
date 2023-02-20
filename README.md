# cfbr_orders
A simple website to guide your team playing [College Football Risk](https://collegefootballrisk.com/).

# Setup
You'll need to create a `.env` file in the repo root with these contents:
```
DOMAIN="localhost"
HTTP_PORT=8080

THE_GOOD_GUYS="Michigan"

REDDIT_CLIENT_ID="..."
REDDIT_CLIENT_SECRET="..."
```

You will need to create a Reddit "app".
1. Go to https://www.reddit.com/prefs/apps
2. Click "create another app...".
3. Give it a sensible name.
4. Pick "Script".
5. Set "redirect uri" to `http://localhost:8080/reddit_callback`.
6. Click "create app".
7. Reload the page.
8. Under "developed applications" at the bottom, find your app and click "edit".
9. Under "personal use script" will be your `REDDIT_CLIENT_ID`.
10. "secret" is your `REDDIT_CLIENT_SECRET`.
11. Do not share these with anyone!

The app is designed to run on a *nix system, but it can be done on Windows too. Message EpicWolverine if you need WSL help.
1. `sudo apt install python3 python3-venv make sqlite3`
2. `make install_venv`
    - If the venv is giving you a hard time, you can just install the dependancies globally with `pip install -r requirements.txt`. I had issues with the venv on WSL.
    - Source the venv in future terminals with `source venv/bin/activate`.
3. Run `./init_db.sh` to initilize the database.
4. Run `python ingest_orders.py <path>` to fill the DB with some data.
5. Run `python flask_app.py` to start the webserver.
