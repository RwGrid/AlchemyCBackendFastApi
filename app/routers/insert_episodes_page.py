import json
import logging
import traceback
from typing import List

from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from app.connection_to_postgre import crud, schemas_sql_alchemy

from app.connection_to_postgre.models import users
from fastapi import APIRouter, Depends, HTTPException
from fastapi import Request, Cookie, APIRouter
from sqlalchemy.orm import Session  # type: ignore
from app.connection_to_postgre.schemas_sql_alchemy import Users, TagsOptions
# from ..CustomClasses.typeHintMsh import SqlOpMsg
# from ..connection_to_postgre import crud
# from ..dependencies import verify_cookie
from app.CustomClasses.typeHintMsh import SqlOpMsg
from app.connection_to_postgre import crud
from app.dependencies import verify_cookie
from app.SessionFactory import get_db
# from ..elastic_session import ElasticSearchSingelton
# from ..send_data_to_elastic_utility import process_episode
from app.elastic_session import ElasticSearchSingelton
from app.send_data_to_elastic_utility import process_episode

# the 'tags' in the router are important for-> These "tags" are especially useful for the automatic interactive
# documentation systems
insert_episodes_router = APIRouter(
    tags=["insert_episode"],
    dependencies=[Depends(verify_cookie)],
    responses={404: {"description": "Not found"}},
)
from app.elastic_session import ELASTIC_CONFIG

es = ElasticSearchSingelton().es_client
@insert_episodes_router.post("/CreateGuestInfoDynamically")
async def read_item(
        guest_info: schemas_sql_alchemy.GuestsInfoC, db: Session = Depends(get_db)
) -> SqlOpMsg:
    sdfasdf=0

    return crud.create_guest_info_dynamically(db=db, guest_info_pydantic=guest_info)

@insert_episodes_router.post("/CreateEpisode")
async def read_item(
        request: Request, access_token: dict = Depends(verify_cookie), db: Session = Depends(get_db)
) -> SqlOpMsg:
    """

    :param request:{'formFake': '', 'formDay': 'الخميس', 'topics': '', 'formEpiTime': '2022-12-02T01:11',
    'formProgramName': 'اجراس المشرق', 'formHosts1': 'زينب الصفار', 'formHosts2': 'محمد زيني', 'formBroadcastType':
    'جديد', 'formEpisodeType': 'ثقافي', 'formMainSubject': 'wer', 'formSubSubject1': 'asdf', 'formSubSubject2': '',
    'formSubSubject3': '', 'formSubSubject4': '', 'formSubSubject5': '', 'formGuestName1': 'كاتا ريا',
    'formGuestExpertise1': 'فنان', 'formGuestDesc1': 'عضو المكتب السياسي لحركة حماس', 'formGuestName2': '',
    'formGuestExpertise2': '', 'formGuestDesc2': '', 'formGuestName3': '', 'formGuestExpertise3': '',
    'formGuestDesc3': '', 'formGuestName4': '', 'formGuestExpertise4': '', 'formGuestDesc4': '', 'formGuestName5':
    '', 'formGuestExpertise5': '', 'formGuestDesc5': '', 'formGuestName6': '', 'formGuestExpertise6': '',
    'formGuestDesc6': '', 'formMashhadSa5en': '', 'formMashhadSeyasi': '', 'formMashhadSaqafi': '',
    'formMashhadOnline': '', 'formSiyasiyaMalaf1': '', 'formSiyasiyaMalaf2': '', 'formSiyasiyaMalaf3': '',
    'formSiyasiyaMalaf4': '', 'formYoutubeLink': 'https://www.youtube.com/watch?v=6DYEx8u9tFQ'}
    :param access_token: the jwt bearer token passed with axios with credentials
    :return:
    """
    try:
        episode_json = await request.json()
        # episode_json={'formFake': '', 'formDay': 'الاربعاء', 'formEpiTime': '2023-02-02T22:02', 'formProgramName': 'بيت القصيد', 'formEpisodeType': 'برنامج حواري', 'formMainSubject': 'ergdfgd', 'formSummary': 'dgfgdgdf', 'formMashhadSa5en': '', 'formMashhadSeyasi': '', 'formMashhadSaqafi': '', 'formMashhadOnline': '', 'formSiyasiyaMalaf1': '', 'formSiyasiyaMalaf2': '', 'formSiyasiyaMalaf3': '', 'formSiyasiyaMalaf4': '', 'formYoutubeLink': 'https://www.youtube.com/watch?v=AMNOwdnqhsM', 'formHosts': [{'value': 'مايك شلهوب', 'label': 'مايك شلهوب'}, {'value': 'أيهم بني المرجة', 'label': 'أيهم بني المرجة'}], 'formSubSubjects': ['dfgdfgfd', 'dfgdfg'], 'formEditors': [{'value': 'ali', 'label': 'ali'}], 'formGraphic': [{'value': 'ahmad', 'label': 'ahmad'}], 'formGuests': [{'GuestName': 'Rida Wazneh', 'GuestId': 37, 'GuestDesc': ['باحث في الشؤون السياسية والاستراتيجية']},{'GuestName': 'ali kheirdeen', 'GuestId': 36, 'GuestDesc': ['باحث في الشؤون السياسية والاستراتيجية']}]}
        # episode_json={'formFake': '', 'formDay': 'الخميس', 'formProgramName': 'بيت القصيد', 'formEpisodeType': 'ثقافي', 'formSummary': 'adsf asdf sadf asdf asdf asdf asd', 'formMashhadSa5en': '', 'formMashhadSeyasi': '', 'formMashhadSaqafi': '', 'formMashhadOnline': '', 'formSiyasiyaMalaf1': '', 'formSiyasiyaMalaf2': '', 'formSiyasiyaMalaf3': '', 'formSiyasiyaMalaf4': '', 'formYoutubeLink': '', 'formHosts': [{'value': 'مايك شلهوب', 'label': 'مايك شلهوب'}], 'formSubSubjects': [], 'formEditors': None, 'formGraphic': None, 'formGuests': [{'GuestName': 'toto', 'GuestId': 50, 'GuestDesc': ['toto'], 'GuestErrors': {'guestDescRequired': ''}}, {'GuestName': 'hamada', 'GuestId': '', 'GuestDesc': ['asdfasdf'], 'GuestErrors': {'guestDescRequired': ''}}], 'formMainSubject': 'adsf asd fasd fasdf ads', 'formEpiTime': '2023-06-22T09:57:06.903Z', 'formSectionDuration': '1:50', 'formSections': [{'SectionStart': '00:00:00', 'SectionEnd': '0:25:00', 'SectionTitle': 'makta31'}, {'SectionStart': '0:25:00', 'SectionEnd': '0:50:00', 'SectionTitle': 'makta32'}, {'SectionStart': '0:50:00', 'SectionEnd': '1:50:00', 'SectionTitle': 'makta33'}], 'formTags': [{'id': 1, 'label': 'sdafsdf', 'value': 'sdafsdf'}, {'value': 'testtag2', 'label': 'testtag2'}]}
        youtube_status, preprocess_and_format_episodes_list, hash_episode = process_episode(
            episode_json
        )
        for episode in preprocess_and_format_episodes_list:
            res = await es.index(
                index=ELASTIC_CONFIG["index_dump_data_into"], document=episode
            )
            if res.body["result"] != "created":
                logging.error("did not insert this record: " + str(res.body))
        logging.info("The Record has been successfully insert to elastic")
        if youtube_status != "success":
            token: dict = json.loads(access_token.body)
            usr = crud.get_user_by_username(db=db, user_name=token["user"])
            crud.create_send_actions(db=db, user=usr, episode_hash=hash_episode,
                                     subject=episode_json['formMainSubject'],
                                     program_name=episode_json['formProgramName'])
        if youtube_status == "success":
            return {
                "status": "Successfully Integrated The Episode",
                "youtube_status": "managed to get youtube video",
            }
        elif youtube_status == "None":

            return {
                "status": "Successfully Integrated The Episode",
                "youtube_status": "success",
            }
        elif youtube_status == "failed":
            return {
                "status": "Successfully Integrated The Episode",
                "youtube_status": "success",
            }

    except Exception as err:
        print(traceback.format_exc())
        logging.error(f"could not perform REQUEST: {err}")
        return {"status": "ERR"}
        # episode_input_hash = hashlib.md5(
        #     json.dumps(episode_json, sort_keys=True, ensure_ascii=True).encode('utf-8')).hexdigest()
        # try:
        #     os.mkdir('all_episodes_json')
        # except Exception as ex:
        #     pass
        # with open('all_episodes_json/' + episode_input_hash + '.json', 'w', encoding='utf8') as json_file:
        #     json.dump(episode_json, json_file, ensure_ascii=False)
        # #episode_processed = process_episode(episode_json)
        # await print_request(request)

    # json_compatible_item_data = jsonable_encoder({"item_id": episode_info})
    # return JSONResponse(content=json_compatible_item_data)


@insert_episodes_router.post("/InsertTags")
async def create_option(option: TagsOptions, db: Session = Depends(get_db)):
    res = crud.create_tag(db, tag=option)
    return res


@insert_episodes_router.get("/GetTags")
async def create_option(db: Session = Depends(get_db)):
    tags = crud.get_tags(db)
    return tags


@insert_episodes_router.post("/SendTask")
async def send_task(
        request: Request, access_token: dict = Depends(verify_cookie), db: Session = Depends(get_db), ):
    try:
        token: dict = json.loads(access_token.body)
        usr = db.get_user(db=db, user_name=token["user"])
        fasdf = 0
    except Exception as err:
        print(traceback.format_exc())
        logging.error(f"could not perform REQUEST: {err}")
        return {"status": "ERR"}
