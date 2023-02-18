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
        if not is_allowed(username):
            log.warn(f"{username}: They don't belong here!  Sending 'em to the root.")
            return make_response(redirect('/'))

        orders = Orders.get_orders(hoy_d, hoy_m)
        if orders:
            for order in orders:
                order['display_pct'] = '{:.1%}'.format(order['pct_complete'])
        return make_response(render_template('admin.html',
                                             orders=orders))

def is_allowed(user):
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
