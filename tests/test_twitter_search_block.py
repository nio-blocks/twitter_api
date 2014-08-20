from ..twitter_search_block import TwitterSearch
from unittest.mock import patch
from requests_oauthlib import OAuth1
from requests import Response
from nio.util.support.block_test_case import NIOBlockTestCase
from nio.modules.threading import Event


class TSTestBlock(TwitterSearch):
    def __init__(self, event):
        super().__init__()
        self._event = event

    def _search_tweets(self, url):
        super()._search_tweets(url)
        self._event.set()

    def _authorize(self):
        self._auth = OAuth1('foo', 'bar', 'baz', 'qux')


class TestTwitterSearch(NIOBlockTestCase):
    
    @patch("requests.get")
    @patch("requests.Response.json")
    def test_produce_response(self, mock_json, mock_get):
        mock_get.return_value = Response()
        mock_get.return_value.status_code = 200
        mock_json.return_value = {
            'statuses': [
                {'some': 'tweet'},
                {'some': 'other'}
            ],
            'search_metadata': {}
        }
        e = Event()
        blk = TSTestBlock(e)
        self.configure_block(blk, {
            'interval': {
                'milliseconds': 500
            }
        })
        blk.start()
        e.wait(1)
        self.assert_num_signals_notified(2)
        blk.stop()

    @patch("requests.get")
    @patch("requests.Response.json")
    def test_complex_query(self, mock_json, mock_get):
        e = Event()
        blk = TSTestBlock(e)
        expected_url = ("https://api.twitter.com/1.1/search/tweets.json?q=some"
                        "%20OR%20text%20OR%20%23foo%20OR%20%23bar%20OR%20%40me"
                        "%20OR%20%40you%20OR%20from%3AAlan&count=25&result_type"
                        "=mixed&")
        self.configure_block(blk, {
            'interval': {
                'seconds': 2
            },
            'operator': 'OR',
            'hashtags': ['foo', 'bar'],
            'at': ['me', 'you'],
            'tweet_text': ['some', 'text'],
            '_from': 'Alan'
        })
        blk.start()
        e.wait(.5)
        self.assertEqual(expected_url, blk._url)
