Twitter Search
================
A block that searches Twitter statuses.

Properties
-------------
* **consumer_key**: Twitter API key
* **app_secret**: Twitter API secret
* **oauth_token**: Twitter access token
* **oauth_token_secret**: Twitter access token secret
* **latitude**: latitude for location to search for tweets
* **longitude**: longitude for location to search for tweets
* **radius**: how far from `latitude` and `longitude` position to search for tweets
* **interval**: how often the API is polled
* **tweet_text**: keywords to search for in tweets
* **hashtags**: hashtags to search for in tweets
* **_from**: user's tweets to search
* **_to**: search tweets to this user
* **at**: list of users who were referenced in tweets using `@` character
* **count**: maximum tweets to notify from search results
* **lookback**: how far to look back for tweets
* **tude**: choose from `NEUTRAL`, `QUESTION`, `NEGATIVE` and `POSITIVE` to specify the tone of the tweets that should be notified from block
* **operator**: choose between `AND` and `OR`
* **result_type**: choose between `POPULAR`, `RECENT` or `MIXED` to specify what types of tweets to notify from search

Dependencies
-------------
None.

Commands
-------------
None.

Input
-------------
Any list of signals.

Output
-------------
The following is an example of the output signals notified from the block after the Twitter API is searched with the configurable criteria. Note that there may be more attributes output than what is listed below, and not all of the listed attributes are guaranteed to be included on every signal.

```
{
  statuses: [
    {
      coordinates: string
      favorited: boolean,
      created_at: datetime,
      text: string,
      metadata: {
        iso_language_code: string,
        result_type: string
      },
      retweet_count: int,
      geo: null,
      retweeted: boolean,
      user: {
        name: string,
        profile_image_url: string,
        created_at: string,
        location: string,
        id: int,
        followers_count: int,
        protected: boolean,
        geo_enabled: boolean,
        description: string,
        statuses_count: int,
        friends_count: int,
      },
    },
    ...
  ],
}
```
