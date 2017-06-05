# reddittube
Look for YouTube-videos in submissions or comments in specific subreddits and add them to a playlist on YouTube.

&nbsp;

## Config


### OAuth
reddittube uses OAuth to authorize against both reddit and YouTube.
[How to set up reddit OAuth](http://praw.readthedocs.io/en/latest/getting_started/authentication.html)

[How to set up Youtube OAuth](https://developers.google.com/youtube/v3/guides/authentication)


### userinfo.ini

The individual scripts uses configuration from the `userinfo.ini`. An example file is included (`userinfo_example.ini`).

&nbsp;

## Use

Add videos by running `python reddittube-add.py`.

Delete all videos in playlist by running `python reddittube-del.py`.

&nbsp;

## Todo

- [ ] Make a webpage with embedded player according to [this comment on reddit](https://www.reddit.com/r/learnpython/comments/6el9c7/autopurging_a_youtube_playlist_after_watching/dib66p5/) for easier management of selective deleting videos from playlist