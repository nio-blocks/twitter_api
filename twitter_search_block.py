import requests
import json
from enum import Enum
from datetime import datetime, timedelta
from urllib.parse import quote
from requests_oauthlib import OAuth1
from nio.block.base import Block
from nio.signal.base import Signal
from nio.util.discovery import discoverable
from nio.properties.string import StringProperty
from nio.properties.timedelta import TimeDeltaProperty
from nio.properties.int import IntProperty
from nio.properties.list import ListProperty
from nio.properties.bool import BoolProperty
from nio.properties.select import SelectProperty
from nio.properties.object import ObjectProperty
from nio.properties.holder import PropertyHolder
from nio.modules.scheduler import Job
from nio.types import StringType


VERIFY_CREDS_URL = ('https://api.twitter.com/1.1/'
                    'account/verify_credentials.json')
SEARCH_URL = 'https://api.twitter.com/1.1/search/tweets.json'


class TwitterQueryOp(Enum):
    AND = " "
    OR = " OR "


class TwitterResultType(Enum):
    MIXED = "mixed"
    RECENT = "recent"
    POPULAR = "popular"


class TwitterAttitude(Enum):
    NEUTRAL = ""
    POSITIVE = ":)"
    NEGATIVE = ":("
    QUESTION = "?"


class TwitterCreds(PropertyHolder):

    """ Property holder for Twitter OAuth credentials.

    """
    consumer_key = StringProperty(title='Consumer Key',
                                  default='[[TWITTER_CONSUMER_KEY]]')
    app_secret = StringProperty(title='App Secret',
                                default='[[TWITTER_APP_SECRET]]')
    oauth_token = StringProperty(title='OAuth Token',
                                 default='[[TWITTER_OAUTH_TOKEN]]')
    oauth_token_secret = StringProperty(title='OAuth Token Secret',
                                        default='[[TWITTER_OAUTH_TOKEN_SECRET]]')


class GeoCode(PropertyHolder):
    """ Property holder for a latitude and longitude

    """
    latitude = StringProperty(title="Latitude", default='')
    longitude = StringProperty(title="Longitude", default='')
    radius = StringProperty(title="Radius (miles)", default='')


@discoverable
class TwitterSearch(Block):
    interval = TimeDeltaProperty(title="Query Interval",
                                 default={"minutes": 10})
    tweet_text = ListProperty(StringType, title="Text includes", default=[])
    hashtags = ListProperty(StringType, title="Hashtags", default=[])
    _from = StringProperty(title="From user", default='')
    _to = StringProperty(title="To user", default='')
    at = ListProperty(StringType, title="Referenced users", default=[])
    geo = ObjectProperty(GeoCode, title="Geographical")
    count = IntProperty(title="Max Results", default=25)
    lookback = IntProperty(title="Query Lookback (days)", default=-1)
    creds = ObjectProperty(TwitterCreds, title="Credentials")
    tude = SelectProperty(
        TwitterAttitude,
        default=TwitterAttitude.NEUTRAL,
        title="Tone"
    )
    operator = SelectProperty(
        TwitterQueryOp,
        default=TwitterQueryOp.AND,
        title="Query Operator"
    )
    result_type = SelectProperty(
        TwitterResultType,
        default=TwitterResultType.MIXED,
        title="Result Type"
    )

    def __init__(self):
        super().__init__()
        self._auth = None
        self._url = None
        self._search_job = None

    def configure(self, context):
        super().configure(context)

    def start(self):
        super().start()
        self._authorize()
        self._construct_url()
        self._search_job = Job(
            self._search_tweets,
            self.interval(),
            False,
            self._url
        )

    def stop(self):
        super().stop()
        self._search_job.cancel()

    def _search_tweets(self, url):
        rsp = requests.get(url, auth=self._auth)
        status = rsp.status_code
        if status == 200:
            data = rsp.json()
            tweets = data['statuses']
            next_results = data['search_metadata'].get('next_results')
            self.notify_signals([Signal(t) for t in tweets])
            if next_results is not None:
                self._search_tweets(
                    "{0}{1}".format(SEARCH_URL, next_results)
                )
            else:
                self.logger.debug("Scheduling next search...")
                self._search_job = Job(
                    self._search_tweets,
                    self.interval(),
                    False,
                    self._url
                )

        else:
            self.logger.error(
                "Twitter search failed with status {0}".format(status))

    def _construct_url(self):
        self._url = "{0}?".format(SEARCH_URL)

        query = self._process_query()

        if query:
            self._append_param('q', sep=self.operator().value, vals=query)

        if self.geo().latitude():
            self._append_param('geo', ',', 'mi',
                               [self.geo().latitude(),
                                self.geo().longitude(),
                                self.geo().radius()])

        if self.lookback() >= 0:
            now = datetime.utcnow() - timedelta(days=self.lookback())
            vals = [now.year, now.month, now.day]
            self._append_param('since', '-', vals=vals)

        if self.count():
            self._append_param('count', vals=[self.count()])

        self._append_param('result_type', vals=[self.result_type().value])

    def _append_param(self, p_name, sep='', end='', vals=[]):
        val_str = quote(sep.join([str(v) for v in vals]) + end)
        self._url += "{0}={1}&".format(p_name, val_str)

    def _process_query(self):
        values = []
        values.extend(self.tweet_text())
        for h in self.hashtags():
            values.append("#{0}".format(h))
        for u in self.at():
            values.append("@{0}".format(u))
        if self._from():
            values.append("from:{0}".format(self._from()))
        if self._to():
            values.append("to:{0}".format(self._to()))
        if self.tude().value:
            values.append(self.tude().value)
        return values

    def _authorize(self):
        """ Prepare the OAuth handshake and verify.

        """
        try:
            self._auth = OAuth1(self.creds().consumer_key(),
                          self.creds().app_secret(),
                          self.creds().oauth_token(),
                          self.creds().oauth_token_secret())
            resp = requests.get(VERIFY_CREDS_URL, auth=self._auth)
            if resp.status_code != 200:
                raise Exception("Status %s" % resp.status_code)
        except Exception as e:
            self.logger.error("Authentication Failed"
                               "for consumer key: %s" %
                               self.creds().consumer_key())
