from flask import Flask, abort, request, make_response, redirect, render_template
import requests
import requests.auth
from uuid import uuid4
import urllib
from datetime import datetime, timedelta
from pytz import timezone

from constants import *
from cfbr_db import Db
from orders import Orders
from admin_page import Admin
from logger import Logger

Logger.init_logging()
log = Logger.getLogger(__name__)
app = Flask(__name__)

###############################################################
#
# Functions to handle routes & Flask app logic
#
###############################################################


CONFIRMATION_PAGE = "confirmation.html"
ORDER_PAGE = "order.html"
ERROR_PAGE = "error.html"

@app.route('/')
def homepage():
    cookie = request.cookies.get('a')
    auth_resp_if_necessary, username = check_identity_or_auth(request)

    # The user needs to authenticate, short-circuit here.
    if auth_resp_if_necessary:
        return auth_resp_if_necessary

    template_params = {"username": username}

    cfbr_api_user_response = requests.get(f"{CFBR_REST_API}/player?player={username}")
    try:
        cfbr_api_user_response.raise_for_status()
    except requests.exceptions.HTTPError or AttributeError as e:
        log.error(f"{username}: Reddit user who doesn't play CFBR tried to log in")
        log.error(f"Exception: {e}")
        template_params |= {
            "error_message": f"Sorry, you'll need to sign up for CFB Risk and join {THE_GOOD_GUYS} first.",
            "link": "https://www.collegefootballrisk.com/"
        }
        return build_template_response(cookie, ERROR_PAGE, template_params)

    active_team = cfbr_api_user_response.json()['active_team']['name']
    current_stars = cfbr_api_user_response.json()['ratings']['overall']
    template_params |= {
        "is_admin": Admin.is_admin(username),
        "current_stars": current_stars,
        "hoy": what_day_is_it(),
        "confirm_url": CONFIRM_URL
    }

    # Enemy rogue or SPY!!!! Just give them someone to attack.
    if active_team != THE_GOOD_GUYS:
        # TODO: This codepath is currently broken.  Don't rely on it until it gets fixed again.
        # order = Orders.get_foreign_order(active_team, CFBR_day(), CFBR_month())
        log.info(f"{username}: Player on {active_team} tried to log in.")
        template_params |= {"error_message": f"Sorry, you'll need to join {THE_GOOD_GUYS} first."}
        return build_template_response(cookie, ERROR_PAGE, template_params)
    # Good guys get their assignments here
    else:
        # We now have three states, ordered in reverse chronological:
        # 3) The user has already accepted an order.  Show them the thank-you screen, but remind them what (we think)
        #   they did
        # 2) The user has been offered a few options.  Retrieve those options and then display them (or confirm
        #   their choice)
        # 1) The user is showing up for the first time.  Create offers for them and display them.
        # (...and 0) There aren't any plans available yet to pick from.

        # Stage 3: This user has already been here and done that.
        existing_move = Orders.user_already_moved(username, CFBR_day(), CFBR_month())
        if existing_move is not None:
            log.info(f"{username}: Showing them the move they previously made.")
            template_params |= {"territory": existing_move}
            return build_template_response(cookie, CONFIRMATION_PAGE, template_params)

        # They're not in Stage 3.  Are they in stage 2, or did they make a choice?
        confirmed_territory = None
        confirmation = request.args.get('confirmed', default=None, type=str)
        if confirmation:
            confirmed_territory = Orders.confirm_offer(username, CFBR_day(), CFBR_month(), confirmation)
        if confirmed_territory:
            # They made a choice!  Our favorite.
            log.info(f"{username}: Chose to move on {confirmed_territory}")
            template_params |= {"territory": confirmed_territory}
            return build_template_response(cookie, CONFIRMATION_PAGE, template_params)
        else:
            existing_offers = Orders.user_already_offered(username, CFBR_day(), CFBR_month())
        if existing_offers is not None and len(existing_offers) > 0:
            log.info(f"{username}: Showing them their previous offers.")
            template_params |= {"orders": existing_offers}
            return build_template_response(cookie, ORDER_PAGE, template_params)

        # I guess they're in Stage 1: Make them an offer
        new_offer_territories = Orders.get_next_offers(CFBR_day(), CFBR_month(), current_stars)
        if len(new_offer_territories) > 0:
            new_offers = []
            for i in range(len(new_offer_territories)):
                offer_uuid = Orders.write_new_offer(username, new_offer_territories[i],
                                                    CFBR_day(), CFBR_month(), current_stars, i)
                new_offers.append((new_offer_territories[i], offer_uuid))
            log.info(f"{username}: Generated new offers.")
            template_params |= {"orders": new_offers}
            return build_template_response(cookie, ORDER_PAGE, template_params)
        else:
            log.info(f"{username}: Tried to generate new offers and failed. Are the plans loaded for today?")

        # Nope sorry we're in stage 0: Ain't no orders available yet.  We'll use the order template
        # sans orders until we create a page with a sick meme telling the Strategists to hurry up.
        log.warning(f"{username}: Hit the 'No Orders Loaded' page")
        return build_template_response(cookie, ORDER_PAGE, template_params)


def build_template_response(cookie, template, template_params):
    resp = make_response(render_template(template, **template_params))
    resp.set_cookie('a', cookie)
    return resp


@app.route(REDDIT_CALLBACK_ROUTE)
def reddit_callback():
    error = request.args.get('error', '')
    if error:
        return "Error: " + error
    state = request.args.get('state', '')
    if not is_valid_state(state):
        # Uh-oh, this request wasn't started by us!
        log.error(f"unknown,403 from Reddit Auth API. WTF bro.")
        abort(403)
    code = request.args.get('code')
    access_token = get_token(code)

    response = make_response(redirect('/'))
    response.set_cookie('a', access_token.encode())
    return response


@app.route('/admin')
def admin_page():
    auth_resp_if_necessary, username = check_identity_or_auth(request)

    # The user needs to authenticate, short-circuit here.
    if auth_resp_if_necessary:
        return auth_resp_if_necessary

    return Admin.build_page(request, username, CFBR_day(), CFBR_month())

@app.teardown_appcontext
def close_connection(exception):
    Db.close_connection(exception)


###############################################################
#
# Functions to handle time
#
###############################################################


def CFBR_month():
    tz = timezone('EST')
    today = datetime.now(tz)
    hour = int(today.strftime("%H"))
    minute = int(today.strftime("%M"))
    if (hour == 23) or ((hour == 22) and (minute > 29)):
        today = datetime.now(tz) + timedelta(days=1)
    if today.strftime("%A") == "Sunday":
        today = today + timedelta(days=1)
    return today.strftime("%-m")


def CFBR_day():
    tz = timezone('EST')
    today = datetime.now(tz)
    hour = int(today.strftime("%H"))
    minute = int(today.strftime("%M"))
    if (hour == 23) or ((hour == 22) and (minute > 29)):
        today = datetime.now(tz) + timedelta(days=1)
    if today.strftime("%A") == "Sunday":
        today = today + timedelta(days=1)
    return today.strftime("%-d")


# Pretty date, for the user so not CFBR
def what_day_is_it():
    tz = timezone('EST')
    return datetime.now(tz).strftime("%B %d, %Y")

###############################################################
#
# Boilerplate for any page loads
#
###############################################################

def check_identity_or_auth(request):
    access_token = request.cookies.get('a')

    if access_token is None:
        log.debug(f"Incoming request with no access token, telling them to auth the app")
        link = make_authorization_url()
        resp = make_response(render_template('auth.html', authlink=link))
        return (resp, None)

    headers = {"Authorization": "bearer " + access_token, 'User-agent': 'CFB Risk Orders'}
    response = requests.get(REDDIT_ACCOUNT_URI, headers=headers)
    if response.status_code == 401:
        log.error(f"{access_token},401 Error from CFBR API")
        link = make_authorization_url()
        resp = make_response(render_template('auth.html', authlink=link))
        return (resp, None)

    # If we made it this far, we theoretically know the user's identity.  Say so.
    username = get_username(access_token)
    return (None, username)


###############################################################
#
# Reddit API helper functions
#
###############################################################


def make_authorization_url():
    state = str(uuid4())
    save_created_state(state)
    params = {"client_id": REDDIT_CLIENT_ID,
              "response_type": "code",
              "state": state,
              "redirect_uri": REDIRECT_URI,
              "duration": "temporary",
              "scope": "identity"}
    url = f"{REDDIT_AUTH_URI}?{urllib.parse.urlencode(params)}"
    return url


def save_created_state(state):
    pass


def is_valid_state(state):
    return True


def get_token(code):
    client_auth = requests.auth.HTTPBasicAuth(REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET)
    post_data = {"grant_type": "authorization_code",
                 "code": code,
                 "redirect_uri": REDIRECT_URI}
    response = requests.post(REDDIT_TOKEN_URI,
                             auth=client_auth,
                             headers={'User-agent': 'CFB Risk Orders'},
                             data=post_data)
    token_json = response.json()
    return token_json['access_token']


def get_username(access_token):
    headers = {"Authorization": "bearer " + access_token, 'User-agent': 'CFB Risk Orders'}
    response = requests.get(REDDIT_ACCOUNT_URI, headers=headers)
    me_json = response.json()
    return me_json['name']


###############################################################
#
# Let's go!!!!
#
###############################################################


if __name__ == '__main__':
    app.run(debug=True, port=HTTP_PORT)
