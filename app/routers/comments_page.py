import json
import re
from collections import defaultdict
import datetime
import time
import emoji
import nltk
import math

import pytz
from fastapi.encoders import jsonable_encoder
from nltk import bigrams, word_tokenize
from nltk import FreqDist
import pandas as pd
import requests
from dotenv import dotenv_values
from fastapi import Depends, Query
from fastapi import Request, APIRouter,BackgroundTasks
from nltk.corpus import stopwords
from sqlalchemy.orm import Session  # type: ignore
from starlette.responses import JSONResponse
from tzlocal import get_localzone
from app.dependencies import verify_cookie
from app.send_data_to_elastic_utility import process_youtube_episode

nltk.download('stopwords')
nltk.download('punkt')
sentiment_service: dict = dotenv_values("./.env.sentiment")
comments_dashboard_router_experimenting = APIRouter(
    tags=["comments"],
    responses={404: {"description": "Not found"}},
)

comments_dashboard_router = APIRouter(
    tags=["comments"],
    dependencies=[Depends(verify_cookie)],
    responses={404: {"description": "Not found"}},
)
arabic_stop_words = []
with open('./arabic_stop_words.txt', 'r') as file:
    # Read the contents of the file into a single string
    file_contents = file.read()

    # Split the string into a list of strings, one for each line
    arabic_stop_words = file_contents.split('\n')

    # Remove any empty strings from the list
    arabic_stop_words = list(filter(None, arabic_stop_words))


def clean_text(sentences_list):
    cleaned_sentences = []
    for sentence in sentences_list:
        sentence_without_punctuation = re.sub(r'[^\w\s]', ' ', sentence.strip())
        stop_words_english = stopwords.words('english')
        sentence_cleaned_from_stop_words = []
        sentence_without_punctuation = sentence_without_punctuation.replace('<br>', '')
        sentence_without_punctuation = sentence_without_punctuation.replace('</br>', '')
        sentence_without_punctuation = re.sub(r'\bbr\b', ' ', sentence_without_punctuation)
        sentence_without_punctuation_splitted = sentence_without_punctuation.split(' ')
        for word in sentence_without_punctuation_splitted:
            if word not in stop_words_english:
                if word not in arabic_stop_words:
                    sentence_cleaned_from_stop_words.append(word)

        sentence_cleaned_from_stop_words = [word for word in sentence_cleaned_from_stop_words if
                                            word != '']
        sentence_cleaned_from_stop_words = " ".join(sentence_cleaned_from_stop_words)
        cleaned_sentences.append(sentence_cleaned_from_stop_words)
    return cleaned_sentences


def get_unigrams(corpus, top_x: int):
    # Combine the strings into a single corpus
    # Tokenize the corpus into individual words
    tokens = word_tokenize(corpus)
    # Calculate frequency distribution of unigrams
    freq_dist = nltk.FreqDist(tokens)
    # Print the top 20 unigrams by frequency
    top_20_unigram = freq_dist.most_common(top_x)
    top_20_unigram_list = []
    # Iterate over the top 20 bigrams
    top_unigram_series = []
    top_unigram_tags = []
    for unigram, frequency in top_20_unigram:
        # Add the bigram and its frequency count to the dictionary
        bigram_obj = dict()
        bigram_obj['bigram_keyword'] = unigram
        bigram_obj['bigram_frequency'] = str(frequency)
        top_20_unigram_list.append(bigram_obj)
        top_unigram_series.append(frequency)
        top_unigram_tags.append(unigram)
        # top_20_bigrams_dict[bigram] = frequency

    return top_20_unigram_list, top_unigram_series, top_unigram_tags


def get_bigrams(corpus, top_x: int):
    # Tokenize the input string into individual words
    tokens = word_tokenize(corpus)

    # Create a list of bigrams from the tokens
    bigrams = list(nltk.bigrams(tokens))

    # Calculate frequency distribution of bigrams
    freq_dist = FreqDist(bigrams)

    # Get the top 20 bigrams by frequency
    top_20_bigrams = freq_dist.most_common(top_x)

    # Create a dictionary to hold the top 20 bigrams and their frequency counts
    top_20_bigrams_dict = {}
    top_20_bigrams_list = []
    top_bigram_series = []
    top_bigram_tags = []
    # Iterate over the top 20 bigrams
    for bigram, frequency in top_20_bigrams:
        # Add the bigram and its frequency count to the dictionary
        bigram_obj = dict()
        bigram_obj['bigram_keyword'] = bigram[0] + ' ' + bigram[1]
        bigram_obj['bigram_frequency'] = str(frequency)
        top_20_bigrams_list.append(bigram_obj)
        top_bigram_series.append(frequency)
        top_bigram_tags.append(bigram[0] + ' ' + bigram[1])
        # top_20_bigrams_dict[bigram] = frequency

    return top_20_bigrams_list, top_bigram_series, top_bigram_tags


def remove_br(sentence):
    sentence_without_punctuation = sentence.replace('<br>', '')
    sentence_without_punctuation = sentence_without_punctuation.replace('</br>', '')
    sentence_without_punctuation = re.sub(r'\bbr\b', ' ', sentence_without_punctuation)
    return sentence_without_punctuation


# @comments_dashboard_router.get("/GetYoutubeCommentsSingle/{url}")
# async def get_comments_analytics(url: str):
#     # just make it a post request and put the youtube in the body
#     url = ast.literal_eval(url)
#     decoded_url = decrypt(url, '01234567890123456789012345678901')
#     asdfsadf = 0
def process_youtube(comments_url):
    # response = requests.post(
    #     'http://' + sentiment_service['SENTIMENT_IP'] + ':' + sentiment_service['SENTIMENT_PORT'] + '/get_sentiment',
    #     json=comments_url)
    print("here processing youtube")
    response = requests.post(
        'http://0.0.0.0:4432'+'/get_sentiment',
        json=comments_url)
    return response
def notify_client(result):
    # notify the client that the task is complete
    print("Task completed with result:", result)

async def process_data(data):
    # perform some processing on the data
    result = data + " processed"
    print(result)


    with open("data.txt", "w") as f:
            f.write(result)

    return result
@comments_dashboard_router_experimenting.post("/GetYoutubeCommentsSingle")
async def get_comments_analytics(request: Request,background_tasks: BackgroundTasks):
    comments_url: dict = await request.json()
    taskd = background_tasks.add_task(process_data, "bobob_")
    task =background_tasks.add_task(process_youtube,comments_url=comments_url)
    # task_result = background_tasks.get_task_result(task)
    gsdfgsg=0
    # background_tasks.add_task(notify_client, result)
    iamhere=0
    # sentiment_result = json.loads(response.text)

# @comments_dashboard_router_experimenting.post("/GetYoutubeCommentsSingle")
# async def get_comments_analytics(request: Request,background_tasks: BackgroundTasks):
#     comments_url: dict = await request.json()
#     # assgf = {'youtube_url': 'https://www.youtube.com/watch?v=3NnU0eY_Bbs'}
#     url = comments_url['youtube_url']
#     youtube_data = process_youtube_episode(comments_allowed=True, url=url)
#     comments = youtube_data['comments']
#     comments_lst = [cmnt['sentence'] for cmnt in comments]
#     cmnt_obj = {'sentences': comments_lst}
#     response = requests.post(
#         'http://' + sentiment_service['SENTIMENT_IP'] + ':' + sentiment_service['SENTIMENT_PORT'] + '/get_sentiment',
#         json=cmnt_obj)
#     sentiment_result = json.loads(response.text)
#     sentiment_stat = dict()
#     sentiment_stat['negative_comments'] = len([sent for sent in sentiment_result if sent['sentiment'] == 'negative'])
#     sentiment_stat['positive_comments'] = len([sent for sent in sentiment_result if sent['sentiment'] == 'positive'])
#     sentiment_stat['neutral_comments'] = len([sent for sent in sentiment_result if sent['sentiment'] == 'neutral'])
#
#     sentiment_sentences = pd.DataFrame(sentiment_result)
#     comments_df = pd.DataFrame(comments)
#     comments_with_sentiment = pd.merge(sentiment_sentences, comments_df, on='sentence', how='inner').astype(
#         str)
#     comments_with_sentiment['sentence'] = comments_with_sentiment['sentence'].apply(lambda x: remove_br(x))
#     comments_with_sentiment = comments_with_sentiment.to_dict(
#         orient='records')
#     date_counts = defaultdict(int)
#
#     for d in comments_with_sentiment:
#         # convert ISO formatted date string to a datetime object
#         date = datetime.datetime.fromisoformat(d['updated_at'].replace('Z', '+00:00')).date()
#         timestamp = int(time.mktime(date.timetuple())) * 1000
#         d['timestamp']=timestamp
#         date_counts[timestamp] += 1
#     # convert dictionary to a list of tuples
#     date_counts_list = [[(date), count] for date, count in date_counts.items()]
#     # sort list by date
#     date_counts_list.sort()
#
#     clean_comments = clean_text(comments_lst)
#     bigrams, top_bigram_series, top_bigram_tags = get_bigrams(corpus=" ".join(clean_comments), top_x=10)
#     unigrams, top_unigram_series, top_unigram_tags = get_unigrams(corpus=" ".join(clean_comments), top_x=10)
#     stats = dict()
#     stats['عدد التعليقات'] = str(youtube_data['عدد التعليقات'])
#     stats['عدد الإعجابات'] = str(youtube_data['عدد الإعجابات'])
#     stats['عدد المشاهدات'] = str(youtube_data['عدد المشاهدات'])
#     comments_info = dict()
#     comments_info['unigram'] = unigrams
#     comments_info['bigram'] = bigrams
#     comments_info['top_unigram_series'] = top_unigram_series
#     comments_info['top_unigram_tags'] = top_unigram_tags
#     comments_info['top_bigram_series'] = top_bigram_series
#     comments_info['top_bigram_tags'] = top_bigram_tags
#     comments_info['stats'] = stats
#     comments_info['comments_data'] = comments_with_sentiment
#     comments_info['message'] = "successfully analyzed comments"
#     comments_info['status'] = "success"
#     comments_info['sentiment_stat'] = sentiment_stat
#     comments_info = jsonable_encoder(comments_info)
#     comments_info['engagement_metric'] = math.ceil(
#         int(youtube_data['عدد المشاهدات']) / youtube_data['عدد المشتركين بالقناة'] * 100)
#
#     comments_info['date_count_list'] = date_counts_list
#
#     first_comment_timestamp=date_counts_list[0][0]/1000 # dividing by 1000 is critical
#
#     dt_object = datetime.datetime.fromtimestamp(first_comment_timestamp)
#
#     # Subtract one day
#     one_day = datetime.timedelta(days=1)
#     new_dt_object = dt_object - one_day
#
#     # Convert the datetime object back to a timestamp
#     comments_info['date_count_first_date'] = int(new_dt_object.timestamp())*1000
#     return JSONResponse(content=comments_info)
