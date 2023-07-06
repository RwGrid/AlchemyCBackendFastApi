import json
import logging
import traceback
import math
import ujson
from datetime import date, timedelta
import multiline
import pandas as pd
from dateutil.parser import parse
from datetime import datetime as dtm
from app.elastic_deps.elastic_session import ELASTIC_CONFIG, ElasticSearchSingelton
from starlette.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi import Depends
from fastapi import Request, APIRouter
from sqlalchemy.orm import Session  # type: ignore
# from ..dependencies import verify_cookie
from app.dependencies import verify_cookie

from app.utility_functions import return_date, process_date
from app.SessionFactory import get_db
from app.connection_to_postgre import crud

# the 'tags' in the router are important for-> These "tags" are especially useful for the automatic interactive
# documentation systems
tasks_router = APIRouter(
    tags=["tasks_pages"],
    dependencies=[Depends(verify_cookie)],
    responses={404: {"description": "Not found"}},
)
es = ElasticSearchSingelton().es_client

default_from_date: str = (
        date.today() - timedelta(days=int(ELASTIC_CONFIG["default_days_preview_episodes"]))
).isoformat()
default_to_date_now: str = (date.today() + timedelta(days=1)).isoformat()


def convert_to_string(data):
    if isinstance(data, float):
        return str(data)
    elif isinstance(data, dict):
        return {key: convert_to_string(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_to_string(item) for item in data]
    else:
        return data


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


@tasks_router.get("/GetTasksEpisodesDataP/")
async def get_episodes_elastic(db: Session = Depends(get_db), access_token: dict = Depends(verify_cookie)
                               ):
    token: dict = json.loads(access_token.body)
    current_user = crud.get_user_by_username(db=db, user_name=token["user"])
    sent_actions_to_current_user = crud.get_send_actions_pending(db, current_user)
    sent_actions_to_current_user_hash = [action.action_body['hash'] for action in sent_actions_to_current_user]
    # Define the search query
    search_query = {
        "query": {
            "bool": {
                "must": [
                    {
                        "terms": {
                            "episode_id": sent_actions_to_current_user_hash
                        }
                    }
                ]
            }
        }
    }

    response = await  es.search(index=ELASTIC_CONFIG["index_dump_data_into"], body=search_query, size=9999)
    result: list = response.body["hits"]["hits"]
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
        if 'ملاحظة'  in epi:
            distinct_episode["note"] = epi["ملاحظة"]

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
            action_copy = (action.__dict__)
            action_copy['episode_id'] = action_copy['action_body']['hash']
            action_copy['sender_name'] = action.sender.user_display_name
            action_copy['receiver_name'] = action.receiver.user_display_name

            actions_list.append(action_copy)
        tasks = pd.DataFrame(actions_list
                             )

        if len(tasks) > 0 and len(final_list) > 0:
            final_list = final_list.merge(tasks, on='episode_id', how='outer').to_dict(orient='records')
        elif len(final_list) > 0 and len(tasks) == 0:
            final_list = final_list.to_dict(orient='records')
    final_list = convert_to_string(final_list)
    return final_list


@tasks_router.get("/GetTasksEpisodesDataC/")
async def get_episodes_elastic(db: Session = Depends(get_db), access_token: dict = Depends(verify_cookie)
                               ):
    token: dict = json.loads(access_token.body)
    current_user = crud.get_user_by_username(db=db, user_name=token["user"])
    sent_actions_to_current_user = crud.get_send_actions_received(db, current_user)
    actions_required_from_user = crud.get_send_actions_pending_sender(db, current_user)
    sent_actions_to_current_user = sent_actions_to_current_user + actions_required_from_user
    usrs_with_admin_previlige_ids = [usr.id for usr in crud.get_users_by_role(db=db, role_name='roleXF')]
    sent_actions_to_current_user = [send_action for send_action in sent_actions_to_current_user if
                                    send_action.receiver_id not in usrs_with_admin_previlige_ids]
    sent_actions_to_current_user_hash = [action.action_body['hash'] for action in sent_actions_to_current_user]
    # Define the search query
    search_query = {
        "query": {
            "bool": {
                "must": [
                    {
                        "terms": {
                            "episode_id": sent_actions_to_current_user_hash
                        }
                    }
                ]
            }
        }
    }

    response = await  es.search(index=ELASTIC_CONFIG["index_dump_data_into"], body=search_query, size=9999)
    result: list = response.body["hits"]["hits"]
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
        if 'ملاحظة'  in epi:
            distinct_episode["note"] = epi["ملاحظة"]
        else:
            distinct_episode["note"] = ""
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

    # sort_by_date=parse(distinct_episode['insertion_date'], fuzzy=True)
    final_list.sort(
        key=lambda x: dtm.strptime(str(x["insertion_date"]), "%Y-%m-%d %H:%M:%S"),
        reverse=True,
    )

    # to get date time format:https://jeffkayser.com/projects/date-format-string-composer/index.html
    # need to change sort by to 'insertion_date'
    for i, item in enumerate(final_list):
        item.update({"e_id": i})
    actions_list = []
    for action in sent_actions_to_current_user:
        action_copy = (action.__dict__)
        action_copy['episode_id'] = action_copy['action_body']['hash']
        action_copy['sender_name'] = action.sender.user_display_name
        action_copy['receiver_name'] = action.receiver.user_display_name
        updater_user = action.get_updater(db=db)
        if updater_user:
            action_copy['updated_by'] = updater_user.user_display_name
        action_copy['sender_username'] = action.sender.user_name
        action_copy['sender_display_name'] = action.sender.user_display_name
        action_copy['receiver_username'] = action.receiver.user_name
        actions_list.append(action_copy)
    actions_list = jsonable_encoder(actions_list)

    tasks = pd.DataFrame(actions_list
                         )
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
        epi_final['db_program_name'] = program_name['program_name']
        epi_final['episode_type'] = episode_type['episode_type']
    if len(final_list) > 0:
        final_list = pd.DataFrame(final_list)
        if len(tasks) > 0 and len(final_list) > 0:
            final_list = final_list.merge(tasks, on='episode_id', how='outer').to_dict(orient='records')
        elif len(final_list) > 0 and len(tasks) == 0:
            final_list = final_list.to_dict(orient='records')
        final_list = convert_to_string(final_list)

        json_compatible_item_data = jsonable_encoder(final_list)
        json_compatible_item_data = [{k: v for k, v in d.items()} for d in json_compatible_item_data]
        return JSONResponse(content=json_compatible_item_data)

    return final_list
