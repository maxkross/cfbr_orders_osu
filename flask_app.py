from flask import Flask, abort, request, make_response, redirect, g, render_template
import requests
import requests.auth
from uuid import uuid4
import urllib
from datetime import datetime, timedelta
from pytz import timezone
import sqlite3

from constants import *
from logger import Logger

app = Flask(__name__)

###############################################################
#
# Functions to handle routes
#
###############################################################


@app.route('/')
def homepage():
    access_token = request.cookies.get('a')
    confirmation = request.args.get('confirmed', default=0, type=int)

    if access_token is None:
        link = make_authorization_url()
        resp = make_response(render_template('auth.html', authlink=link))
        return resp
    else:
        headers = {"Authorization": "bearer " + access_token, 'User-agent': 'CFB Risk Orders'}
        response = requests.get(REDDIT_ACCOUNT_URI, headers=headers)
        if response.status_code == 401:
            Logger.log(f"Error,{access_token},401 Error from CFBR API")
            link = make_authorization_url()
            resp = make_response(render_template('auth.html', authlink=link))
            return resp
        else:
            # Let's get the basics
            username = get_username(access_token)
            hoy = what_day_is_it()

            # Let's get this user's CFBR info
            response = requests.get(f"{CFBR_REST_API}/player?player={username}")
            active_team = response.json()['active_team']['name']
            total_turns = response.json()['stats']['totalTurns']
            current_stars = response.json()['ratings']['overall']

            order = ""
            # Enemy rogue or SPY!!!! Just give them someone to attack.
            if active_team != THE_GOOD_GUYS:
                order = get_foreign_order(active_team, CFBR_day(), CFBR_month())
            # Good guys get their assignments here
            else:
                existing_assignment = user_already_assigned(username, CFBR_day(), CFBR_month())
                if existing_assignment is not None:  # Already got an assignment today.
                    order = existing_assignment
                else: # Newly made assignment
                    # Step one of getting to multi-order -- just pull the first value off the response
                    order = get_next_orders(CFBR_day(), CFBR_month())[0]
                    if order is not None:
                        write_new_order(username, order, current_stars)

            if order is not None:
                Logger.log(f"SUCCESS,{what_day_is_it()},{CFBR_day()}-{CFBR_month()},{username},Order: {order}")
            else:
                Logger.log(f"NO ORDER,{what_day_is_it()},{CFBR_day()}-{CFBR_month()},{username}")

            try:
                if confirmation:
                    # TODO: If a user sits on the order-confirmation page for a long enough time, they could
                    # "confirm" yesterday's order but it'd be written as today's.  Fix this by updating the
                    # query parameters to include the season/day
                    Logger.log(f"SUCCESS,{what_day_is_it()},{CFBR_day()}-{CFBR_month()},{username},Order confirmed! Yay.")
                    confirm_order(username)
                    resp = make_response(render_template('confirmation.html',
                                                         username=username))
                else:
                    resp = make_response(render_template('order.html',
                                                         username=username,
                                                         current_stars=current_stars,
                                                         total_turns=total_turns,
                                                         hoy=hoy,
                                                         order=order,
                                                         confirm_url=CONFIRM_URL))
                resp.set_cookie('a', access_token.encode())
            except Exception as e:
                error = "Go sign up for CFB Risk."
                Logger.log(f"ERROR,{what_day_is_it()},{CFBR_day()}-{CFBR_month()},{username},Reddit user who doesn't play CFBR tried to log in")
                Logger.log(f"  ERROR,unknown,Exception in get_next_order:{e}")
                resp = make_response(render_template('error.html', username=username,
                                                     error_message=error,
                                                     link="https://www.collegefootballrisk.com/"))
            return resp


@app.route(REDDIT_CALLBACK_ROUTE)
def reddit_callback():
    error = request.args.get('error', '')
    if error:
        return "Error: " + error
    state = request.args.get('state', '')
    if not is_valid_state(state):
        # Uh-oh, this request wasn't started by us!
        Logger.log(f"ERROR,,{CFBR_day()}-{CFBR_month()},{what_day_is_it()}unknown,403 from Reddit Auth API. WTF bro.")
        abort(403)
    code = request.args.get('code')
    access_token = get_token(code)

    response = make_response(redirect('/'))
    response.set_cookie('a', access_token.encode())
    return response

###############################################################
#
# Functions to handle order logic
#
###############################################################

def get_next_orders(hoy_d, hoy_m, num_orders=1):
    # This is sorted by tier and then least-filled within the tier.
    round_orders = get_orders(hoy_d, hoy_m)
    rv = []

    # Now all we need to do is find the first 'x' sets of orders that aren't already complete, if they exist...
    for candidate in round_orders:
        if candidate['pct_complete'] < 1:
            rv.append(candidate['territory'])
        if len(rv) >= num_orders:
            return rv

    # ...and if they need more orders than we've already pulled, we'll just tell them to go with the Tier 1 targets with the
    # lowest percentage completion (which will already be over 100%, since we got here in the first place)
    for candidate in round_orders:
        territory = candidate['territory']
        if not territory in rv:
            rv.append(territory)
        if len(rv) >= num_orders:
            return rv

    # It's theoretically possible that we have less possible total orders than are requested; if we made it this far,
    # return whatever we've got
    return rv



def get_orders(hoy_d, hoy_m):
    query = '''
        SELECT
            name,
            tier,
            quota,
            assigned,
            pct_complete
        FROM (
            SELECT
                t.name,
                p.season,
                p.day,
                p.tier,
                p.quota,
                0 as assigned,
                0 as pct_complete
            FROM plans p
                INNER JOIN territory t ON p.territory=t.id
            WHERE
                NOT EXISTS (SELECT * FROM orders o
                                WHERE p.territory = o.territory
                                    AND p.season=o.season
                                    AND p.day=o.day
                                    AND o.accepted=TRUE)
            UNION ALL
            SELECT
                t.name,
                p.season,
                p.day,
                p.tier,
                p.quota,
                SUM(o.stars) AS assigned,
                stars / CAST(p.quota AS REAL) AS pct_complete
            FROM plans p
                INNER JOIN territory t ON p.territory=t.id
                LEFT JOIN orders o ON (
                    p.territory = o.territory
                    AND p.season = o.season
                    AND p.day = o.day
                    )
            WHERE
                o.accepted=TRUE
            GROUP BY
                p.territory, p.season, p.day
        )
        WHERE
            season = ?
            AND day = ?
        ORDER BY
            tier ASC,
            pct_complete ASC;
    '''
    res = get_db().execute(query, (hoy_m, hoy_d))
    orders = []
    for row in res:
        territory, tier, quota, assigned, pct_complete = row
        orders.append({
            'territory': territory,
            'tier': tier,
            'quota': quota,
            'assigned': assigned,
            'pct_complete': pct_complete
        })
    res.close()
    return orders


def get_tiers(orders):
    return max(x['tier'] for x in orders.values())



def get_assigned_orders(hoy_d, hoy_m):
    query = '''
        SELECT
            t.name,
            SUM(o.stars) as stars
        FROM orders o
            INNER JOIN territory t ON o.territory=t.id
        WHERE
            season=?
            AND day=?
            AND accepted=TRUE
        GROUP BY t.name
        ORDER BY stars DESC
        '''
    res = get_db().execute(query, (hoy_m, hoy_d))
    territory_moves = dict(res.fetchall())
    res.close()
    return territory_moves


def user_already_assigned(username, hoy_d, hoy_m):
    query = '''
        SELECT
            t.name
        FROM orders o
            INNER JOIN territory t ON o.territory=t.id
        WHERE
            user=?
            AND season=?
            AND day=?
        LIMIT 1
    '''
    res = get_db().execute(query, (username, hoy_m, hoy_d))
    cmove = res.fetchone()
    res.close()

    return None if cmove is None else cmove[0]


def get_foreign_order(team, hoy_d, hoy_m):
    query = '''
        SELECT
            t.name,
            SUM(o.stars) as stars
        FROM orders o
            INNER JOIN territory t ON o.territory=t.id
        WHERE
            team=?
            AND season=?
            AND day=?
        GROUP BY t.name
        ORDER BY stars DESC
    '''
    res = get_db().execute(query, (team, hoy_m, hoy_d))
    fmove = res.fetchone()
    res.close()

    # If all else fails, default to the most primal hate
    return "Columbus" if fmove is None else fmove[0]


def write_new_order(username, order, current_stars):
    query = '''
        INSERT INTO orders (season, day, user, territory, stars)
        VALUES (?, ?, ?,
            (SELECT id FROM territory WHERE name=?),
        ?)
    '''
    db = get_db()
    db.execute(query, (CFBR_month(), CFBR_day(), username, order, current_stars))
    db.commit()


def confirm_order(username):
    query = '''
        UPDATE orders
            SET accepted=TRUE
        WHERE
            user=?
            AND season=?
            AND day=?
    '''
    db = get_db()
    db.execute(query, (username, CFBR_month(), CFBR_day()))
    db.commit()

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
# Database -- taken from https://flask.palletsprojects.com/en/2.2.x/patterns/sqlite3/
#
###############################################################


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB)
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

###############################################################
#
# Let's go!!!!
#
###############################################################


if __name__ == '__main__':
    app.run(debug=True, port=HTTP_PORT)
