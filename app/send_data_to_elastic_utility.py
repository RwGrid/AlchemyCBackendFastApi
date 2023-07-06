import logging
import os
import re
import traceback
from datetime import datetime
from sqlalchemy.util import reduce
import datetime as dt_lib
from math import isnan
from time import sleep
from dateutil.parser import parse
from elasticsearch import AsyncElasticsearch
import hashlib, json
import pandas as pd
from os import path
from datetime import datetime as dtm
import get_channel_info_youtubeapi_single_url
from app.connection_to_postgre import models
from app.connection_to_postgre.crud import get_guest_info_to_modify, get_guest_info_by_name, get_editor_by_name, \
    get_program_by_name, get_episode_type_by_name, get_graphic_by_name, get_host_by_name
from app.connection_to_postgre.database import AlchemySession


def aggregate_similar_cols(column_keyword, data_cols):
    similar_cols: list = [col for col in data_cols if column_keyword in col]
    return similar_cols


def process_youtube_episode(comments_allowed, url):
    youtube_status, youtube_crawl_obj = get_channel_info_youtubeapi_single_url.YoutubeWrapper(
        allow_comments=comments_allowed).get_youtube_info(
        url)

    youtube_crawl_obj['Youtube_Link'] = url
    dict2 = {}
    if 'comments' in youtube_crawl_obj:
        dict2['comments'] = youtube_crawl_obj['comments']
    if 'comments_replies' in youtube_crawl_obj:
        dict2['comments_replies'] = youtube_crawl_obj['comments_replies']
    if 'Youtube_Link' in youtube_crawl_obj:
        if youtube_crawl_obj['Youtube_Link'] != ' ' and youtube_crawl_obj['Youtube_Link'] != '':
            dict2["رايط المقطع"] = youtube_crawl_obj['Youtube_Link']
    if 'Youtube_Title' in youtube_crawl_obj:
        if youtube_crawl_obj['Youtube_Title'] != ' ' and youtube_crawl_obj['Youtube_Title'] != '':
            dict2["عنوان المقطع"] = youtube_crawl_obj['Youtube_Title']
    if 'Youtube_Publish time' in youtube_crawl_obj:
        if youtube_crawl_obj['Youtube_Publish time'] != ' ' and youtube_crawl_obj[
            'Youtube_Publish time'] != '':
            Youtube_Publish = parse(str(youtube_crawl_obj['Youtube_Publish time']), fuzzy=True)
            dict2["تاريخ تحميل المقطع"] = str(Youtube_Publish.isoformat())
    if 'Youtube_Duration' in youtube_crawl_obj:
        if youtube_crawl_obj['Youtube_Duration'] != ' ' and youtube_crawl_obj['Youtube_Duration'] != '':
            dict2["مدة المقطع"] = int(youtube_crawl_obj['Youtube_Duration'].split(':')[0])
    if 'Youtube_Number_Of_Comments' in youtube_crawl_obj:
        if youtube_crawl_obj['Youtube_Number_Of_Comments'] != ' ' and youtube_crawl_obj[
            'Youtube_Number_Of_Comments'] != '':
            dict2["عدد التعليقات"] = int(youtube_crawl_obj['Youtube_Number_Of_Comments'])
    if "Youtube_Number_Of_Likes" in youtube_crawl_obj:
        if youtube_crawl_obj['Youtube_Number_Of_Likes'] != ' ' and youtube_crawl_obj[
            'Youtube_Number_Of_Likes'] != '':
            dict2["عدد الإعجابات"] = int(youtube_crawl_obj['Youtube_Number_Of_Likes'])
    if "Youtube_Number_Of_Views" in youtube_crawl_obj:
        if youtube_crawl_obj['Youtube_Number_Of_Views'] != ' ' and youtube_crawl_obj[
            'Youtube_Number_Of_Views'] != '':
            # total_count_views += int(record['Youtube_Number_Of_Views'])
            dict2["عدد المشاهدات"] = int(youtube_crawl_obj['Youtube_Number_Of_Views'])
    if "Youtube_Channel_subscriber_count" in youtube_crawl_obj:
        if youtube_crawl_obj['Youtube_Channel_subscriber_count'] != ' ' and youtube_crawl_obj[
            'Youtube_Channel_subscriber_count'] != '':
            dict2["عدد المشتركين بالقناة"] = int(youtube_crawl_obj['Youtube_Channel_subscriber_count'])

    return dict2, youtube_status


def convert_int_values_to_string(data):
    if isinstance(data, dict):
        new_dict = {}
        for key, value in data.items():
            new_dict[key] = convert_int_values_to_string(value)
        return new_dict
    elif isinstance(data, list):
        new_list = []
        for item in data:
            new_list.append(convert_int_values_to_string(item))
        return new_list
    elif isinstance(data, int):
        return str(data)
    else:
        return data


def process_episode(sent_json):
    try:
        # counter = 0
        # if path.exists('count.txt'):
        #     with open('count.txt', 'r') as f:
        #         counter = int(f.read())
        #         test = 0
        # else:
        #     with open('count.txt', 'w') as f:
        #         f.write('0')
        record = dict(sent_json)
        import datetime
        from dateutil.parser import parse
        current_date_time = datetime.datetime.now()
        year0 = current_date_time.year
        month0 = current_date_time.month
        day0 = current_date_time.day
        hour0 = current_date_time.hour
        minute0 = current_date_time.minute
        second0 = current_date_time.second

        dt0 = dt_lib.date((year0), (month0), (day0))
        tm0 = dt_lib.time(hour0, minute0, second0)
        combined0 = dtm.isoformat(dtm.combine(dt0, tm0))

        json_object = json.dumps(record, indent=4, ensure_ascii=False)
        try:
            os.mkdir('inserted_objects')
        except:
            pass
        try:
            os.mkdir('inserted_objects' + '/' + str(dt0))
        except:
            pass
        # Writing to sample.json
        with open('inserted_objects' + '/' + str(dt0) + '/' + str(tm0) + '.json', "w") as outfile:
            outfile.write(json_object)
        if 'formEditors' in record:
            if record.get('formEditors', None) is not None:

                if len(record['formEditors']) > 0:
                    record['formEditors'] = [rec['label'] for rec in record['formEditors']]
        if 'formHosts' in record:
            if record.get('formHosts', None) is not None:

                if len(record['formHosts']) > 0:
                    record['formHosts'] = [rec['label'] for rec in record['formHosts']]
        if 'formGraphic' in record:
            if record.get('formGraphic', None) is not None:

                if len(record['formGraphic']) > 0:
                    record['formGraphic'] = [rec['label'] for rec in record['formGraphic']]

        record = {k: v for k, v in record.items() if v != ''}
        columns = [col for col in list(record.keys())]
        hosts_cols = aggregate_similar_cols("formHosts", columns)
        sub_subject_cols = aggregate_similar_cols("formSubSubject", columns)
        guest_cols = aggregate_similar_cols('formGuests', columns)
        editor_cols = aggregate_similar_cols('formEditors', columns)
        graphic_cols = aggregate_similar_cols('formGraphic', columns)
        scene_cols = aggregate_similar_cols("formMashhad", columns)
        malafat_cols = aggregate_similar_cols("formSiyasiya", columns)

        dict2 = {}

        dict2["تاريخ إدخال الداتا"] = combined0
        dict2["اليوم"] = record['formDay'].strip()
        # dict2["تاريخ"] = str(record['formEpiDate']).strip()%m/%d/%Y,
        datee = parse(record['formEpiTime'].strip(), fuzzy=True).strftime("%Y-%m-%d")
        time = parse(record['formEpiTime'].strip(), fuzzy=True).strftime("%H:%M:%S")
        dict2["تاريخ"] = str(datee).strip()
        dict2["التوقيت اليومي"] = str(time).strip()
        if 'formEditors' in record:
            if record.get('formEditors', None) is not None:

                if len(record['formEditors']) > 0:
                    dict2['فريق الإعداد'] = '|'.join(record['formEditors'])
        if 'formGraphic' in record:
            if record.get('formGraphic', None) is not None:

                if len(record['formGraphic']) > 0:
                    dict2['فريق الغرافيك'] = '|'.join(record['formGraphic'])

        dict2["التصنيف"] = str(record['formEpisodeType']).strip()
        # dict2["التصنيف"]
        # dict2["طبيعة البث"] = record['formBroadcastType'].strip()
        # date = record['formEpiDate']
        if isinstance(datee, str):
            datee = datee.strip()

            datee = parse(datee, fuzzy=True)

        if isinstance(time, str):
            time = time.strip()

            dt = parse(time, fuzzy=True)
            exacttime = dt_lib.datetime.strptime(time, '%H:%M:%S')

        # dt = parse(record['Date'], fuzzy=True)
        year = datee.year
        month = datee.month
        day = datee.day
        hour = exacttime.hour
        minute = exacttime.minute

        dt = dt_lib.date((year), (month), (day))
        tm = dt_lib.time(hour, minute)
        combined = dtm.isoformat(dtm.combine(dt, tm))

        dict2["الزمان"] = combined
        dict2["البرنامج"] = record['formProgramName']
        dict2["رايط المقطع"] = ''
        dict2["عنوان المقطع"] = ''
        dict2["تاريخ تحميل المقطع"] = ' '
        dict2["مدة المقطع"] = ''
        dict2["عدد التعليقات"] = ''
        dict2["عدد الإعجابات"] = ''
        dict2["عدد المشاهدات"] = ''
        youtube_status = "None"
        if 'formYoutubeLink' in record:
            youtube_status, youtube_crawl_obj = get_channel_info_youtubeapi_single_url.YoutubeWrapper(
                allow_comments=False).get_youtube_info(
                record['formYoutubeLink'])
            youtube_crawl_obj['Youtube_Link'] = record['formYoutubeLink']
            if 'Youtube_Link' in youtube_crawl_obj:
                if youtube_crawl_obj['Youtube_Link'] != ' ' and youtube_crawl_obj['Youtube_Link'] != '':
                    dict2["رايط المقطع"] = youtube_crawl_obj['Youtube_Link']
            if 'Youtube_Title' in youtube_crawl_obj:
                if youtube_crawl_obj['Youtube_Title'] != ' ' and youtube_crawl_obj['Youtube_Title'] != '':
                    dict2["عنوان المقطع"] = youtube_crawl_obj['Youtube_Title']
            if 'Youtube_Publish time' in youtube_crawl_obj:
                if youtube_crawl_obj['Youtube_Publish time'] != ' ' and youtube_crawl_obj[
                    'Youtube_Publish time'] != '':
                    Youtube_Publish = parse(str(youtube_crawl_obj['Youtube_Publish time']), fuzzy=True)
                    dict2["تاريخ تحميل المقطع"] = str(Youtube_Publish.isoformat())
            if 'Youtube_Duration' in youtube_crawl_obj:
                if youtube_crawl_obj['Youtube_Duration'] != ' ' and youtube_crawl_obj['Youtube_Duration'] != '':
                    dict2["مدة المقطع"] = int(youtube_crawl_obj['Youtube_Duration'].split(':')[0])
            if 'Youtube_Number_Of_Comments' in youtube_crawl_obj:
                if youtube_crawl_obj['Youtube_Number_Of_Comments'] != ' ' and youtube_crawl_obj[
                    'Youtube_Number_Of_Comments'] != '':
                    dict2["عدد التعليقات"] = int(youtube_crawl_obj['Youtube_Number_Of_Comments'])
            if "Youtube_Number_Of_Likes" in youtube_crawl_obj:
                if youtube_crawl_obj['Youtube_Number_Of_Likes'] != ' ' and youtube_crawl_obj[
                    'Youtube_Number_Of_Likes'] != '':
                    dict2["عدد الإعجابات"] = int(youtube_crawl_obj['Youtube_Number_Of_Likes'])
            if "Youtube_Number_Of_Views" in youtube_crawl_obj:
                if youtube_crawl_obj['Youtube_Number_Of_Views'] != ' ' and youtube_crawl_obj[
                    'Youtube_Number_Of_Views'] != '':
                    # total_count_views += int(record['Youtube_Number_Of_Views'])
                    dict2["عدد المشاهدات"] = int(youtube_crawl_obj['Youtube_Number_Of_Views'])
        hosts = []
        # for host_col in hosts_cols:
        #     if record[host_col] != '' and record[host_col] != ' ':
        #         hosts.append(record[host_col])

        if 'formHosts' in record:
            if record.get('formHosts', None) is not None:
                if len(record['formHosts']) > 0:
                    hosts = list(record['formHosts'])
                    hosts = [{"المقدم": hst.strip()} for hst in hosts]
        dict2 = {key: value for (key, value) in dict2.items() if (value != ' ' or value == '')}
        if 'formMainSubject' in record:
            dict2["الموضوع الرئيسي"] = record['formMainSubject']
            subjects = [record['formMainSubject']]
        # guests 1st field
        guestslist = []
        db_init = AlchemySession().get_session_only()
        db_init = db_init()
        # i did this in order to fetch the expertise of each guest
        guests_list_from_postgres = []
        for guest in record['formGuests']:
            if guest['GuestName'] != '':
                db_guest_info = get_guest_info_by_name(db_init, guest['GuestName'])
                guest_obj = dict()
                guest_obj_postgre = dict()
                guests_list_from_postgres.append(dict(db_guest_info))
                guest_obj["اسم الضيف"] = db_guest_info['name'].strip()
                guest_obj_postgre['guest_name'] = db_guest_info['name'].strip()
                if 'expertise' in db_guest_info:
                    if db_guest_info.get('expertise', None) is not None:
                        guest_obj["مهنة الضيف"] = db_guest_info['expertise'].strip()
                        guest_obj_postgre['guest_expertise'] = db_guest_info['expertise'].strip()
                else:
                    guest_obj["مهنة الضيف"] = "لا يوجد حاليا"
                    guest_obj_postgre['guest_expertise'] = "لا يوجد حاليا"
                if 'GuestDesc' in guest:
                    if db_guest_info.get('GuestDesc', None) is not None:
                        guest_obj["صفة الضيف"] = list(guest['GuestDesc'])
                        guest_obj_postgre['guest_descs'] = db_guest_info['descriptions']
                if 'id' in db_guest_info:
                    guest_obj_postgre['guest_id'] = db_guest_info['id']

                # if db_guest_info.__dict__.get('country', None) is not None:
                if 'country' in db_guest_info:
                    if db_guest_info.get('country', None) is not None:
                        guest_obj['بلد الضيف'] = db_guest_info['country']
                guestslist.append(guest_obj)
                # guests_list_from_postgres.append(guest_obj_postgre)
        editor_list_from_postgres = []
        if 'formEditors'in record:
            if record.get('formEditors', None) is not None:
                for editor in record['formEditors']:
                    editor_list_from_postgres.append(get_editor_by_name(db_init, editor))
        graphic_list_from_postgres = []
        if 'formGraphic'in record:
            if record.get('formGraphic', None) is not None:
                for graphic in record['formGraphic']:
                    graphic_list_from_postgres.append(get_graphic_by_name(db_init, graphic))
        if 'formProgramName'in record:
            if record.get('formProgramName', None) is not None:
                program_name_postgres = get_program_by_name(db_init, record['formProgramName'])
        if 'formEpisodeType'in record:
            if record.get('formEpisodeType', None) is not None:
                    episode_type_postgres = get_episode_type_by_name(db_init, record['formEpisodeType'])
        hosts_list_from_postgres=[]
        if 'formHosts' in record:
            if record.get('formHosts', None) is not None:
                if len(record['formHosts']) > 0:
                    for hst in record['formHosts']:
                        hosts_list_from_postgres.append(get_host_by_name(db_init, hst))

        dfgsdfg=0
        """        
        guestslist = []
        db_init = AlchemySession().get_session_only()
        db_init = db_init()
        for guest in record['formGuests']:
            if guest['GuestId'] != '':
                db_guest_info: models.guests_info = get_guest_info_to_modify(db_init, guest['GuestId'])
                guest_obj = dict()
                guest_obj["اسم الضيف"] = db_guest_info.name.strip()
                guest_obj["مهنة الضيف"] = db_guest_info.expertise.expertise.strip()
                guest_obj["صفة الضيف"] = list(guest['GuestDesc'])
                if db_guest_info.__dict__.get('country', None) is not None:
                    guest_obj['بلد الضيف'] = db_guest_info.country
                guestslist.append(guest_obj)"""
        # for k in range(6):
        #     cols = [cl for cl in guest_cols if str(k + 1) in cl]
        #     guest_obj = {}
        #     for guest_col in cols:
        #         if record[guest_col] != '' and record[guest_col] != ' ':
        #
        #             if 'Name' in guest_col:
        #                 guest_obj["اسم الضيف"] = record[guest_col].strip()
        #
        #             elif 'Expertise' in guest_col:
        #                 guest_obj["مهنة الضيف"] = record[guest_col].strip()
        #
        #             elif 'Desc' in guest_col:
        #                 guest_obj["صفة الضيف"] = record[guest_col].strip()
        #     if bool(guest_obj) != False:
        #         guestslist.append(guest_obj)
        sub_subjectlist = []
        # for sub_subject in sub_subject_cols:
        #     if record[sub_subject] != '' and record[sub_subject] != ' ':
        #         sub_subjectlist.append({"الموضوع الثانوي": record[sub_subject]})
        if 'formSections' in record:
            if len(record['formSections']) > 0:
                for sub_subject in record['formSections']:
                    sub_subjectlist.append({"الموضوع الثانوي": sub_subject['SectionTitle']})

        if dict2["البرنامج"] == "التحليلية":
            lol = 0
        scenes_lst = []
        for scene in scene_cols:
            if record[scene] != '' and record[scene] != ' ':
                scn = {}
                scn["الموضوع الثانوي"] = record[scene]
                if scene == "formMashhadOnline":
                    scene_desc = "المشهد اونلاين"
                elif scene == "formMashhadSaqafi":
                    scene_desc = "المشهد الثقافي"
                elif scene == "formMashhadSeyasi":
                    scene_desc = "المشهد السياسي"
                elif scene == "formMashhadSa5en":
                    scene_desc = "المشهد الساخن"
                scn["طبيعة المقطع"] = scene_desc
                scenes_lst.append(scn)
                sub_subjectlist.append({"الموضوع الثانوي": record[scene]})
        malafat_lst = []
        for malaf in malafat_cols:
            if record[malaf] != '' and record[malaf] != ' ':
                mlf = {}
                mlf["الموضوع الثانوي"] = record[malaf]
                malaf_desc = ""
                if malaf == "formSiyasiyaMalaf1":
                    malaf_desc = "الملف الأوّل"
                elif malaf == "formSiyasiyaMalaf2":
                    malaf_desc = "الملف الثاني"
                elif malaf == "formSiyasiyaMalaf3":
                    malaf_desc = "الملف الثالث"
                elif malaf == "formSiyasiyaMalaf4":
                    malaf_desc = "قضية اليوم"
                mlf["طبيعة المقطع"] = malaf_desc
                malafat_lst.append(mlf)
                sub_subjectlist.append({"الموضوع الثانوي": record[malaf]})
        if dict2["البرنامج"] == "التحليلية":
            if len(guestslist) > 4:
                t7lilya_extra_guests = []

                for i in range(4, 6):
                    if i > 0 and i < len(guestslist):
                        current_extra_guest = guestslist[i]
                        # t7lilya_extra_guests.append(current_extra_guest['اسم الضيف'])
                        dict2["ضيف التحليلية" + "_" + str(i + 1)] = current_extra_guest['اسم الضيف']
        dict2['guest_list'] = guestslist
        dict2['الضيوف'] = guestslist
        dict2 = {key: value for (key, value) in dict2.items() if value != ' ' and value != ''}
        dict2 = dict((k, v) for k, v in dict2.items() if v)
        hash_checksum = hashlib.md5(json.dumps(dict2, sort_keys=True, ensure_ascii=True).encode('utf-8')).hexdigest()
        dict2['episode_id'] = hash_checksum
        dict2['guest_list_postgres']=guests_list_from_postgres
        dict2['editors_list_postgres']=editor_list_from_postgres
        dict2['graphic_list_from_postgres'] = graphic_list_from_postgres
        dict2['program_name_postgres']=program_name_postgres
        dict2['episode_type_postgres']=episode_type_postgres
        dict2['hosts_list_from_postgres']=hosts_list_from_postgres
        if 'formTags' in record:
            tags = [tg['label'] for tg in record['formTags']]
            dict2['tags'] = tags
        if 'formSummary' in record:
            dict2['الملخص'] = record['formSummary']
        if 'formEditors' in record:
            dict2['الفريق المنتج'] = record['formEditors']
        if 'formGraphic' in record:
            dict2['الفريق الفني'] = record['formGraphic']
        if 'formSections' in record:
            if len(record['formSections']) > 0:
                dict2['مقاطع الحلقة'] = record['formSections']
            else:
                dict2['مقاطع الحلقة'] = [
                    {'SectionStart': '00:00:00', 'SectionEnd': record['formSectionDuration'] + ':00',
                     'SectionTitle': record['formMainSubject']}]
        if 'formSectionDuration' in record:
            dict2['مدة الحلقة'] = record['formSectionDuration']

        dict2['original_obj'] = record.copy()
        dict2['original_obj'] = convert_int_values_to_string(dict2['original_obj'])
        original_row = pd.DataFrame([dict2])
        dict2["طبيعة المقطع"] = ""
        ReadyToInsertRows = []
        if dict2["البرنامج"] != "التحليلية" and dict2["البرنامج"] != "المشهدية":
            dict2["طبيعة المقطع"] = "عادي"
            guestslist_checksumed = checksum_data_return_df(data=guestslist, checksum=hash_checksum)
            subjectslist_checksumed = checksum_data_return_df(data=sub_subjectlist, checksum=hash_checksum)
            hostslist_checksumed = checksum_data_return_df(data=hosts, checksum=hash_checksum)
            dfs = [guestslist_checksumed, subjectslist_checksumed, hostslist_checksumed]
            non_empty_dfs = [df for df in dfs if not df.empty]
            if len(non_empty_dfs) > 0:
                join_all_dataframes = reduce(lambda left, right: pd.merge(left, right, on='episode_id', how='inner'),
                                             non_empty_dfs)
                join_all_dataframes = pd.merge(left=original_row, right=join_all_dataframes, how='inner',
                                               on='episode_id')
            else:
                join_all_dataframes = original_row
        elif dict2["البرنامج"] == "المشهدية":
            mshadiye_episodes_list = []
            for i in range(4):
                mshadiye_episode = {}
                if len(guestslist) >= 0 and i < len(guestslist):
                    current_guest = guestslist[i]
                    if "اسم الضيف" in current_guest:
                        mshadiye_episode["اسم الضيف"] = current_guest["اسم الضيف"]
                    if "مهنة الضيف" in current_guest:
                        mshadiye_episode["مهنة الضيف"] = current_guest["مهنة الضيف"]
                    if "صفة الضيف" in current_guest:
                        mshadiye_episode["صفة الضيف"] = current_guest["صفة الضيف"]
                if len(scenes_lst) > 0 and i < len(scenes_lst):
                    current_scene = scenes_lst[i]
                    if "الموضوع الثانوي" in current_scene:
                        mshadiye_episode["الموضوع الثانوي"] = current_scene["الموضوع الثانوي"]
                    if "طبيعة المقطع" in current_scene:
                        mshadiye_episode["طبيعة المقطع"] = current_scene["طبيعة المقطع"]
                if bool(mshadiye_episode) != False:
                    mshadiye_episodes_list.append(mshadiye_episode)
            # if len(guestslist)>4:
            #     mshadiye_extra_guests=[]
            #     for i in range(4,6):
            #         current_extra_guest = guestslist[i]
            #         #t7lilya_extra_guests.append(current_extra_guest['اسم الضيف'])
            #         dict2["ضيوف المشهدية"+"_"+str(i+1)]=current_extra_guest['اسم الضيف']
            guestslist_checksumed = checksum_data_return_df(data=guestslist.copy(), checksum=hash_checksum)
            subjectslist_checksumed = checksum_data_return_df(data=sub_subjectlist.copy(), checksum=hash_checksum)
            mshadiye_episodes_list_checksumed = checksum_data_return_df(data=mshadiye_episodes_list,
                                                                        checksum=hash_checksum)
            hostslist_checksumed = checksum_data_return_df(data=hosts, checksum=hash_checksum)
            dfs = [mshadiye_episodes_list_checksumed, hostslist_checksumed]
            non_empty_dfs = [df for df in dfs if not df.empty]
            if len(non_empty_dfs) > 0:
                join_all_dataframes = reduce(lambda left, right: pd.merge(left, right, on='episode_id', how='inner'),
                                             non_empty_dfs)
                join_all_dataframes = pd.merge(left=original_row, right=join_all_dataframes, how='inner',
                                               on='episode_id')
            else:
                join_all_dataframes = original_row
        elif dict2["البرنامج"] == "التحليلية":
            t7lilya_episodes_list = []
            for i in range(4):
                t7lilya_episode = {}
                if len(guestslist) > 0 and i < len(guestslist):
                    current_guest = guestslist[i]
                    if "اسم الضيف" in current_guest:
                        t7lilya_episode["اسم الضيف"] = current_guest["اسم الضيف"]
                    if "مهنة الضيف" in current_guest:
                        t7lilya_episode["مهنة الضيف"] = current_guest["مهنة الضيف"]
                    if "صفة الضيف" in current_guest:
                        t7lilya_episode["صفة الضيف"] = current_guest["صفة الضيف"]
                if len(malafat_lst) > 0 and i < len(malafat_lst):
                    current_scene = malafat_lst[i]
                    if "الموضوع الثانوي" in current_scene:
                        t7lilya_episode["الموضوع الثانوي"] = current_scene["الموضوع الثانوي"]
                    if "طبيعة المقطع" in current_scene:
                        t7lilya_episode["طبيعة المقطع"] = current_scene["طبيعة المقطع"]
                if bool(t7lilya_episode) != False:
                    t7lilya_episodes_list.append(t7lilya_episode)

            guestslist_checksumed = checksum_data_return_df(data=guestslist.copy(), checksum=hash_checksum)
            subjectslist_checksumed = checksum_data_return_df(data=sub_subjectlist.copy(), checksum=hash_checksum)
            t7lilya_episodes_list_checksumed = checksum_data_return_df(data=t7lilya_episodes_list,
                                                                       checksum=hash_checksum)
            hostslist_checksumed = checksum_data_return_df(data=hosts, checksum=hash_checksum)
            dfs = [t7lilya_episodes_list_checksumed, hostslist_checksumed]
            non_empty_dfs = [df for df in dfs if not df.empty]
            if len(non_empty_dfs) > 0:
                join_all_dataframes = reduce(lambda left, right: pd.merge(left, right, on='episode_id', how='inner'),
                                             non_empty_dfs)
                join_all_dataframes = pd.merge(left=original_row, right=join_all_dataframes, how='inner',
                                               on='episode_id')
            else:
                join_all_dataframes = original_row
        for rec in (join_all_dataframes.to_dict(orient='records')):
            rec['الكلمات المفتاحية'] = ''
            host_names = []
            sub_subject_name = []
            guest_names = []
            guest_expertise_lst = []
            guest_desc_lst = []
            if guestslist_checksumed.empty == False:
                episode_guests = {}
                episode_guests['episode_guest_list'] = guestslist_checksumed.to_dict(orient='records')
                episode_guests['episode_guest_list'] = [
                    {k: v for k, v in item.items() if not (isinstance(v, float) and isnan(v) == True)} for item in
                    episode_guests['episode_guest_list']]

                for itm in episode_guests['episode_guest_list']:
                    if 'اسم الضيف' in itm:
                        guest_names.append(itm['اسم الضيف'])
                    if 'مهنة الضيف' in itm:
                        guest_expertise_lst.append(itm['مهنة الضيف'])
                    if 'صفة الضيف' in itm:
                        guest_desc_lst.extend(itm['صفة الضيف'])
                if len(guest_names) > 0:
                    rec['Guests_Name_List'] = '|'.join(guest_names)
                    rec['Guests_Name_List'] = rec['episode_id'] + '_' + rec['Guests_Name_List']
                if len(guest_expertise_lst) > 0:
                    rec['Guests_Expertise_List'] = '|'.join(guest_expertise_lst)
                    rec['Guests_Expertise_List'] = rec['episode_id'] + '_' + rec['Guests_Expertise_List']
                if len(guest_desc_lst) > 0:
                    rec['Guests_Desc_List'] = '|'.join(guest_desc_lst)
                    rec['Guests_Desc_List'] = rec['episode_id'] + '_' + rec['Guests_Desc_List']
            if subjectslist_checksumed.empty == False:
                episode_subjects = {}
                episode_subjects['episode_sub_subjects_list'] = subjectslist_checksumed.to_dict(orient='records')
                episode_subjects['episode_sub_subjects_list'] = [
                    {k: v for k, v in item.items() if not (isinstance(v, float) and isnan(v) == True)} for item in
                    episode_subjects['episode_sub_subjects_list']]

                for ele in episode_subjects['episode_sub_subjects_list']:
                    if 'الموضوع الثانوي' in ele:
                        sub_subject_name.append(ele['الموضوع الثانوي'])
                if len(sub_subject_name) > 0:
                    rec['sub_subjects_list'] = '|'.join(sub_subject_name)
                    rec['sub_subjects_list'] = rec['episode_id'] + '_' + rec['sub_subjects_list']
            if hostslist_checksumed.empty == False:
                episode_hosts = {}

                episode_hosts['episode_hosts_list'] = hostslist_checksumed.to_dict(orient='records')
                episode_hosts['episode_hosts_list'] = [
                    {k: v for k, v in item.items() if not (isinstance(v, float) and isnan(v) == True)} for item in
                    episode_hosts['episode_hosts_list']]
                for mele in episode_hosts['episode_hosts_list']:
                    if 'المقدم' in mele:
                        host_names.append(mele['المقدم'])
                if len(host_names) > 0:
                    rec['hosts_list'] = ','.join(host_names)
                    rec['hosts_list'] = rec['episode_id'] + '_' + rec['hosts_list']
            rec = {k: v for k, v in rec.items() if not (isinstance(v, float) and isnan(v) == True)}
            keywords_of_subjects = []
            try:
                keywords_of_subjects.extend(subjects)
            except:
                pass
            try:
                keywords_of_subjects.extend(sub_subject_name)
            except:
                pass
            if len(keywords_of_subjects) > 0:
                key_words_comma_seperated = ','.join(keywords_of_subjects)
                key_words_comma_seperated_cleaned = key_words_comma_seperated.replace(',', ' ').split()
                key_words_comma_seperated_cleaned2 = []
                key_words_comma_seperated_cleaned3 = []
                # removing punctuation
                key_words_comma_seperated_cleaned = [re.sub(r'[^\w\s]', '', word) for word in
                                                     key_words_comma_seperated_cleaned]
                for word in key_words_comma_seperated_cleaned:
                    if 'وال' in word:
                        word = word.replace('وال', 'ال')
                    key_words_comma_seperated_cleaned2.append(word)
                stop_list_datafframe = pd.read_csv('stop_list.txt')
                # Assuming there's a columns with the headers 'name', 'height', 'weight'
                stop_list = list(stop_list_datafframe['stop_words'])
                words = [word for word in key_words_comma_seperated_cleaned2 if word.lower() not in stop_list]
                tags_concatenated = " ".join(tags)
                rec['الكلمات المفتاحية'] = " ".join(words) + " " + tags_concatenated

            ReadyToInsertRows.append(rec)
        # with open('count.txt', 'w') as f:
        #     f.write(str(counter + 1))
        return youtube_status, ReadyToInsertRows, hash_checksum
    except Exception as ex:
        print(traceback.format_exc())
        logging.error("> The error is in processing the data: " + str(ex))


def checksum_data_return_df(data, checksum):
    checksumed_list = []
    for dt_dict in (data):

        try:
            xx = dict(dt_dict)
            xx['episode_id'] = checksum

            checksumed_list.append(xx)
        except Exception as exx:
            print(str(exx))
    return pd.DataFrame(checksumed_list)


def send_data_to_elastic_utility(es_connection: AsyncElasticsearch, data, index_name, checksum):
    for dt_dict in data:

        try:
            xx = dict(dt_dict)
            xx['episode_id'] = checksum

            res = es_connection.index(index=index_name, document=xx)
        except Exception as exx:
            print(str(exx))
