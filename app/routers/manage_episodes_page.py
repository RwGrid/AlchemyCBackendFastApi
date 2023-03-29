import hashlib
import json
import logging
import traceback
from datetime import date, timedelta
import multiline
from dateutil.parser import parse
from datetime import datetime as dtm
from app.elastic_session import ELASTIC_CONFIG, ElasticSearchSingelton
from fastapi import Depends
from fastapi import Request, APIRouter
from sqlalchemy.orm import Session  # type: ignore
from ..dependencies import verify_cookie
from app.utility_functions import return_date, process_date
from app.send_data_to_elastic_utility import process_youtube_episode
from app.SessionFactory import get_db
from app.connection_to_postgre import crud

# the 'tags' in the router are important for-> These "tags" are especially useful for the automatic interactive
# documentation systems
manage_episodes_router = APIRouter(
    tags=["manage_episodes"],
    dependencies=[Depends(verify_cookie)],
    responses={404: {"description": "Not found"}},
)
es = ElasticSearchSingelton().es_client

default_from_date: str = (
        date.today() - timedelta(days=int(ELASTIC_CONFIG["default_days_preview_episodes"]))
).isoformat()
default_to_date_now: str = (date.today() + timedelta(days=1)).isoformat()


@manage_episodes_router.get("/GetEpisodesData/")
async def get_episodes_elastic(
        from_date: str = '"' + default_from_date + '"',
        to_date: str = '"' + default_to_date_now + '"',
):
    # now = dtm.today().isoformat()
    # week_ago = (dtm.today() - timedelta(days=365)).isoformat()
    # need to use a code different from fuzzy true , because its slow if it is a defined format
    if from_date != default_from_date:
        from_date = parse(from_date.strip(), fuzzy=True)
        from_date = '"' + process_date(from_date) + '"'
        to_date = parse(to_date.strip(), fuzzy=True)
        to_date = '"' + process_date(to_date) + '"'

        # IN CASE OF TESTING USE THE ONE BELOW
        # to_date = '"' + default_to_date_now + '"'
    # end_time = parse(to_date.strip(), fuzzy=True)
    range_query_body = (
            """{
    "range": {
             "تاريخ إدخال الداتا": {
                 "gte": """
            + from_date
            + """,
                 "lte": """
            + to_date
            + """
             }
         }}
     """
    )

    json_dict: dict = multiline.loads(range_query_body, multiline=True)
    resp = await es.search(
        index=ELASTIC_CONFIG["index_dump_data_into"],
        body={"query": json_dict},
        size=9999,
    )
    result: list = resp.body["hits"]["hits"]
    result_sources: list = [res["_source"] for res in result]
    distinct_episodes = []

    for i, epi in enumerate(result_sources):
        distinct_episode = dict()
        distinct_episode["_id"] = result[i]["_id"]
        if "رايط المقطع" in epi:
            distinct_episode["youtube_url"] = epi["رايط المقطع"]
        else:
            distinct_episode["youtube_url"] = ""
        distinct_episode["episode_id"] = epi["episode_id"]
        distinct_episode["day"] = epi["اليوم"]
        distinct_episode["date"] = epi["تاريخ"]
        try:
            date_time_obj = str(return_date(parse(epi["تاريخ"], fuzzy=True)))
        except:
            date_time_obj = str(epi["تاريخ"])
        distinct_episode["date"] = date_time_obj
        distinct_episode["time"] = epi["التوقيت اليومي"]
        if "تاريخ إدخال الداتا":
            distinct_episode["insertion_date"] = epi["تاريخ إدخال الداتا"].replace(
                "T", " "
            )
            # distinct_episode['insertion_date'] =str(parse(epi['تاريخ إدخال الداتا'], fuzzy=True))
        else:
            distinct_episode["insertion_date"] = epi["تاريخ"]
        if "البرنامج" in epi:
            distinct_episode["program"] = epi["البرنامج"]
        else:
            distinct_episode["program"] = ""
        if "الموضوع الرئيسي" in epi:
            distinct_episode["subject"] = epi["الموضوع الرئيسي"]
        else:
            distinct_episode["subject"] = ""
        distinct_episodes.append(distinct_episode)
    episode_ids = set([ep["episode_id"] for ep in distinct_episodes])

    final_list = []
    for episode_id in episode_ids:
        for de in distinct_episodes:
            if episode_id == de["episode_id"]:
                final_list.append(de)
                break
    set_of_jsons = {json.dumps(d, sort_keys=True) for d in final_list}
    final_list = [json.loads(t) for t in set_of_jsons]
    # sort_by_date=parse(distinct_episode['insertion_date'], fuzzy=True)
    final_list.sort(
        key=lambda x: dtm.strptime(str(x["insertion_date"]), "%Y-%m-%d %H:%M:%S"),
        reverse=True,
    )
    # to get date time format:https://jeffkayser.com/projects/date-format-string-composer/index.html
    # need to change sort by to 'insertion_date'
    for i, item in enumerate(final_list):
        item.update({"id": i})
    return final_list


@manage_episodes_router.post("/UpdateEpisode")
async def read_item(request: Request, db: Session = Depends(get_db), access_token: dict = Depends(verify_cookie)):
    try:
        # https://www.youtube.com/watch?v=UqjMKAkWqKY
        episode_json: dict = await request.json()
        if 'is_task' in episode_json:
            if episode_json['completion_status'] == 'pending':
                token: dict = json.loads(access_token.body)
                current_user = crud.get_user_by_username(db=db, user_name=token["user"])
                if 'task_hash' in episode_json:
                    crud.update_send_actions(db, episode_json['task_hash'], current_user)
                else:
                    episode_body = {}
                    episode_body['hash'] = episode_json['episode_id']
                    episode_body['subject'] = episode_json['subject']
                    episode_body['program_name'] = episode_json['program']
                    hash_checksum = hashlib.md5(
                        json.dumps(episode_body, sort_keys=True, ensure_ascii=True).encode('utf-8')).hexdigest()
                    crud.update_send_actions(db, hash_checksum, current_user)

        search_param = {
            "query": {"match": {"episode_id.keyword": episode_json["episode_id"]}}
        }
        resp = await es.search(
            index=ELASTIC_CONFIG["index_dump_data_into"],
            body=search_param,
            size=9999,
        )
        rows: list = resp.raw["hits"]["hits"]
        updated_list: list = []
        youtube_data = process_youtube_episode(comments_allowed=False, url=episode_json['new_youtube_url'])
        for row in rows:
            row["_source"]["_id"] = row["_id"]
            d1 = dict(row["_source"])
            d1.update(youtube_data)
            updated_list.append(d1)

        for episode in updated_list:
            indexed_doc = dict(episode)
            del indexed_doc["_id"]
            await es.index(
                index=ELASTIC_CONFIG["index_dump_data_into"],
                document=indexed_doc,
                id=episode["_id"],
            )
        return {
            "status": "SUCCESS",
            "message": "updated episode Successfully",
            "youtube_url": youtube_data["رايط المقطع"],
        }
    except Exception as err:
        print(traceback.format_exc())
        logging.error(f"could not perform REQUEST: {err}")
        return {"status": "ERR"}


@manage_episodes_router.delete("/DeleteEpisode/{episode_id}")
async def delete_program(episode_id: str, db: Session = Depends(get_db)):
    episode_id_to_delete = '"' + episode_id + '"'
    crud.delete_send_actions(db, episode_id)

    query = (
            """{
        "match": {
          "episode_id": """
            + episode_id_to_delete
            + """
        }
      }"""
    )
    query_dict = multiline.loads(query, multiline=True)
    # error_Trace = await es.ping(error_trace=True)
    resp = await es.delete_by_query(
        index=ELASTIC_CONFIG["index_dump_data_into"],
        body={"query": query_dict},
    )
    if resp.meta.status == 200:
        return {"status": "SUCCESS", "message": "Deleted  Episode Successfully"}
    else:
        return {"status": "FAILED", "message": "Failed To Delete Episode"}
