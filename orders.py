from cfbr_db import Db
from uuid import uuid4

###############################################################
#
# Functions to handle order logic
#
###############################################################

class Orders:
    @staticmethod
    def get_next_offers(hoy_d, hoy_m, num_orders=1):
        # This is sorted by tier and then least-filled within the tier.
        round_orders = Orders.get_orders(hoy_d, hoy_m)
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

    @staticmethod
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
                    SUM(o.stars) / CAST(p.quota AS REAL) AS pct_complete
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
                    p.territory, p.season, p.day, p.tier
            )
            WHERE
                season = ?
                AND day = ?
            ORDER BY
                tier ASC,
                pct_complete ASC;
        '''
        res = Db.get_db().execute(query, (hoy_m, hoy_d))
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

    @staticmethod
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
        res = Db.get_db().execute(query, (hoy_m, hoy_d))
        territory_moves = dict(res.fetchall())
        res.close()
        return territory_moves

    @staticmethod
    def user_already_moved(username, hoy_d, hoy_m):
        query = '''
            SELECT
                t.name
            FROM orders o
                INNER JOIN territory t ON o.territory=t.id
            WHERE
                user=?
                AND season=?
                AND day=?
                AND accepted=TRUE
            LIMIT 1
        '''
        res = Db.get_db().execute(query, (username, hoy_m, hoy_d))
        cmove = res.fetchone()
        res.close()

        # The return value here will either be None or the territory name that the user acted on
        return None if cmove is None else cmove[0]

    @staticmethod
    def user_already_offered(username, hoy_d, hoy_m):
        query = '''
            SELECT
                t.name,
                o.uuid
            FROM offers o
                INNER JOIN territory t ON o.territory=t.id
            WHERE
                user=?
                AND season=?
                AND day=?
            ORDER BY
                rank ASC
        '''
        res = Db.get_db().execute(query, (username, hoy_m, hoy_d))
        cmove = res.fetchall()
        res.close()

        # The return value here will either be None or an array of tuples of the form (territory, order_uuid)
        return cmove

    @staticmethod
    def get_foreign_order(team, hoy_d, hoy_m):
        query = '''
            SELECT
                t.name,
            FROM enemy_plans e
                INNER JOIN territory t ON e.territory=t.id
            WHERE
                team=?
                AND season=?
                AND day=?
            GROUP BY t.name
            ORDER BY stars DESC
        '''
        res = Db.get_db().execute(query, (team, hoy_m, hoy_d))
        fmove = res.fetchone()
        res.close()

        # If all else fails, default to the most primal hate
        return "Columbus" if fmove is None else fmove[0]

    @staticmethod
    def write_new_offer(username, order, hoy_d, hoy_m, current_stars, rank):
        query = '''
            INSERT INTO offers (season, day, user, territory, stars, rank, uuid)
            VALUES (?, ?, ?,
                (SELECT id FROM territory WHERE name=?),
            ?, ?, ?)
        '''

        new_uuid = str(uuid4())

        db = Db.get_db()
        db.execute(query, (hoy_m, hoy_d, username, order, current_stars, rank, new_uuid))
        db.commit()

        return new_uuid

    @staticmethod
    def confirm_offer(username, hoy_d, hoy_m, uuid):
        query = '''
            INSERT INTO orders (
                season,
                day,
                user,
                territory,
                stars,
                accepted,
                uuid
            )
            SELECT
                season,
                day,
                user,
                territory,
                stars,
                TRUE,
                uuid
            FROM
                offers
            WHERE
                user=?
                AND season=?
                AND day=?
                AND uuid=?
        '''
        db = Db.get_db()
        cur = db.cursor()
        cur.execute(query, (username, hoy_m, hoy_d, uuid))
        nrows = cur.rowcount
        db.commit()

        if nrows > 0:
            # Now retrieve the territory name of the order so we can return it
            assigned_row = Orders.user_already_moved(username, hoy_d, hoy_m)
            # Returning "None" from here would mean something went seriously askew, since
            # we literally just assigned a row.  Which doesn't mean it won't happen!
            return None if assigned_row is None else assigned_row

        return None

    @staticmethod
    def get_day_and_tier_totals(hoy_d, hoy_m, tier):
        # For the record: We could do this in a single query, but that makes the logic much more
        # difficult to read and to maintain.  So I'm splitting it up so that you don't have to
        # be an SQL expert to understand it.  Note that this is absolutely going to be a slower
        # overall process than doing it in a single query, but we're not exactly working with
        # BiG DaTa here.

        # First: Get the quota total for the tier
        query = '''
            SELECT
                SUM(quota) as quota
            FROM
                plans
            WHERE
                season=?
                AND day=?
                AND tier=?
        '''
        res = Db.get_db().execute(query, (hoy_m, hoy_d, tier))
        # We'll always get a tuple back, but if it's (None,) we need to coerce that to zero
        quota = res.fetchone()[0] or 0
        res.close()

        # Next, get the assigned stars total
        query = '''
            SELECT
                SUM(stars) AS stars
            FROM
                orders o
            WHERE
                season=?
                AND day=?
                AND accepted=TRUE
                AND territory IN (
                    SELECT territory
                    FROM plans p
                    WHERE
                        p.season=o.season
                        AND p.day=o.day
                        AND p.tier=?
                    )
        '''
        res = Db.get_db().execute(query, (hoy_m, hoy_d, tier))
        # We'll always get a tuple back, but if it's (None,) we need to coerce that to zero
        assigned = res.fetchone()[0] or 0
        res.close()

        return (quota, assigned)

    @staticmethod
    def get_day_totals(hoy_d, hoy_m):
        # See the note on get_day_and_tier_totals for the reason why this is done as two separate
        # queries.

        # First: Get the quota total for the day.  This would look nicer if SUM(MAX(x)) worked.
        query = '''
            SELECT
                SUM(quota)
            FROM (
                SELECT
                    MAX(quota) as quota
                FROM
                    plans
                WHERE
                    season=?
                    AND day=?
                GROUP BY
                    territory
            )
        '''
        res = Db.get_db().execute(query, (hoy_m, hoy_d))
        # We'll always get a tuple back, but if it's (None,) we need to coerce that to zero
        quota = res.fetchone()[0] or 0
        res.close()

        # Next, get the assigned stars total
        query = '''
            SELECT
                SUM(stars) AS stars
            FROM
                orders o
            WHERE
                season=?
                AND day=?
                AND accepted=TRUE
                AND territory IN (
                    SELECT territory
                    FROM plans p
                    WHERE
                        p.season=o.season
                        AND p.day=o.day
                    )
        '''
        res = Db.get_db().execute(query, (hoy_m, hoy_d))
        # We'll always get a tuple back, but if it's (None,) we need to coerce that to zero
        assigned = res.fetchone()[0] or 0
        res.close()

        return (quota, assigned)
