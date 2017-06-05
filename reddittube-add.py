#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import httplib2
import sys
from time import sleep as sleep
import re
import praw
import configparser
from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run_flow

# Sets up the reddit oAuth, gets info from config-file
config = configparser.ConfigParser()
filedir = os.path.dirname(os.path.abspath(__file__))
if os.path.exists('{}/userinfo.ini'.format(filedir)):
    config.read('userinfo.ini')
    username = config['reddit']['username']
else:
    print('Couldn\'t find the config file, bruh. Check out the readme on '
          'github?')
    sys.exit()
# Authenticates to reddit through praw
r = praw.Reddit(client_id=config['reddit']['client_id'],
                client_secret=config['reddit']['client_secret'],
                password=config['reddit']['password'],
                user_agent=config['reddit']['useragent'],
                username=config['reddit']['username'])

# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret.
CLIENT_SECRETS_FILE = "client_secret.json"

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account and requires requests to use an SSL connection.
YOUTUBE_READ_WRITE_SSL_SCOPE = "https://www.googleapis.com/auth/youtube"
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"

# This variable defines a message to display if the CLIENT_SECRETS_FILE is
# missing.
MISSING_CLIENT_SECRETS_MESSAGE = "WARNING: Please configure OAuth 2.0"


def get_authenticated_service():
    '''Authorize the request and store authorization credentials to YouTube'''
    flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE,
                                   scope=YOUTUBE_READ_WRITE_SSL_SCOPE,
                                   message=MISSING_CLIENT_SECRETS_MESSAGE)

    storage = Storage("%s-oauth2.json" % sys.argv[0])
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage)

    # Trusted testers can download this discovery document from the
    # developers page and it should be in the same directory with the code.
    return build(API_SERVICE_NAME, API_VERSION,
                 http=credentials.authorize(httplib2.Http()))


youtube = get_authenticated_service()
desired_playlist = config['reddit']['desired_playlist']


def add_video_to_playlist(videoID):
    global youtube, desired_playlist
    youtube.playlistItems().insert(
        part="snippet",
        body={'snippet': {'playlistId': desired_playlist,
                          'resourceId': {'kind': 'youtube#video',
                                         'videoId': videoID
                                         }
                          }
              }
    ).execute()


def fetch_all_youtube_videos(playlistId):
    """
    Fetches a playlist of videos from youtube
    We splice the results together in no particular order

    Parameters:
        parm1 - (string) playlistId
    Returns:res = youtube.playlistItems().list(part="snippet",
        playListItem Dict
    """
    global youtube
    res = youtube.playlistItems().list(
        part="snippet",
        playlistId=playlistId,
        maxResults="50"
    ).execute()

    nextPageToken = res.get('nextPageToken')
    while ('nextPageToken' in res):
        nextPage = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlistId,
            maxResults="50",
            pageToken=nextPageToken
        ).execute()
        res['items'] = res['items'] + nextPage['items']

        if 'nextPageToken' not in nextPage:
            res.pop('nextPageToken', None)
        else:
            nextPageToken = nextPage['nextPageToken']
    video_ids = []
    for vid in res['items']:
        vid_id = vid['snippet']['resourceId']['videoId']
        video_ids.append(vid_id)

    return video_ids


def get_duration(video_id):
    global youtube
    results = youtube.videos().list(
        part='contentDetails',
        id=video_id
    ).execute()
    days, hours, mins, secs = 0, 0, 0, 0
    try:
        duration = results['items'][0]['contentDetails']['duration']
    except:
        pass
    # Youtube uses the ISO 8601 standard for formatting duration:
    # "PT6M23S" represents a duration of "six minutes and twenty three
    # seconds."
    # "P3Y6M4DT12H30M5S" represents a duration of "three years, six
    # months, four days, twelve hours, thirty minutes, and five seconds".
    _days = '(\d+)D'
    _hours = '(\d+)H'
    _mins = '(\d+)M'
    _secs = '(\d+)S'
    try:
        days = int(re.search(_days, duration).group(1)) * 24 * 60 * 60
    except:
        days = 0
    try:
        hours = int(re.search(_hours, duration).group(1)) * 60 * 60
    except:
        hours = 0
    try:
        mins = int(re.search(_mins, duration).group(1)) * 60
    except:
        mins = 0
    try:
        secs = int(re.search(_secs, duration).group(1))
    except:
        secs = 0
    return days + hours + mins + secs


def subreddit_exist(subreddit):
    exist = None
    try:
        r.subreddits.search_by_name(subreddit, include_nsfw=True, exact=True)
        exist = True
    except:
        exist = False
    return exist


yt_regex = '.*youtu.*[/|watch?v=][\w-]{11}'
yt_comment_regex = 'youtu.*[/|watch?v=][\w-]{11}'
subreddits = config['reddit']['subreddits']
no_of_submissions = config['reddit']['no_of_submissions']
yt_videos = fetch_all_youtube_videos(desired_playlist)
videos_to_add = []

# Remove undesired symbols from subreddits-list
symbol_regex = r'[ \\,.:;\-\|\+\/"@\']+'
symbols = re.findall(symbol_regex, subreddits, flags=re.MULTILINE)
for symbol in symbols:
    subreddits = subreddits.replace(symbol, ',')
subreddits = subreddits.split(',')

if len(subreddits) > 1:
    sub_or_subs = 's'
else:
    sub_or_subs = ''
print('Found {} subreddit{} in config file'
      .format(len(subreddits), sub_or_subs))

subr_checked = []
for subr in subreddits:
    # Check if the subreddit exist
    if not subreddit_exist(subr):
        print('Subreddit \'{}\' doesn\'t exist. Skipping...'.format(subr))
    else:
        print('Subreddit \'{}\' exist and will be checked'.format(subr))
        subr_checked.append(subr)


for subr in subr_checked:
    i = 0
    subr = r.subreddit(subr)
    for submission in subr.new(limit=int(no_of_submissions)):
        i += 1
        print('Checking submission {}/{}: {}'
              .format(i, no_of_submissions, submission.shortlink))
        subm_yt = re.findall(yt_regex, submission.url)
        try:
            subm_videoid = str(subm_yt[0][len(subm_yt[0]) - 11:
                                          len(subm_yt[0])])
            # If there is no valid url or it already is in the playlist,
            # don't append it
            if subm_videoid == '':
                pass
            else:
                videos_to_add.append(subm_videoid)
                print('Added {} to pending list'.format(subm_videoid))
        except:
            subm_videoid = ''
        comments = submission.comments
        sleep(2)
        if len(comments) == 0:
            pass
        else:
            for comment in comments:
                text = comment.body
                comment_urls = re.findall(yt_comment_regex, text)
                for comment_url in comment_urls:
                    print('  Found {}'.format(comment_url))
                    comment_url = re.findall(yt_comment_regex, comment_url)
                    if isinstance(comment_url, list):
                        comm_videoid = str(
                            comment_url[0][len(comment_url[0]) - 11:
                                           len(comment_url[0])])
                    else:
                        comm_videoid = str(
                            comment_url[len(comment_url) - 11:
                                        len(comment_url)])
                    if comm_videoid == '':
                        pass
                    else:
                        videos_to_add.append(comm_videoid)
                        print('  Added {} to pending list'
                              .format(comm_videoid))

# Check duration of videos, if ok add to playlist
checked_videos = []
video_max_length = int(config['reddit']['video_max_length'])
# Check duration of each video. If below the limit set in config, add it to
# 'checked_videos'.
for video in videos_to_add:
    if video in yt_videos:
        print('Video {} is already in the playlist'.format(video))
        pass
    else:
        print('Adding video {} to playlist'.format(video))
        if video_max_length is not None or video_max_length is not 0:
            duration = get_duration(video)
            if duration > video_max_length:
                print('Video {} lasts longer than max length in settings'
                      .format(video))
                pass
            else:
                try:
                    add_video_to_playlist(video)
                except HttpError as e:
                    print('Couldn\'t add {}:\n{}'.format(video, e))
