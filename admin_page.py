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

        # You're in.  Let's tell you what's happening.
        orders = Orders.get_orders(hoy_d, hoy_m)
        if orders:

            cur_tier = -1
            running_totals = {
                "quota": 0,
                "assigned": 0,
            }
            overall_totals = {
                "quota": 0,
                "assigned": 0,
            }

            # We're duplicating the storage for the orders because a) it's small and b) it's easier to
            # understand building a second list vs. manipulating the length of an array that we're currently
            # looping over.  Blame Tapin.
            composite_orders = []
            for order in orders:
                # If necessary, put a summation row on the list and reset the running totals
                # NB we're not going to try to display tiers that have no territories assigned
                if order['tier'] != cur_tier and cur_tier > -1 and running_totals['quota'] > 0:
                    composite_orders.append({
                        "sumrow": True,
                        "tier": cur_tier,
                        "quota": running_totals['quota'],
                        "assigned": running_totals['assigned'],
                        "display_pct": '{:.1%}'.format(running_totals['assigned'] / running_totals['quota'])
                    })

                    running_totals = {
                        "quota": 0,
                        "assigned": 0,
                    }

                # Make a note of the quota & assigned for both the running and overall totals
                running_totals['quota'] += order['quota']
                running_totals['assigned'] += order['assigned']
                overall_totals['quota'] += order['quota']
                overall_totals['assigned'] += order['assigned']

                # Format the display, since we don't need infinite precision
                order['display_pct'] = '{:.1%}'.format(order['pct_complete'])

                # Put this order on the list we're going to display
                composite_orders.append(order)

                cur_tier = order['tier']

            # Now that we're done, if we had anything to show then we still have the tier sum row
            # and the overall totals to display
            if running_totals['quota'] > 0:
                composite_orders.append({
                    "sumrow": True,
                    "tier": cur_tier,
                    "quota": running_totals['quota'],
                    "assigned": running_totals['assigned'],
                    "display_pct": '{:.1%}'.format(running_totals['assigned'] / running_totals['quota'])
                })

            if overall_totals['quota'] > 0:
                overall_totals['display_pct'] = '{:.1%}'.format(overall_totals['assigned'] / overall_totals['quota'])


        return make_response(render_template('admin.html',
                                             orders=composite_orders,
                                             totals=overall_totals))

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
