from flask import Flask, abort, request, make_response, redirect, g
import requests
import requests.auth
from uuid import uuid4
import urllib
from datetime import datetime, timedelta
from flask import render_template
import math
import statistics
from pytz import timezone
from dotenv import dotenv_values
import sqlite3

app = Flask(__name__)
config = dotenv_values('.env')

###############################################################
#
# Functions to handle routes
#
###############################################################

@app.route('/')
def homepage():
    access_token = request.cookies.get('a')
    confirmation = request.args.get('confirmed', default = 0, type = int)

    log = get_log_file()

    if (access_token == None):
        header1 = "Welcome to Central Command!"
        link = make_authorization_url()

        resp = make_response(render_template('auth.html', title='What Are My Orders?', header=header1, authlink=link))
        return resp
    else:
        headers = {"Authorization": "bearer " + access_token, 'User-agent': 'CFB Risk Orders'}
        response = requests.get(config['REDDIT_ACCOUNT_URI'], headers=headers)
        if (response.status_code == 401):
            log.write("Error,"+access_token+",401 Error from CFBR API\n" )
            header1 = "Welcome to Central Command!"
            link = make_authorization_url()
            resp = make_response(render_template('auth.html', title='What Are My Orders?', header=header1, authlink=link))
            return resp
        else:
            # Let's get the basics
            username = get_username(access_token)
            hoy = what_day_is_it()

            # Let's get this user's CFBR info
            response = requests.get(f"{config['CFBR_REST_API']}/player?player={username}")
            active_team = response.json()['active_team']['name']
            current_stars = response.json()['ratings']['overall']

            order_msg = ""
            display_button = False
            # Enemy rogue or SPY!!!! Just give them someone to attack.
            if active_team != config['THE_GOOD_GUYS']:
                order_msg = "Your order is to attack/defend "
                order = get_foreign_order(active_team, CFBR_day(), CFBR_month())
            # Good guys get their assignments here
            else:
                order = get_next_order(CFBR_day(), CFBR_month(), username, current_stars)
                existing_assignment = user_already_assigned(username, CFBR_day(), CFBR_month())

                if order is None:
                    order_msg = "Orders have not been loaded for today. Please check back later."
                    order = ""
                elif existing_assignment is not None: # Already got an assignment today.
                    order_msg = "Your order is to attack/defend "
                    order = existing_assignment
                else: # Newly made assignment
                    order_msg = "Your order is to attack/defend "
                    write_new_order(username, order, current_stars)
                    display_button = True

            log.write("SUCCESS,"+what_day_is_it()+","+CFBR_day()+"-"+CFBR_month()+","+username+ ",Order: "+order_msg+order+"\n")
            header1 = "Greetings, " + username

            try:
                div1 = "I see you are a "+ str(current_stars) + " star. Thank you for your commitment."
                div2 = "Today is " + hoy + ".  " +order_msg
                if confirmation == 1:
                    div1 = "Thank you for confirming your order. Good luck out there, soldier."
                    log.write("SUCCESS,"+what_day_is_it()+","+CFBR_day()+"-"+CFBR_month()+","+username+",Order confirmed! Yay.\n")

                resp = make_response(render_template('index.html', title='What Are My Orders?', header=header1, div1=div1, div2=div2, order=order, display_button=display_button))
                resp.set_cookie('a', access_token.encode())
            except Exception as e:
                div1 = "Go sign up for CFB Risk."
                log.write("ERROR,"+what_day_is_it()+","+CFBR_day()+"-"+CFBR_month()+","+username+",Reddit user who doesn't play CFBR tried to log in\n")
                log.write("  ERROR,unknown,Exception in get_next_order:"+str(e)+"\n")
                resp = make_response(render_template('index.html', title='What Are My Orders?', header=header1, div1=div1))
            return resp

@app.route('/reddit_callback')
def reddit_callback():
    error = request.args.get('error', '')
    if error:
        return "Error: " + error
    state = request.args.get('state', '')
    if not is_valid_state(state):
        # Uh-oh, this request wasn't started by us!
        log = get_log_file()
        log.write("ERROR,"+","+CFBR_day()+"-"+CFBR_month()+","+what_day_is_it()+"unknown,403 from Reddit Auth API. WTF bro.\n")
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

def get_next_order(hoy_d, hoy_m, username, current_stars):
    log = get_log_file()
    # Get already assigned moves
    assigned_orders = get_assigned_orders(hoy_d, hoy_m)

    # Get the orders for this round and count tiers
    round_orders = get_orders(hoy_d, hoy_m)
    tiers = get_tiers(round_orders)

    # For each tier, calculate denom and figure out lowest % complete,
    # if tier 1 store floor, if lowest in tier below 100% then return,
    # if lowest in tier above 100% and last tier then return floor
    floor_terr = ""
    for i in range(1, tiers+1):
        lowest_score = 999999
        lowest_terr = ""
        for rorder in round_orders:
            if int(round_orders[rorder][0]) == i:
                if rorder in assigned_orders:
                    if int(assigned_orders[rorder]) / int(round_orders[rorder][1]) < lowest_score:
                        lowest_score = int(assigned_orders[rorder]) / int(round_orders[rorder][1])
                        lowest_terr = rorder
                else:
                    lowest_score = 0
                    lowest_terr = rorder

        if i == 1:
            floor_terr = lowest_terr

        if lowest_score < 1:
            return lowest_terr

        if (i == tiers) and (lowest_score >= 1):
            return floor_terr

def get_orders(hoy_d, hoy_m):
    query = '''
        SELECT
            t.name,
            p.tier,
            p.quota
        FROM plans p
            INNER JOIN territory t on p.territory=t.id
        WHERE
            season=?
            AND day=?
        ORDER BY 
            p.tier ASC, 
            p.quota DESC
    '''
    res = get_db().execute(query, (hoy_m, hoy_d))
    round_orders = {}
    for row in res:
        territory, tier, stars = row
        round_orders[territory] = [tier, stars]
    res.close()
    return round_orders

def get_tiers(orders):
    tiers = 0
    for order in orders:
        if int(orders[order][0]) > tiers:
            tiers = int(orders[order][0])
    return tiers

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

    return None if cmove == None else cmove[0]

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
    return "Columbus" if fmove == None else fmove[0]

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

###############################################################
#
# Functions to handle time
#
###############################################################

def CFBR_month():
    tz = timezone('EST')
    today = datetime.now(tz)
    hour = int(today.strftime("%H"))
    min = int(today.strftime("%M"))

    if ((hour == 23) or ((hour == 22) and (min >29))):
        today = datetime.now(tz) + timedelta(days = 1)
    if today.strftime("%A") == "Sunday":
        today = today + timedelta(days = 1)

    return today.strftime("%-m")

def CFBR_day():
    tz = timezone('EST')
    today = datetime.now(tz)
    hour = int(today.strftime("%H"))
    min = int(today.strftime("%M"))

    if ((hour == 23) or ((hour == 22) and (min >29))):
        today = datetime.now(tz) + timedelta(days = 1)
    if today.strftime("%A") == "Sunday":
        today = today + timedelta(days = 1)

    return today.strftime("%-d")

# Pretty date, for the user so not CFBR
def what_day_is_it():
    tz = timezone('EST')
    return(datetime.now(tz).strftime("%B %d, %Y"))

###############################################################
#
# Reddit API helper functions
#
###############################################################

def make_authorization_url():
    state = str(uuid4())
    save_created_state(state)
    params = {"client_id": config['REDDIT_CLIENT_ID'],
              "response_type": "code",
              "state": state,
              "redirect_uri": config['REDIRECT_URI'],
              "duration": "temporary",
              "scope": "identity"}
    url = f"{config['REDDIT_AUTH_URI']}?{urllib.parse.urlencode(params)}"
    return url

def save_created_state(state):
    pass
def is_valid_state(state):
    return True

def get_token(code):
    client_auth = requests.auth.HTTPBasicAuth(config['REDDIT_CLIENT_ID'], config['REDDIT_CLIENT_SECRET'])
    post_data = {"grant_type": "authorization_code",
                 "code": code,
                 "redirect_uri": config['REDIRECT_URI']}
    response = requests.post(config['REDDIT_TOKEN_URI'],
                             auth=client_auth,
                             headers = {'User-agent': 'CFB Risk Orders'},
                             data=post_data)
    token_json = response.json()
    return token_json['access_token']

def get_username(access_token):
    headers = {"Authorization": "bearer " + access_token, 'User-agent': 'CFB Risk Orders'}
    response = requests.get(config['REDDIT_ACCOUNT_URI'], headers=headers)
    me_json = response.json()
    return me_json['name']

###############################################################
#
# Functions for star calcs
#
###############################################################
def days_to_next_star(turns, current_stars, total_turns, game_turns, mvps, streak):
    if current_stars == 5:
        return -1
    turns = turns+1
    total_turns = total_turns+1
    game_turns = game_turns + 1
    streak = streak + 1
    if (current_stars < count_stars(total_turns, game_turns, mvps, streak)):
        return turns
    else:
        return days_to_next_star(turns, current_stars, total_turns, game_turns, mvps, streak)

# Function to count stars based on stats
def count_stars(total_turns, game_turns, mvps, streak):
    star1 = total_turn_stars(total_turns)
    star2 = game_turn_stars(game_turns)
    star3 = mvp_stars(mvps)
    star4 = streak_stars(streak)
    return math.ceil(statistics.median([star1, star2, star3, star4]))

# Count star level of streaks stat
def streak_stars(streak):
    stars = 1
    if(streak > 24):
        stars = 5
    elif(streak > 9):
        stars = 4
    elif(streak > 4):
        stars = 3
    elif(streak > 2):
        stars = 2
    return stars

# Count star level of mvps stat
def mvp_stars(mvps):
    stars = 1
    if(mvps > 24):
        stars = 5
    elif(mvps > 9):
        stars = 4
    elif(mvps > 4):
        stars = 3
    elif(mvps > 0):
        stars = 2
    return stars

# Count star level of game turns stat
def game_turn_stars(game_turns):
    stars = 1
    if(game_turns > 39):
        stars = 5
    elif(game_turns > 24):
        stars = 4
    elif(game_turns > 9):
        stars = 3
    elif (game_turns > 4):
        stars = 2
    return stars

# Count star level of total turns stat
def total_turn_stars(total_turns):
    stars = 1
    if(total_turns > 99):
        stars = 5
    elif(total_turns > 49):
        stars = 4
    elif(total_turns > 24):
        stars = 3
    elif(total_turns > 9):
        stars = 2
    return stars

###############################################################
#
# Filenames
#
###############################################################
def get_log_file():
    try:
        fname = f"{config['ROOT']}/files/log.txt"
        fs = open(fname, "a")
    except:
        return "Well, this is a problem. Someone tell the admin that the log file is corrupted."

    return fs

###############################################################
#
# Database -- taken from https://flask.palletsprojects.com/en/2.2.x/patterns/sqlite3/
#
###############################################################
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(config['DB'])
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
    app.run(debug=True, port=config['HTTP_PORT'])
