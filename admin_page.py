from flask import make_response, redirect, render_template
from cfbr_db import Db
from logger import Logger
from orders import Orders


log = Logger.getLogger(__name__)


class Admin:
    @staticmethod
    def build_page(request, username, hoy_d, hoy_m):
        log.info(f"{username}: Admin page request")
        # First things first: are you allowed to be here?
        if not Admin.is_admin(username):
            log.warn(f"{username}: They don't belong here!  Sending 'em to the root.")
            return make_response(redirect('/'))

        composite_orders = []
        overall_totals = {
            "quota": 0,
            "assigned": 0,
            "display_pct": "0%"
        }

        # What day did you request?
        elegido_m, elegido_d = (hoy_m, hoy_d)
        display_date = request.args.get('date', default=None, type=str)
        if display_date:
            # This next line could go bad for a number of reasons.  It's an admin page,
            # I'm going to assume nobody's intentionally trying to break it.
            elegido_m, elegido_d = [int(x) for x in display_date.split('/')]

        # You're in.  Let's tell you what's happening.
        orders = Orders.get_orders(elegido_d, elegido_m)
        if orders:
            cur_tier = -1

            # We're duplicating the storage for the orders because a) it's small and b) it's easier to
            # understand building a second list vs. manipulating the length of an array that we're currently
            # looping over.  Blame Tapin.
            for order in orders:
                # If necessary, put a summation row on the list and reset the running totals
                # NB we're not going to try to display tiers that have no territories assigned
                if order['tier'] != cur_tier and cur_tier > -1:
                    composite_orders.append(display_sum_row(elegido_d, elegido_m, cur_tier))

                # Format the display, since we don't need infinite precision
                order['display_pct'] = '{:.1%}'.format(order['pct_complete'])

                # Put this order on the list we're going to display
                composite_orders.append(order)

                cur_tier = order['tier']

            # Now that we're done, we have to put out the final tier total and the overall total
            composite_orders.append(display_sum_row(elegido_d, elegido_m, cur_tier))

            total_quota, total_assigned = Orders.get_day_totals(elegido_d, elegido_m)
            if total_quota > 0:
                overall_totals['quota'] = total_quota
                overall_totals['assigned'] = total_assigned
                overall_totals['display_pct'] = '{:.1%}'.format(total_assigned / total_quota)

        dropdown_dates = populate_date_dropdown()
        pagedate = f"{elegido_m}/{elegido_d}"
        # If orders aren't loaded yet, we need to cheat with the dropdown_dates
        if pagedate not in dropdown_dates:
            dropdown_dates.insert(0, pagedate)

        return make_response(render_template('admin.html',
                                             orders=composite_orders,
                                             totals=overall_totals,
                                             dates=dropdown_dates,
                                             pagedate=pagedate))

    @staticmethod
    def is_admin(user):
        query = '''
            SELECT
                role
            FROM
                users
            WHERE
                user=?
            LIMIT 1
        '''
        res = Db.get_db().execute(query, (user,))
        roleid_row = res.fetchone()
        res.close()

        if roleid_row is None or roleid_row[0] < 4:
            return False
        return True

def display_sum_row(hoy_d, hoy_m, tier):
    quota, assigned = Orders.get_day_and_tier_totals(hoy_d, hoy_m, tier)
    nterritories, ncompleted = Orders.get_tier_territory_summary(hoy_d, hoy_m, tier)
    if quota > 0:
        return {
            "sumrow": True,
            "tier": tier,
            "quota": quota,
            "assigned": assigned,
            "display_pct": '{:.1%}'.format(assigned / quota),
            "nterritories": nterritories,
            "ncompleted": ncompleted,
            "completed_pct": '{:.1%}'.format(ncompleted / nterritories)
        }

def populate_date_dropdown():
    query = '''
        SELECT DISTINCT season, day
        FROM plans
        ORDER BY season, day;
    '''
    res = Db.get_db().execute(query)
    dropdown_values = [f"{x[0]}/{x[1]}" for x in res.fetchall()]
    res.close()

    # Since we're more likely to be using dates that are recent, let's invert the order.  Doing
    # this here instead of in the SQL so that a) it's explicit that this was a choice; and b) to
    # make it trivial to go back when I change my mind.
    dropdown_values.reverse()

    return dropdown_values
