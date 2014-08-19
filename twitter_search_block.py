import requests
import json
import oauth2 as oauth2
from nio.common.block.base import Block
from nio.common.discovery import Discoverable, DiscoverableType
from nio.metadata.properties.string import StringProperty
from nio.metadata.properties.timedelta import TimeDeltaProperty
from nio.metadata.properties.int import IntProperty
from nio.metadata.properties.object import ObjectProperty
from nio.metadata.properties.holder import PropertyHolder
from nio.modules.scheduler import Job


VERIFY_CREDS_URL = ('https://api.twitter.com/1.1/'
                    'account/verify_credentials.json')
SEARCH_URL = 'https://api.twitter.com/1.1/search/tweets.json'


class TwitterCreds(PropertyHolder):

    """ Property holder for Twitter OAuth credentials.

    """
    consumer_key = StringProperty(title='Consumer Key')
    app_secret = StringProperty(title='App Secret')
    oauth_token = StringProperty(title='OAuth Token')
    oauth_token_secret = StringProperty(title='OAuth Token Secret')


class GeoCode(PropertyHolder):
    """ Property holder for a latitude and longitude

    """
    latitude = StringProperty(title="Latitude")
    longitude = StringProperty(title="Longitude")
    radius = StringProperty(title="Radius (miles)")


class TwitterAPIBlock(Block):
    
    interval = TimeDeltaProperty(title="Query Interval", default={"minutes": 10})
    query = StringProperty(title="Query")
    geo = ObjectProperty(GeoCode, title="Geographical")
    count = IntProperty(title="Max Results", default=25)
    
    creds = ObjectProperty(TwitterCreds, title="Credentials")

    def __init__(self):
        self._url = None
        self._search_job = None
    
    def start(self):
        super().start()
        self. _url = self._construct_query()
        self._authorize()
        self._search_job = Job(
            self._search_tweets,
            self.interval
            True
        )

    def stop(self):
        self._search_job.cancel()

    def search_tweets(self):
        rsp = requests.get(self._url)
        if rsp.status_code == 200:
            data = rsp.json()
            self.notify_signals([Signal(t) for t in data])
        else:
            self._logger.error("FUCK YOU")
            print(rsp.text)

    def _construct_query(self):
        url = "{0}?".format(SEARCH_URL)
        
        if self.query:
            url = "{0}q={1}&".format(url, self.query)
        if self.geo:
            url = "{0}geo={1},{2},{3}mi&".format(url, self.geo.latitude,
                                                 self.geo.longitude,
                                                 self.geo.radius)
        if self.count:
            url = "{0}count={1}&".format(url, self.count)
            

    def _authorize(self):
        """ Prepare the OAuth handshake and verify.

        """
        try:
            auth = OAuth1(self.creds.consumer_key,
                          self.creds.app_secret,
                          self.creds.oauth_token,
                          self.creds.oauth_token_secret)
            resp = requests.get(VERIFY_CREDS_URL, auth=auth)
            if resp.status_code != 200:
                raise Exception("Status %s" % resp.status_code)
        except Exception:
            self._logger.error("Authentication Failed"
                               "for consumer key: %s" %
                               self.creds.consumer_key)
        
    
