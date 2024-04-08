# cfbr_orders
A simple website to guide your team playing [College Football Risk](https://collegefootballrisk.com/).

## Setup
You'll need to create a `.env` file in the repo root with these contents:
```env
DOMAIN="localhost"
HTTP_PORT=8080

THE_GOOD_GUYS="Michigan"
GOOD_GUYS_DISCORD_LINK="..."

REDDIT_CLIENT_ID="..."
REDDIT_CLIENT_SECRET="..."

DISCORD_CLIENT_ID="..."
DISCORD_CLIENT_SECRET="..."
```

### Reddit
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

### Discord
You will also need to create a Discord "app".
1. Go to https://discord.com/developers/applications
2. Make an account/sign in
3. Click "New Application"
4. Give it an even more sensible name
5. Click on "OAuth2" on the left hand sidebar
6. Copy the client ID to the .env file as your `DISCORD_CLIENT_ID`
7. Generate a secret and copy that to the .env file as your `DISCORD_CLIENT_SECRET`
8. Enter your redirect URL: `http://localhost:8080/discord_callback`.
9. Scroll down and save changes
10. Do not share these with anyone!


## Deployment

The app is designed to run on a *nix system, but it can be done on Windows too. Message EpicWolverine if you need WSL help.
1. `sudo apt install python3 python3-venv make sqlite3`
2. `make install_venv`
    - If the venv is giving you a hard time, you can just install the dependancies globally with `pip install -r requirements.txt`. I had issues with the venv on WSL.
    - Source the venv in future terminals with `source venv/bin/activate`.
3. Run `./init_db.sh` to initilize the database.
4. Run `python ingest_orders.py <path>` to fill the DB with some data.
5. Run `python flask_app.py` to start the webserver.

### PythonAnywhere (WebApp)

If you want to deploy this as a webapp, a useful and relatively cheap hosting service is PythonAnywhere ($5/mo) at https://www.pythonanywhere.com

1. Make an account. 
2. Either open a Bash console via the dashboard or SSH into PythonAnywhere.
    - To SSH into PythonAnywhere through VSCode, you'll want to make sure you're using Remote - SSH Version v0.107.1. Later versions seem broken with PythonAnywhere.
3. Clone the repo into your home directory.
4. Create your .env as outlined in Setup but set 
    ```env
    DOMAIN=<username>.pythonanywhere.com
    HTTP_PORT=80
    ```
5. Go to the "Web" tab of your PythonAnywhere dashboard.
6. Add a new webapp that for the purpose of this tutorial will be `<username>.pythonanywhere.com`
7. Select "Flask" as your web framework.
8. Select Python 3.10 as your Python version.
9. Point the path to `/home/<username>/cfbr_orders/flask_app.py`
10. This will delete whatever is in `flask_app.py`. Just restore it using git: 
    ```shell
    cd /home/<username>/cfbr_orders
    git checkout -- flask_app.py
    ```
11. Under "Code", set your working directory AND source code to `/home/<username>/cfbr_orders`
12. Scroll up and "Reload" `<username>.pythonanywhere.com`
13. Set your Discord and Reddit redirect URLs to `http://<username>.pythonanywhere.com:80/<app>_callback` in the app settings pages on each service.
14. Things *should* be working! Visit `<username>.pythonanywhere.com` and get started dominating the Risk board!
