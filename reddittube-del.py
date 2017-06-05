#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import httplib2
import sys
from apiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run_flow
import configparser


config = configparser.ConfigParser()
filedir = os.path.dirname(os.path.abspath(__file__))
if os.path.exists('{}/userinfo.ini'.format(filedir)):
    config.read('userinfo.ini')
    username = config['reddit']['username']
else:
    print('Couldn\'t find the config file, bruh. Check out the readme on '
          'github?')
    sys.exit()

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
    '''
    Authorize the request and store authorization credentials.
    '''
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

    return res


res = fetch_all_youtube_videos(desired_playlist)

if res['items'] == []:
    print('Playlist is empty. Quitting.')
    sys.exit()

no_of_vids = len(res['items'])
if no_of_vids > 1:
    video_or_videos = 's'
else:
    video_or_videos = ''
print('Found {} video{}.'.format(no_of_vids, video_or_videos))

i = 0
for item in res['items']:
    # Delete video
    try:
        i += 1
        youtube.playlistItems().delete(id=item['id']).execute()
        print('{} of {}: Deleted the video \'{}\''.format(i, no_of_vids,
              item['snippet']['title']))
    except:
        print('Error! Couldn\'t delete \'{}\''.format(
              item['snippet']['title']))
