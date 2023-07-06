import hashlib
import json
import logging
import traceback
from datetime import date, timedelta
import multiline
from dateutil.parser import parse
import pandas as pd
from datetime import datetime as dtm
from app.elastic_session import ELASTIC_CONFIG, ElasticSearchSingelton
from fastapi import Depends
from fastapi import Request, APIRouter
from sqlalchemy.orm import Session  # type: ignore
# from ..dependencies import verify_cookie
from app.dependencies import verify_cookie

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
def fetch_from_db_by_ids(db: Session, guest_list_postgres, editors_list_postgres, graphic_list_from_postgres,
                         hosts_list_from_postgres, program_name_postgres, episode_type_postgres):
    guest_list = []
    editor_list = []
    graphic_list = []
    hosts_list = []
    program_name={}
    episode_type={}
    for gst in guest_list_postgres:
        try:
            guest_list.append(crud.get_guest_info_by_id(db, gst['id']))
        except Exception as ex:
            print("the guest is probably deleted")
    for edtr in editors_list_postgres:
        try:
            editor_list.append(crud.get_editor_by_id(db, edtr['id']))
        except Exception as ex:
            print("the editor is probably deleted")
    for grphic in graphic_list_from_postgres:
        try:
            graphic_list.append(crud.get_graphic_by_id(db, grphic['id']))
        except Exception as ex:
            print("the graphic person is probably deleted")
    for gst in hosts_list_from_postgres:
        try:
            hosts_list.append(crud.get_host_by_id(db, gst['id']))
        except Exception as ex:
            print("the host person is probably deleted")
    try:
        program_name = crud.get_program_by_id(db, program_name_postgres['id'])
    except Exception as ex:
        print("the program name is probably deleted")
    try:
        episode_type = crud.get_episode_type_by_id(db, episode_type_postgres['id'])

    except Exception as ex:
        print("the episode type  is probably deleted")

    return guest_list, editor_list, graphic_list, hosts_list, program_name, episode_type



def convert_to_string(data):
    if isinstance(data, float):
        return str(data)
    elif isinstance(data, dict):
        return {key: convert_to_string(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_to_string(item) for item in data]
    else:
        return data


@manage_episodes_router.get("/GetEpisodesData/")
async def get_episodes_elastic(
        from_date: str ='',
        to_date: str ='',db: Session = Depends(get_db),access_token: dict = Depends(verify_cookie)
):
    token: dict = json.loads(access_token.body)
    current_user = crud.get_user_by_username(db=db, user_name=token["user"])
    sent_actions_to_current_user = crud.get_send_actions_received(db, current_user)
    sent_actions_to_current_user_hash = [action.action_body['hash'] for action in sent_actions_to_current_user]

    # now = dtm.today().isoformat()
    # week_ago = (dtm.today() - timedelta(days=365)).isoformat()
    # need to use a code different from fuzzy true , because its slow if it is a defined format
    if from_date=='' and to_date=='':
        default_from_date: str = (
                date.today() - timedelta(days=30)
        ).isoformat()
        from_date= default_from_date
        to_date: str = (date.today() + timedelta(days=1)).isoformat()

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
    try:
        resp = await es.search(
            index=ELASTIC_CONFIG["index_dump_data_into"],
            body={"query": json_dict},
            size=9999,
        )
    except Exception as elastic_exc:
        asdf = 0
    result: list = resp.body["hits"]["hits"]
    result_sources: list = [res["_source"] for res in result]
    distinct_episodes = []

    for i, epi in enumerate(result_sources):
        distinct_episode = dict()
        distinct_episode['guest_list_postgres'] = epi['guest_list_postgres']
        distinct_episode['editors_list_postgres'] = epi['editors_list_postgres']
        distinct_episode['graphic_list_from_postgres'] = epi['graphic_list_from_postgres']
        distinct_episode['hosts_list_from_postgres'] = epi['hosts_list_from_postgres']
        distinct_episode['program_name_postgres'] = epi['program_name_postgres']
        distinct_episode['episode_type_postgres'] = epi['episode_type_postgres']
        distinct_episode['episode_sections'] = epi['مقاطع الحلقة']
        distinct_episode['episode_duration'] = epi['مدة الحلقة']
        duration_hour, duration_minutes = epi['مدة الحلقة'].split(':')
        distinct_episode['episode_duration_view'] = duration_hour + ' h ' + duration_minutes + ' m '

        distinct_episode['tags'] = epi['tags']
        distinct_episode["summary"] = epi["الملخص"]
        distinct_episode["episode_release_date"] = epi["الزمان"]
        distinct_episode["episode_release_date_for_view"] = epi["الزمان"].replace(
            "T", " "
        )
        distinct_episode["_id"] = result[i]["_id"]
        if "رايط المقطع" in epi:
            distinct_episode["youtube_url"] = epi["رايط المقطع"]
        else:
            distinct_episode["youtube_url"] = ""
        distinct_episode["episode_id"] = epi["episode_id"]
        distinct_episode["day"] = epi["اليوم"]
        distinct_episode["date"] = epi["تاريخ"]
        if "ملاحظة" in epi:
            distinct_episode["note"]=epi["ملاحظة"]
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
    for epi_final in final_list:
        guest_list, editors_list, graphic_list, host_list, program_name, episode_type = fetch_from_db_by_ids(db,
                                                                                                             epi_final[
                                                                                                                 'guest_list_postgres'],
                                                                                                             epi_final[
                                                                                                                 'editors_list_postgres'],
                                                                                                             epi_final[
                                                                                                                 'graphic_list_from_postgres'],
                                                                                                             epi_final[
                                                                                                                 'hosts_list_from_postgres'],
                                                                                                             epi_final[
                                                                                                                 'program_name_postgres'],
                                                                                                             epi_final[
                                                                                                                 'episode_type_postgres'])
        epi_final['guest_list'] = guest_list
        epi_final['editors_list'] = [edtr['name'] for edtr in editors_list]
        epi_final['graphic_list'] = [ghic['name'] for ghic in graphic_list]
        epi_final['guest_names_list'] = [gst['name'] for gst in guest_list]

        epi_final['host_list'] = [hst['host_name'] for hst in host_list]
        if 'program_name' in program_name:
            epi_final['db_program_name'] = program_name['program_name']
        if 'episode_type' in episode_type:
            epi_final['episode_type'] = episode_type['episode_type']
    if len(final_list) > 0:
        # sort_by_date=parse(distinct_episode['insertion_date'], fuzzy=True)
        final_list.sort(
            key=lambda x: dtm.strptime(str(x["insertion_date"]), "%Y-%m-%d %H:%M:%S"),
            reverse=True,
        )

        # to get date time format:https://jeffkayser.com/projects/date-format-string-composer/index.html
        # need to change sort by to 'insertion_date'
        for i, item in enumerate(final_list):
            item.update({"e_id": i})
        final_list = pd.DataFrame(final_list)
        actions_list = []
        for action in sent_actions_to_current_user:
            action_copy = dict(action.__dict__)
            if 'updated_at' in action_copy:
                action_copy["update_date"] = str(action_copy["updated_at"]).split('.')[0]
            action_copy['episode_id'] = action_copy['action_body']['hash']
            action_copy['sender_name'] = action.sender.user_display_name
            action_copy['receiver_name'] = action.receiver.user_display_name
            updater_user = action.get_updater(db=db)
            if updater_user:
                action_copy['updated_by'] = updater_user.user_display_name
            action_copy['sender_username'] = action.sender.user_name
            action_copy['sender_display_name'] = action.sender.user_display_name
            action_copy['receiver_username'] = action.receiver.user_name
            action_copy.pop('_sa_instance_state', None)

            actions_list.append(action_copy)
        tasks = pd.DataFrame(actions_list
                             )
        if len(tasks)>0 and len(final_list)>0:
            final_list = final_list.merge(tasks, on='episode_id', how='outer').to_dict(orient='records')
        elif  len(final_list)>0 and len(tasks)==0:
            final_list = final_list.to_dict(orient='records')
    for i, item in enumerate(final_list):
        item.update({"id": i})
    final_list = convert_to_string(final_list)
    return final_list


@manage_episodes_router.post("/UpdateEpisode")
async def read_item(request: Request, db: Session = Depends(get_db), access_token: dict = Depends(verify_cookie)):
    try:
        # https://www.youtube.com/watch?v=UqjMKAkWqKY
        episode_json: dict = await request.json()
        if 'new_youtube_url' in episode_json:
            if episode_json['new_youtube_url']!='':
                youtube_data, fetch_status = process_youtube_episode(comments_allowed=False,
                                                                     url=episode_json['new_youtube_url'])
                if fetch_status == "failed":
                    return {"status": "Warning", "message": "Youtube Link Not Valid, task not done"}
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


        for row in rows:
            row["_source"]["_id"] = row["_id"]
            d1 = dict(row["_source"])
            if 'new_youtube_url' in episode_json:
                d1.update(youtube_data)
            if 'new_note' in episode_json:
                if episode_json['new_note'] != '':
                    d1['ملاحظة'] = episode_json['new_note']
            updated_list.append(d1)

        for episode in updated_list:
            indexed_doc = dict(episode)
            del indexed_doc["_id"]
            await es.index(
                index=ELASTIC_CONFIG["index_dump_data_into"],
                document=indexed_doc,
                id=episode["_id"],
            )
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
        return {
            "status": "SUCCESS",
            "message": "successfully finished task"
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
