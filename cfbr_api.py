import requests
import json
from constants import CFBR_REST_API
from logger import Logger

log = Logger.getLogger(__name__)

class CfbrApi:
    @staticmethod
    def get_cur_turn():
        """
        :returns: tuple (season, day)
        """

        resp = requests.get(f"{CFBR_REST_API}/turns")
        resp.raise_for_status()

        all_turns = resp.json()

        try:
            filter_obj = filter(lambda x: x['active'], all_turns)
            active_turn = list(filter_obj)[0]
            return (active_turn['season'], active_turn['day'])
        except:
            log.error("No active turn!")

        return (None,)

    @staticmethod
    def get_territories(hoy_d, hoy_m):
        '''
        :returns: array of CFBR territory objects
        '''

        resp = requests.get(f"{CFBR_REST_API}/territories?day={hoy_d}&season={hoy_m}")
        resp.raise_for_status()

        return resp.json()
