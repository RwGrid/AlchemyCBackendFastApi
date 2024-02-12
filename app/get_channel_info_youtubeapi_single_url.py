# pip3 install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
import logging
import traceback
from time import sleep
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import urllib.parse as p
import re
import os
import pickle

# step 1, create a server to server service as instructions below
# https://developers.google.com/identity/protocols/oauth2/service-account
#step 2, add youtube api service to project enables apis
#https://console.cloud.google.com/apis/
#step 3, check out the analyticsyoutube api which is different from regular api
class YoutubeWrapper:
    def __init__(self, allow_comments:bool):
        self._SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
        # authenticate to YouTube API
        self.youtube = self.youtube_authenticate()
        self.allow_comments = allow_comments

    @staticmethod
    def service_account():

        scopes = ['https://www.googleapis.com/auth/sqlservice.admin',
                  "https://www.googleapis.com/auth/youtube.force-ssl"]
        service_account_file = './youtubeservertoservercra-ed96d3051901.json'
        service_account_file = './youtube_server_to_server.json'
        credentials = service_account.Credentials.from_service_account_file(
            service_account_file, scopes=scopes)
        return credentials

    def youtube_authenticate(self):
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
        api_service_name = "youtube"
        api_version = "v3"
        cred = YoutubeWrapper.service_account()
        return build(api_service_name, api_version, credentials=cred)
        # the file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first time
        if os.path.exists("token.pickle"):
            with open("token.pickle", "rb") as token:
                creds = pickle.load(token)
        # if there are no (valid) credentials availablle, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    fet_req = creds.refresh(Request())
                except Exception as ex:
                    logging.error(f'an error in fetching youtube api: {ex}')
                    os.unlink('token.pickle')
                    sleep(0.5)
                    self.youtube_authenticate()
            else:
                flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, self._SCOPES)
                creds = flow.run_local_server(open_browser=False)
            # save the credentials for the next run
            with open("token.pickle", "wb") as token:
                pickle.dump(creds, token)

        return build(api_service_name, api_version, credentials=creds)

    def get_comments(self, **kwargs):
        return self.youtube.commentThreads().list(
            part="snippet,replies",
            **kwargs
        ).execute()

    def scrap_comments_by_pages(self, params, comment_count):
        comments = []
        comments_and_replies = []
        while len(comments) < int(comment_count):
            # make API call to get all comments from the channel (including posts & videos)
            response = self.get_comments(**params)
            items = response.get("items")
            # if items is empty, breakout of the loop
            if not items:
                break
            for item in items:
                comment = {}
                comment['sentence'] = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                comment['updated_at'] = item["snippet"]["topLevelComment"]["snippet"]["updatedAt"]
                comment['like_count'] = item["snippet"]["topLevelComment"]["snippet"]["likeCount"]
                comment['comment_id'] = item["snippet"]["topLevelComment"]["id"]
                comments_and_replies.append(item["snippet"]["topLevelComment"]["snippet"]["textDisplay"])
                replycount = item['snippet']['totalReplyCount']
                replies = []
                # if reply is there
                if replycount > 0:

                    # iterate through all reply
                    for reply in item['replies']['comments']:
                        # Extract reply
                        reply = reply['snippet']['textDisplay']
                        comments_and_replies.append(reply)

                        # Store reply is list
                        replies.append(reply)
                    comment['replies'] = replies
                comments.append(comment)

            if "nextPageToken" in response:
                # if there is a next page
                # add next page token to the params we pass to the function
                params["pageToken"] = response["nextPageToken"]
            else:
                # must be end of comments!!!!
                break
            print("*" * 70)
        return comments, comments_and_replies

    def scrap_comments_all(self, params):
        video_response = self.youtube.commentThreads().list(
            part='snippet',
            videoId=params['video_id']
        ).execute()

        # iterate video response
        comments = []
        while video_response:
            replies = []

            # extracting required info
            # from each result object
            for item in video_response['items']:
                comment_obj = {}

                # Extracting comments
                comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
                comment_obj['text'] = comment
                # counting number of reply of comment
                replycount = item['snippet']['totalReplyCount']

                # if reply is there
                if replycount > 0:

                    # iterate through all reply
                    for reply in item['replies']['comments']:
                        # Extract reply
                        reply = reply['snippet']['textDisplay']

                        # Store reply is list
                        replies.append(reply)
                    comment_obj['replies'] = replies

                # print comment with list of reply
                comments.append(comment_obj)
                print(comment, replies, end='\n\n')

                # empty reply list
                replies = []

            # Again repeat
            if 'nextPageToken' in video_response:
                video_response = self.youtube.commentThreads().list(
                    part='snippet,replies',
                    videoId=params['video_id']
                ).execute()
            else:
                break

    @staticmethod
    def get_video_id_by_url(url: str):
        """
        utility method that accepts the url and parse into video id
        Return the Video ID from the video `url`
        """
        # split URL parts
        parsed_url = p.urlparse(url)
        # get the video ID by parsing the query of the URL
        video_id = p.parse_qs(parsed_url.query).get("v")
        if video_id:
            return {"video_id": video_id[0], "status": "success"}
        else:
            print((f"Wasn't able to parse video URL: {url}"))
            logging.warning("errorMessage Wasn't able to parse video URL")
            print(traceback.format_exc())
            return {"errorMessage": "Wasn't able to parse video URL", "status": "failed"}

            # pass
            # raise Exception(f"Wasn't able to parse video URL: {url}")

    def get_video_details(self, **kwargs):
        return self.youtube.videos().list(
            part="snippet,contentDetails,statistics",
            **kwargs
        ).execute()

    def get_video_infos(self, video_response):
        try:
            items = video_response.get("items")[0]
            # get the snippet, statistics & content details from the video response
            snippet = items["snippet"]
            try:
                channelId=snippet['channelId']
                part = 'statistics'
                request = self.youtube.channels().list(part=part, id=channelId)
                response = request.execute()
                subscriber_count = (response['items'][0]['statistics']['subscriberCount'])

            except Exception as exxas:
                print("couldnt get channel statistics")
            statistics = items["statistics"]
            content_details = items["contentDetails"]
            # get infos from the snippet
            channel_title = snippet["channelTitle"]
            title = snippet["title"]
            description = snippet["description"]
            publish_time = snippet["publishedAt"]
            # get stats infos
            comment_count = statistics["commentCount"]
            like_count = statistics["likeCount"]
            # dislike_count = statistics["dislikeCount"]
            view_count = statistics["viewCount"]
            # get duration from content details
            duration = content_details["duration"]
            # duration in the form of something like 'PT5H50M15S'
            # parsing it to be something like '5:50:15'
            parsed_duration = re.search(f"PT(\d+H)?(\d+M)?(\d+S)", duration)
            duration_str = ''
            if parsed_duration:
                parsed_duration = parsed_duration.groups()
                for d in parsed_duration:
                    if d:
                        duration_str += f"{d[:-1]}:"
                duration_str = duration_str.strip(":")
            youtube_info = dict()
            youtube_info['Youtube_Title'] = title
            youtube_info['Youtube_Publish time'] = publish_time
            youtube_info['Youtube_Duration'] = duration_str
            youtube_info['Youtube_Number_Of_Comments'] = comment_count
            youtube_info['Youtube_Number_Of_Likes'] = like_count
            youtube_info['Youtube_Number_Of_Views'] = view_count
            youtube_info['Youtube_Description'] = description
            youtube_info['Youtube_Channel_subscriber_count']=subscriber_count
            return youtube_info
        except KeyError as ke:
            print("> Cannot get video infos: " + str(ke))
            logging.error("> Cannot get video infos: " + str(ke))
            print(traceback.print_exc())
        except Exception as ex:
            print("> Cannot get video infos: " + str(ex))
            logging.error("> Cannot get video infos: " + str(ex))
            print(traceback.print_exc())
            ll = 0
        # print(f"""\
        # Title: {title}
        # Description: {description}
        # Channel Title: {channel_title}
        # Publish time: {publish_time}
        # Duration: {duration_str}
        # Number of comments: {comment_count}
        # Number of likes: {like_count}
        # Number of views: {view_count}
        # """)

    def get_youtube_info(self, url):
        counter = 0

        counter += 1

        youtube_info_dict = {}
        try:
            if "https://youtu.be/" in url:
                url = url.replace("https://youtu.be/", "https://youtu.be/watch?v=")
            if url == ' ' or url == '':
                youtube_info_dict['Youtube_Title'] = ' '
                youtube_info_dict['Youtube_Description'] = ' '
                youtube_info_dict['Youtube_Publish time'] = ' '
                youtube_info_dict['Youtube_Duration'] = ' '
                youtube_info_dict['Youtube_Number_Of_Comments'] = ' '
                youtube_info_dict['Youtube_Number_Of_Likes'] = ' '
                youtube_info_dict['Youtube_Number_Of_Views'] = ' '
                youtube_info_dict["Youtube_status"] = "failed"
                youtube_info_dict["Youtube_errorMessage"] = "no link is given"
            elif "ok.ru" in url:
                youtube_info_dict['Youtube_Title'] = ' '
                youtube_info_dict['Youtube_Description'] = ' '
                youtube_info_dict['Youtube_Publish time'] = ' '
                youtube_info_dict['Youtube_Duration'] = ' '
                youtube_info_dict['Youtube_Number_Of_Comments'] = ' '
                youtube_info_dict['Youtube_Number_Of_Likes'] = ' '
                youtube_info_dict['Youtube_Number_Of_Views'] = ' '
                youtube_info_dict["Youtube_status"] = "failed"
                youtube_info_dict["Youtube_errorMessage"] = "this link is russian"
            else:

                video_url = url
                # parse video ID from URL
                video_obj = YoutubeWrapper.get_video_id_by_url(video_url)

                params = {
                    'videoId': video_obj['video_id'],
                    'maxResults': 80,
                    'order': 'time',  # default is 'time' (newest)
                }
                if video_obj['status'] == "success":
                    # make API call to get video info
                    response = self.get_video_details(id=video_obj["video_id"])
                    # print extracted video infos
                    youtube_info_dict = self.get_video_infos(response)
                    if self.allow_comments == True and int(youtube_info_dict['Youtube_Number_Of_Comments']) > 0:
                        video_comments,comments_replies = self.scrap_comments_by_pages(params,
                                                                      youtube_info_dict['Youtube_Number_Of_Comments'])
                        youtube_info_dict['comments'] = video_comments
                        youtube_info_dict['comments_replies']=comments_replies

                    afsdf = 0
                    youtube_info_dict["Youtube_status"] = video_obj['status']
                    youtube_info_dict["Youtube_errorMessage"] = "none"
                elif video_obj['status'] == "failed":
                    youtube_info_dict['Youtube_Title'] = ' '
                    youtube_info_dict['Youtube_Description'] = ' '
                    youtube_info_dict['Youtube_Publish time'] = ' '
                    youtube_info_dict['Youtube_Duration'] = ' '
                    youtube_info_dict['Youtube_Number_Of_Comments'] = ' '
                    youtube_info_dict['Youtube_Number_Of_Likes'] = ' '
                    youtube_info_dict['Youtube_Number_Of_Views'] = ' '
                    youtube_info_dict["Youtube_status"] = video_obj['status']
                    youtube_info_dict["Youtube_errorMessage"] = video_obj['errorMessage']
            msg_status = "failed"
            if youtube_info_dict["Youtube_status"] == "success":
                msg_status = "success"
            return msg_status, youtube_info_dict
        except Exception as ex:
            logging.error("> get url dict error: " + str(ex))
            youtube_info_dict['Youtube_Title'] = ' '
            youtube_info_dict['Youtube_Description'] = ' '
            youtube_info_dict['Youtube_Publish time'] = ' '
            youtube_info_dict['Youtube_Duration'] = ' '
            youtube_info_dict['Youtube_Number_Of_Comments'] = ' '
            youtube_info_dict['Youtube_Number_Of_Likes'] = ' '
            youtube_info_dict['Youtube_Number_Of_Views'] = ' '
            youtube_info_dict["Youtube_status"] = "failed"
            youtube_info_dict["Youtube_errorMessage"] = str(ex)
            print(str(ex))
            return "failed", youtube_info_dict
            # pass
# try:
#     os.mkdir("youtube_extraction_per_excel")
# except:
#     pass
# all_youtube_info = [i for i in all_youtube_info if i]
# df=0
# try:
#     pd.DataFrame(all_youtube_info).to_excel('youtube_extraction_per_excel/youtube_info_'+file_name+'.xlsx', encoding='utf-8-sig', index=False)
# except Exception as ex:
#     pass
# daskdas=0
# def parse_channel_url(url):
#     """
#     This function takes channel `url` to check whether it includes a
#     channel ID, user ID or channel name
#     """
#     path = p.urlparse(url).path
#     id = path.split("/")[-1]
#     if "/c/" in path:
#         return "c", id
#     elif "/channel/" in path:
#         return "channel", id
#     elif "/user/" in path:
#         return "user", id
# def get_channel_details(youtube, **kwargs):
#     return youtube.channels().list(
#         part="statistics,snippet,contentDetails",
#         **kwargs
#     ).execute()
# def search(youtube, **kwargs):
#     return youtube.search().list(
#         part="snippet",
#         **kwargs
#     ).execute()
# def get_channel_id_by_url(youtube, url):
#     """
#     Returns channel ID of a given `id` and `method`
#     - `method` (str): can be 'c', 'channel', 'user'
#     - `id` (str): if method is 'c', then `id` is display name
#         if method is 'channel', then it's channel id
#         if method is 'user', then it's username
#     """
#     # parse the channel URL
#     method, id = parse_channel_url(url)
#     if method == "channel":
#         # if it's a channel ID, then just return it
#         return id
#     elif method == "user":
#         # if it's a user ID, make a request to get the channel ID
#         response = get_channel_details(youtube, forUsername=id)
#         items = response.get("items")
#         if items:
#             channel_id = items[0].get("id")
#             return channel_id
#     elif method == "c":
#         # if it's a channel name, search for the channel using the name
#         # may be inaccurate
#         response = search(youtube, q=id, maxResults=1)
#         items = response.get("items")
#         if items:
#             channel_id = items[0]["snippet"]["channelId"]
#             return channel_id
#     raise Exception(f"Cannot find ID:{id} with {method} method")
# def get_comments(youtube, **kwargs):
#     return youtube.commentThreads().list(
#         part="snippet",
#         **kwargs
#     ).execute()
# # URL can be a channel or a video, to extract comments
# url = "https://www.youtube.com/watch?v=jNQXAC9IVRw&ab_channel=jawed"
# if "watch" in url:
#     # that's a video
#     video_id = get_video_id_by_url(url)
#     params = {
#         'videoId': video_id,
#         'maxResults': 2,
#         'order': 'relevance', # default is 'time' (newest)
#     }
# else:
#     # should be a channel
#     channel_id = get_channel_id_by_url(url)
#     params = {
#         'allThreadsRelatedToChannelId': channel_id,
#         'maxResults': 2,
#         'order': 'relevance', # default is 'time' (newest)
#     }
# # get the first 2 pages (2 API requests)
# n_pages = 2
# for i in range(n_pages):
#     # make API call to get all comments from the channel (including posts & videos)
#     response = get_comments(youtube, **params)
#     items = response.get("items")
#     # if items is empty, breakout of the loop
#     if not items:
#         break
#     for item in items:
#         comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
#         updated_at = item["snippet"]["topLevelComment"]["snippet"]["updatedAt"]
#         like_count = item["snippet"]["topLevelComment"]["snippet"]["likeCount"]
#         comment_id = item["snippet"]["topLevelComment"]["id"]
#         print(f"""\
#         Comment: {comment}
#         Likes: {like_count}
#         Updated At: {updated_at}
#         ==================================\
#         """)
#     if "nextPageToken" in response:
#         # if there is a next page
#         # add next page token to the params we pass to the function
#         params["pageToken"] =  response["nextPageToken"]
#     else:
#         # must be end of comments!!!!
#         break
#     print("*"*70)
#
