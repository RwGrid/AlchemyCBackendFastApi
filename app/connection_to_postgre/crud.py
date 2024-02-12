from . import models, schemas_sql_alchemy
from .auth import AuthHandler
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.collections import InstrumentedList
from sqlalchemy.orm import lazyload
from sqlalchemy import func
from .models import (
    roles,
    visible_tabs,
    roles_visible_tabs,
    role_tabs_field_rules,
    users,
    guest_names_alchemy,
    program_name_alchemy,
    episode_type_alchemy,
    graphic_alchemy,
    guests_info,
    editor_alchemy,options_tag_model,supervises_users,supervises_roles
)
import ujson
import json
import traceback
import datetime
import hashlib, json
from fastapi import HTTPException
from  sqlalchemy import text
from sqlalchemy.orm import Session, joinedload
# from app.CustomClasses.typeHintMsh import SqlOpMsg
from CustomClasses.typeHintMsh import SqlOpMsg
from MyExceptions.RecordExistsException import RecordExistsException
from MyExceptions.RecordDoesNotExistException import RecordDoesNotExistException
from app.utilities.img_utility import base64_to_image
# https://stackoverflow.com/questions/5756559/how-to-build-many-to-many-relations-using-sqlalchemy-a-good-example
from .schemas_sql_alchemy import UsersSchema,GuestInfo,UsersSchemaRoles
# from marshmalow_sqlalchemy import ModelSerializer
MASTER_USERNAME = "12345"


def get_host_name_if_exists(db: Session, host_name: str) -> models.host_names_alchemy:
    return (
        db.query(models.host_names_alchemy)
        .filter(models.host_names_alchemy.host_name == host_name)
        .first()
    )
def get_host_by_name(db: Session, host_name):

        host_by_nam=db.query(models.host_names_alchemy).filter(models.host_names_alchemy.host_name == host_name).first()
        host=host_by_nam.__dict__
        host.pop('_sa_instance_state', None)
        return host

def get_host_by_id(db: Session, host_id):
    host_by_id = db.query(models.host_names_alchemy).filter(models.host_names_alchemy.id == host_id).first()
    host = host_by_id.__dict__
    host.pop('_sa_instance_state', None)
    return host


def get_hosts(db: Session) -> list[models.host_names_alchemy]:
    return (
        db.query(models.host_names_alchemy)
        .order_by(models.host_names_alchemy.id.desc())
        .all()
    )


def delete_host(db: Session, host_id: int) -> SqlOpMsg:
    try:
        host = db.query(models.host_names_alchemy).filter_by(id=host_id).first()
        if not host:
            raise RecordDoesNotExistException("Host not found")
        db.delete(host)
        db.commit()
        return {"status": "SUCCESS", "message": "Deleted Host Name Successfully"}
    except RecordDoesNotExistException:
        print(traceback.format_exc())
        return {"status": "FAILED", "message": "Deleting host Failed"}
    except Exception as ex:
        print(traceback.format_exc())
        print(str(ex))
        return {"status": "FAILED", "message": "Deleting host Failed"}


def create_host_names(
    db: Session, host_names_pydantic: schemas_sql_alchemy.HostsBaseC
) -> SqlOpMsg:
    db_host_name = models.host_names_alchemy(host_name=host_names_pydantic.host_name)
    db.add(db_host_name)
    db.commit()
    db.refresh(db_host_name)
    return {"status": "SUCCESS", "message": "Inserted Successfully"}


def get_guest_name_if_exists(
    db: Session, guest_name: str
) -> models.guest_names_alchemy:
    return (
        db.query(models.guest_names_alchemy)
        .filter(models.guest_names_alchemy.guest_name == guest_name)
        .first()
    )


def get_guests_info(db: Session) -> list[guests_info]:
    guests_info= db.query(models.guests_info).order_by(models.guests_info.id.desc()).all()
    guest_info_list=[]
    for guest in guests_info:
        guest_info_list.append(GuestInfo.from_orm_guest_info_full(guest).__dict__)
    return guest_info_list
def get_guest_info(db: Session,guest_info_id:int) -> guests_info:
    guests_info= db.query(models.guests_info).filter(models.guests_info.id == guest_info_id).first()
    guest_info_full=GuestInfo.from_orm_guest_info_full_with_base64(guests_info).__dict__
    return guest_info_full
def get_guest_info_by_id(db: Session,guest_info_id:int) -> guests_info:
    guests_info= db.query(models.guests_info).filter(models.guests_info.id == guest_info_id).first()
    guest_info_full=GuestInfo.from_orm_guest_info_full(guests_info).__dict__
    return guest_info_full


def delete_guest_info(db: Session, guest_info_id: int) -> dict:
    try:
        guest_info:guests_info = (
            db.query(models.guests_info).filter_by(id=guest_info_id).first()
        )
        if not guest_info:
            raise RecordDoesNotExistException("Guests Not not found")
            # raise HTTPException(status_code=404, detail="Guests Not not found")
        guest_info.descriptions.clear()
        db.commit()
        db.delete(guest_info)
        db.commit()
        return {"status": "SUCCESS", "message": "Deleted Guest Info Successfully"}
    except RecordDoesNotExistException as recNoExist:
        print(traceback.format_exc())
        return {"status": "FAILED", "message": "Deleting guest info Failed"}
    except Exception as ex:
        print(traceback.format_exc())
        print(str(ex))
        return {"status": "FAILED", "message": "Deleting guest info Failed"}


def get_guest_info_if_exists(db: Session, guest_name: str) -> models.guests_info:
    return (
        db.query(models.guests_info)
        .filter(models.guests_info.name == guest_name)
        .first()
    )
def get_tag_if_exists(db: Session, tag_name: str) ->options_tag_model:
    return (
        db.query(options_tag_model)
        .filter(options_tag_model.value == tag_name)
        .first()
    )

def create_tag(db:Session,tag:schemas_sql_alchemy.TagsOptions):
    if get_tag_if_exists(db=db,tag_name=tag.value):
        return {"status": "WARNING", "message": "Tag Exists"}

    db_tag = options_tag_model(label=tag.label, value=tag.value)
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    return {"status": "SUCCESS", "message": "New Tag Added"}
def get_tags(db:Session,):
    db_tags = db.query(options_tag_model).all()
    return db_tags

def create_guest_info_dynamically(
    db: Session, guest_info_pydantic: schemas_sql_alchemy.GuestsInfoC
) -> SqlOpMsg:
    db_guest_info_check: guest_info = get_guest_info_if_exists(
        db, guest_name=guest_info_pydantic.name
    )
    img="data:image/png;base64,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"
    image_hash = 'a53d1042509d41a22787b51ba800d4f2'
    if db_guest_info_check:
        descriptions=[item.guest_desc for item in db_guest_info_check.descriptions]
        descriptions_set_by_user=set(guest_info_pydantic.descriptions)
        desc_intersection = list(descriptions_set_by_user.intersection(descriptions))
        if len(desc_intersection)==len(descriptions_set_by_user):
            return {"status": "WARNING", "message": "Guest Name Already Exists"}
        else:
            remaining_new_descriptions=[item for item in descriptions_set_by_user if item not in desc_intersection]
            lst_of_descs=[]
            for rem_desc in remaining_new_descriptions:
                db_guest_desc = models.guests_desc(guest_desc=rem_desc)
                db.add(db_guest_desc)
                lst_of_descs.append(db_guest_desc)
            db_guest_info_check.descriptions.extend(lst_of_descs)
            db.commit()
    else:
        lst_of_descs=[]
        for rem_desc in guest_info_pydantic.descriptions:
            db_guest_desc = models.guests_desc(guest_desc=rem_desc)
            db.add(db_guest_desc)
            lst_of_descs.append(db_guest_desc)
        db.commit()

        db_guest_info = models.guests_info(
            name=guest_info_pydantic.name,image=img,image_hash=image_hash
        )
        db_guest_info.descriptions.extend(lst_of_descs)

        db.add(db_guest_info)
        db.commit()
        db.refresh(db_guest_info)
    # descriptions = (
    #     db.query(models.guests_desc)
    #     .filter(models.guests_desc.guest_desc.in_(guest_info_pydantic.descriptions))
    #     .all()
    # )


    return {"status": "SUCCESS", "message": "Inserted Guest Successfully"}
def create_guest_info(
    db: Session, guest_info_pydantic: schemas_sql_alchemy.GuestsInfoC,img_hash:str
) -> SqlOpMsg:
    db_guest_info_check: guest_info = get_guest_info_if_exists(
        db, guest_name=guest_info_pydantic.name
    )
    if db_guest_info_check:
        return {"status": "WARNING", "message": "Record Exists"}
    descriptions = (
        db.query(models.guests_desc)
        .filter(models.guests_desc.guest_desc.in_(guest_info_pydantic.descriptions))
        .all()
    )
    guest_expert=db.query(models.guest_expertise).filter(models.guest_expertise.expertise ==guest_info_pydantic.expertise).first()
    db_guest_info = models.guests_info(
        name=guest_info_pydantic.name,
        phone_number=guest_info_pydantic.phone_number,
        phone_extension=guest_info_pydantic.phone_extension,
        image=guest_info_pydantic.image,image_hash=img_hash,expertise=guest_expert,
        email=guest_info_pydantic.email,country=guest_info_pydantic.country,landline=guest_info_pydantic.landline
    )
    db_guest_info.descriptions.extend(descriptions)
    db.add(db_guest_info)
    db.commit()
    db.refresh(db_guest_info)
    return {"status": "SUCCESS", "message": "Inserted Guest Successfully"}
def get_guest_info_to_modify(db: Session, guest_id):
    db_guest = (
        db.query(models.guests_info)
        .options(joinedload(guests_info.descriptions))
        .filter(models.guests_info.id == guest_id)
        .first()
    )
    return db_guest
def get_guest_info_by_name(db: Session, guest_name: str) -> models.guests_info:
    guest=db.query(models.guests_info).options(joinedload(guests_info.descriptions)).filter(models.guests_info.name == guest_name).first()
    return GuestInfo.from_orm_guest_info_full(guest).__dict__
def update_guest_info(db: Session, guest_info_id: int, guest_object_update:schemas_sql_alchemy.GuestsInfoC,img_hash:str) -> SqlOpMsg:
    db_guest_info:models.guests_info = get_guest_info_to_modify(db, guest_info_id)
    db_guest_info.name=guest_object_update.name
    db_guest_info.image=guest_object_update.image
    db_guest_info.phone_number=guest_object_update.phone_number
    db_guest_info.country=guest_object_update.country
    db_guest_info.country=guest_object_update.country
    db_guest_info.email=guest_object_update.email
    db_guest_info.landline=guest_object_update.landline
    db_guest_info.image_hash=img_hash
    db_guest_info.phone_extension=guest_object_update.phone_extension
    db_guest_info.descriptions.clear()
    all_descs = []
    for gst_desc in guest_object_update.descriptions:
        description = (
            db.query(models.guests_desc)
            .filter(models.guests_desc.guest_desc == gst_desc)
            .first()
        )
        all_descs.append(description)
    db_guest_info.descriptions = all_descs
    guest_expert=db.query(models.guest_expertise).filter(models.guest_expertise.expertise ==guest_object_update.expertise).first()
    db_guest_info.expertise=guest_expert
    db.commit()
    return {"status": "SUCCESS", "message": "updated guest info Successfully"}
def create_guest_name(
    db: Session, guest_names_pydantic: schemas_sql_alchemy.GuestsNameC
) -> SqlOpMsg:
    db_guest_name: guest_names_alchemy = get_guest_name_if_exists(
        db, guest_name=guest_names_pydantic.guest_name
    )
    if db_guest_name:
        return {"status": "WARNING", "message": "Record Exists"}
    db_guest_name = models.guest_names_alchemy(
        guest_name=guest_names_pydantic.guest_name
    )
    db.add(db_guest_name)
    db.commit()
    db.refresh(db_guest_name)
    return {"status": "SUCCESS", "message": "Inserted Successfully"}


def get_guest_expertise_if_exists(db: Session, guest_expertise: str):
    return (
        db.query(models.guest_expertise)
        .filter(models.guest_expertise.expertise == guest_expertise)
        .first()
    )


def get_guest_expertises(db: Session):
    return (
        db.query(models.guest_expertise)
        .order_by(models.guest_expertise.id.desc())
        .all()
    )


def delete_guest_expertise(db: Session, id: int):
    try:
        guest_expertise = db.query(models.guest_expertise).filter_by(id=id).first()
        if not guest_expertise:
            raise RecordDoesNotExistException(" guest expertise does not exist")
        db.delete(guest_expertise)
        db.commit()
        return {"status": "SUCCESS", "message": "Deleted Guest Expertise Successfully"}
    except RecordDoesNotExistException:
        return {"status": "Failed", "message": "Deleting Guest Expertise Failed"}
    except Exception as ex:
        print(str(ex))
        print(traceback.format_exc())


def create_guest_expertise(
    db: Session, guest_expertise_pydantic: schemas_sql_alchemy.GuestsExpertiseC
):
    db_guest_expertise = models.guest_expertise(
        expertise=guest_expertise_pydantic.expertise
    )
    db.add(db_guest_expertise)
    db.commit()
    db.refresh(db_guest_expertise)
    return db_guest_expertise


def get_guest_desc_if_exists(db: Session, guest_desc: str):
    return (
        db.query(models.guests_desc)
        .filter(models.guests_desc.guest_desc == guest_desc)
        .first()
    )


def create_guest_desc(db: Session, guest_desc_pydantic: schemas_sql_alchemy.GuestsDesc):
    db_guest_desc = models.guests_desc(guest_desc=guest_desc_pydantic.guest_desc)
    db.add(db_guest_desc)
    db.commit()
    db.refresh(db_guest_desc)
    return db_guest_desc


def get_guest_desc(db: Session):
    return db.query(models.guests_desc).order_by(models.guests_desc.id.desc()).all()


def delete_guest_desc(db: Session, guest_desc_id: int):
    try:
        guest_desc = db.query(models.guests_desc).filter_by(id=guest_desc_id).first()
        if not guest_desc:
            raise RecordDoesNotExistException("guest desc not found")
        if len(guest_desc.guests) > 0:
                return {"status_title": "Failed",
                        "message": "Go Delete this Guest Description from All guests in Guests Page before u delete this","status":"Warning"}

        db.delete(guest_desc)
        db.commit()
        return {"status": "SUCCESS", "message": "Deleted Guest Desc Successfully"}
    except RecordDoesNotExistException:
        print(str(RecordDoesNotExistException))
        print(traceback.format_exc())
    except Exception as ex:
        print(str(ex))
        print(traceback.format_exc())


def get_program_name_if_exists(db: Session, program_name: str):
    return (
        db.query(models.program_name_alchemy)
        .filter(models.program_name_alchemy.program_name == program_name)
        .first()
    )
def get_program_by_name(db: Session, program_name: str):
    program=  db.query(models.program_name_alchemy).filter(models.program_name_alchemy.program_name == program_name).first()
    prgrm=program.__dict__.copy()
    prgrm.pop('_sa_instance_state', None)
    return prgrm
def get_program_by_id(db: Session, program_id):
    program=  db.query(models.program_name_alchemy).filter(models.program_name_alchemy.id == program_id).first()
    prgrm=program.__dict__.copy()
    prgrm.pop('_sa_instance_state', None)
    return prgrm


def get_all_roles(
    db: Session,
):
    db_roles = db.query(roles).all()
    return db_roles


def get_user_to_modify(db: Session, user_id):
    db_user = (
        db.query(models.users)
        .options(joinedload(users.roles))
        .options(joinedload(users.actions))
        .filter(models.users.id == user_id)
        .first()
    )
    return db_user

def get_user_by_username(db: Session, user_name):
    # db_user = (
    #     db.query(models.users)
    #     .options(joinedload(users.roles))
    #     .options(joinedload(users.actions))
    #     .options(joinedload(users.supervisors))
    #     .filter(models.users.user_name == user_name)
    #     .first()
    # )
    db_user = (
        db.query(models.users)
        .options(joinedload(users.roles))
        .options(joinedload(users.actions))
        .filter(models.users.user_name == user_name)
        .first()
    )
    return db_user
def get_users_with_roles_for_tasks(db: Session):
    db_users = (
        db.query(models.users)
        .options(joinedload(users.roles))
        .all()
    )
    db_users = [ujson.loads(UsersSchemaRoles.from_orm(obj).json()) for obj in db_users]

    # db_users = [obj.__dict__ for obj in db_users]
    return db_users
def get_users_with_roles(db: Session):
    db_users = (
        db.query(models.users)
        .options(joinedload(users.roles))
        .all()
    )

    # for usrr in db_users:
    #     supervised_by_users = usrr.supervised_by
    #     users_schema = UsersSchema(usrr)
    #     users_schema.roles=usrr.roles
    #     users_schema.supervised_by=usrr.supervised_by
    #     users_schema.supervised_by_roles=usrr.supervised_by_roles
    #
    #     afdsf=0

    # db_users_schema_loaded=[]
    # for a_usr in db_users:
    #     # i must load the users and get them from supervisors_users in each user then pass it to from_orm and set the List[users]
    #     # same to roles
    #     # usernames_of_send_tasks_to_user = [usr['value'] for usr in obj.supervised_by_roles]
    #     # users_tasked_by_user = (
    #     #     db.query(models.users)
    #     #     .filter(models.users.user_name.in_(usernames_of_send_tasks_to_user))
    #     #     .all()
    #     # )
    #     supervises_userss=a_usr.supervised_by
    #     sup_other_users=InstrumentedList()
    #     sup_by_roles=InstrumentedList()
    #     if len(a_usr.supervised_by_roles)>0:
    #             sup_by_roles=a_usr.supervised_by_roles
    #     if len(supervises_userss)>0:
    #         for supp in supervises_userss:
    #             duser = (
    #                 db.query(models.users)
    #                 .options(joinedload(users.roles))
    #                 .options(joinedload(users.actions))
    #                 .filter(models.users.id == supp.user_id)
    #                 .first()
    #             )
    #             sup_other_users.append(duser)
    #     updat_user=ujson.loads(UsersSchema.from_orm(a_usr,sup_other_users,sup_by_roles).json())
    #     db_users_schema_loaded.append(updat_user)
    db_users = [ujson.loads(UsersSchema.from_orm(obj).json()) for obj in db_users]

    return db_users
def get_users_by_role(db: Session, role_name):
    db_users = (
        db.query(models.users)
        .options(joinedload(users.roles))
        .filter(models.users.roles.any(role_name=role_name))
        .all()
    )
    return db_users
def get_user(db: Session, user_id):
    db_user = (
        db.query(models.users)
        .options(joinedload(users.roles))
        .options(joinedload(users.actions))
        .filter(models.users.id == user_id)
        .first()
    )
    db_user = json.loads(UsersSchema.from_orm(db_user).json())
    return db_user


def get_user_display_name(db: Session, user_name):
    db_user = (
        db.query(models.users)
        .options(joinedload(users.roles))
        .options(joinedload(users.actions))
        .filter(models.users.user_name == user_name)
        .first()
    )
    db_user = json.loads(UsersSchema.from_orm(db_user).json())
    return db_user


def get_user_by_name(db: Session, user_name):
    if user_name == "null":
        return None
    db_user = (
        db.query(models.users)
        .options(joinedload(users.roles))
        .options(joinedload(users.actions))
        .filter(models.users.user_name == user_name)
        .first()
    )
    all_role = []
    for rol in db_user.roles:
        role = dict()
        role["user_name"] = db_user.user_name
        role["role_name"] = rol.role_name
        role["visible_tabs"] = []
        vis_tabs = rol.visible_tabs
        for vis_tab in vis_tabs:
            x = dict()
            x["tab_name"] = vis_tab.tab_name
            x["head_tab_name"] = vis_tab.head_tab_name
            role["visible_tabs"].append(x)
        role_visible_tabs_all = (
            db.query(models.roles_visible_tabs).filter(
                models.roles_visible_tabs.roleID == rol.id
            )
        ).all()
        all_field_rules = []
        all_perms = []
        for role_tab in role_visible_tabs_all:
            if role_tab.permission == "All":

                all_perms.append(2)
            elif role_tab.permission == "Read":
                all_perms.append(1)
            elif role_tab.permission == "None":
                all_perms.append(0)
            all_field_rules_for_single_tab = []
            for field_rule in role_tab.field_rules:
                field = dict()
                field["field_name"] = field_rule.field_name
                field["field_rule"] = field_rule.field_rule
                all_field_rules_for_single_tab.append(field)
            all_field_rules.append(all_field_rules_for_single_tab)

        for i, vis_tab_obj in enumerate(role["visible_tabs"]):
            try:
                vis_tab_obj["permission"] = all_perms[i]
                vis_tab_obj["field_rules"] = all_field_rules[i]
            except KeyError as ke:
                print(" there was key error when mapping visible tabs")
                print(traceback.format_exc())

            except Exception as ex:
                print(str(ex))
                print(traceback.format_exc())
        all_role.append(role)

    master_role = dict()
    master_role["user_name"] = "master_" + db_user.user_name
    master_role["user_name"] = "master_" + db_user.user_display_name
    master_role["role_name"] = "master_role"
    master_role["all_tabs"]: list = []

    all_field_rules: list = []
    all_perms: list = []
    first_time: bool = True
    last_role_calculation_of_permission_for_each_tab: int = len(all_role) - 1
    for role_index, a_role in enumerate(all_role):

        field_rules: list = []

        for i, vs in enumerate(a_role["visible_tabs"]):
            tab = dict()
            tab["tab_name"] = vs["tab_name"]
            tab["head_tab_name"] = vs["head_tab_name"]

            field_rules.append(vs["field_rules"])
            if first_time:
                all_perms.append(vs["permission"])

            if vs["permission"] == 2:
                tab["tab_permission"] = "All"
            else:
                if vs["permission"] == 1:
                    if all_perms[i] == 2:
                        tab["tab_permission"] = "All"
                    else:
                        tab["tab_permission"] = "Read"
                if vs["permission"] == 0:
                    if all_perms[i] == 2 or all_perms[i] == 1:
                        tab["tab_permission"] = "All"
                    else:
                        tab["tab_permission"] = "None"
            if role_index == last_role_calculation_of_permission_for_each_tab:
                master_role["all_tabs"].append(tab)

        first_time: bool = False
        all_field_rules.append(field_rules)
    final_field_rules: list = []
    from functools import reduce
    import operator

    for iii in range(len(all_field_rules)):
        out = reduce(operator.concat, all_field_rules[iii])
        final_field_rules.append(out)
    final_field_rules = reduce(operator.concat, final_field_rules)
    master_role["field_rules"] = final_field_rules
    return master_role


def get_full_role(db: Session, role_id):
    role_query = db.query(roles).filter_by(id=role_id).first()
    role = dict()
    role["role_name"] = role_query.role_name
    role["visible_tabs"] = []
    vis_tabs = role_query.visible_tabs
    for vis_tab in vis_tabs:
        new_tab_obj = dict()
        new_tab_obj["tab_name"] = vis_tab.tab_name
        new_tab_obj["head_tab_name"] = vis_tab.head_tab_name
        role["visible_tabs"].append(new_tab_obj)
    role_visible_tabs_all = (
        db.query(models.roles_visible_tabs).filter(
            models.roles_visible_tabs.roleID == role_query.id
        ).order_by(models.roles_visible_tabs.tabID.asc())
    ).all()
    #the bug is here
    all_visible_tabs = (db.query(models.visible_tabs)).all()
    all_field_rules = []
    all_perms = []
    for role_tab in role_visible_tabs_all:
        all_perms.append(role_tab.permission)
        all_field_rules_for_single_tab = []
        for field_rule in role_tab.field_rules:
            field = dict()
            field["field_name"] = field_rule.field_name
            field["field_rule"] = field_rule.field_rule
            all_field_rules_for_single_tab.append(field)
        all_field_rules.append(all_field_rules_for_single_tab)

    for i, vis_tab_obj in enumerate(role["visible_tabs"]):
        try:
            vis_tab_obj["permission"] = all_perms[i]
            vis_tab_obj["field_rules"] = all_field_rules[i]
        except KeyError:
            print(
                "there was an error mapping permission and field rules into visible tabs"
            )
            print(traceback.format_exc())
            print(str(ex))
        except Exception as ex:
            print(traceback.format_exc())
            print(str(ex))

    if len(all_visible_tabs) > len(role_visible_tabs_all):
        role_visible_tabs_all_names = [tab["tab_name"] for tab in role["visible_tabs"]]
        unidentified_visible_tabs = [
            x for x in all_visible_tabs if x.tab_name not in role_visible_tabs_all_names
        ]
        for unidentified_tab in unidentified_visible_tabs:
            void_tab_obj = dict()
            void_tab_obj["tab_name"] = unidentified_tab.tab_name
            void_tab_obj["head_tab_name"] = unidentified_tab.head_tab_name
            void_tab_obj["permission"] = "None"
            void_tab_obj["field_rules"] = []
            role["visible_tabs"].append(void_tab_obj)
    return role


def get_all_users(
    db: Session,
):
    db_users = db.query(users).all()
    return db_users


def get_all_visible_tabs(
    db: Session,
):
    db_visible_tabs = db.query(visible_tabs).all()
    return db_visible_tabs


def get_all_visible_tabs_full_info(
    db: Session,
):
    db_visible_tabs_full = db.query(visible_tabs).all()
    return db_visible_tabs_full


auth_handler = AuthHandler()


def check_if_user_exist(db: Session, user):
    user_exists = (
        db.query(models.users)
        .filter(models.users.user_name == user["user_name"])
        .first()
    )
    user_exists = (
        db.query(models.users)
        .filter(models.users.user_name == user["user_name"])
        .first()
    )
    if not user_exists:
        return True
    return False


def create_user(db: Session, user):
    user_exists = (
        db.query(models.users)
        .filter(models.users.user_name == user["user_name"])
        .first()
    )
    status_response = ""
    if not user_exists:
        hashed_password = auth_handler.get_password_hash(user["user_password"])
        user1 = models.users(
            user_name=user["user_name"],
            user_display_name=user["user_display_name"],
            user_password=hashed_password,
        )
        all_roles = []
        for rol in user["roles"]:
            role_exists = (
                db.query(models.roles)
                .filter(models.roles.role_name == rol["value"])
                .first()
            )
            all_roles.append(role_exists)

        user1.roles = all_roles
        #user1.supervisors.extend([user2, user3])
        usernames_of_send_tasks_to_roles=list()
        usernames_of_send_tasks_to_user=list()
        # must add the user then assign the tasks assigned to him because we will need the user id
        # if we do not commit the user insertion and the refreshing of the user, we cannot get the user id to assign the user his supervisors
        db.commit()
        db.refresh(user1)
        # user1=db.query(users).options(lazyload('supervised_by_roles')).filter(users.id == user1.id).first()
        if 'send_tasks_to' in user:
            send_tasks_to=user['send_tasks_to']
            if send_tasks_to is not None:
                if len(send_tasks_to)>0:
                    usernames_of_send_tasks_to_user=[usr['value'] for usr in send_tasks_to]
                    users_tasked_by_user = (
                        db.query(models.users)
                        .filter(models.users.user_name.in_(usernames_of_send_tasks_to_user))
                        .all()
                    )
                    for u_us in users_tasked_by_user:
                        user1.add_user_supervisor(user1, u_us, 'supervises_by_user')
                        # u_us.supervisor_type = 'supervises_by_user'
                        # db_user.supervisors.append(u_us)


        if 'send_tasks_to_roles' in user:
            send_tasks_to_roles=user['send_tasks_to_roles']
            if send_tasks_to_roles is not None:
                if len(send_tasks_to_roles)>0:
                    roles_of_send_tasks_to=[rol['value'] for rol in send_tasks_to_roles]
                    users_with_roles =get_users_with_roles_for_tasks(db=db)
                    lst_of_roles_to_send_to=[]
                    for a_user in users_with_roles:
                        role_names_of_user=[us['role_name'] for us in a_user['roles']]
                        if set(role_names_of_user).intersection(set(roles_of_send_tasks_to)):
                            user_tasked = (
                                db.query(models.users)
                                .filter(models.users.user_name == a_user["user_name"])
                                .first()
                            )
                            roles_to_send_tasks_to = db.query(roles).filter(roles.role_name.in_(roles_of_send_tasks_to)).all()
                            lst_of_roles_to_send_to.extend(roles_to_send_tasks_to)
                    # Use a set to store unique object IDs
                    unique_ids = set()

                    # Use a list comprehension to filter out duplicate objects based on the 'id' attribute
                    unique_roles_to_send_to = [obj for obj in lst_of_roles_to_send_to if
                                      obj.id not in unique_ids and not unique_ids.add(obj.id)]
                    # for un_rol_to_send in unique_roles_to_send_to:
                    #     user1.add_role_supervisor(user1, un_rol_to_send)

                    user1.supervised_by_roles=unique_roles_to_send_to
                            # user1.add_supervisor(user1, user_tasked, 'supervises_by_role', '',roles_to_send_tasks_to)
        try:
            db.commit()
        except IntegrityError as e:
            db.rollback()
            print("the username already exists")
            print(f"Insert failed due to unique constraint violation: {e}")
            return {"status": "WARNING", "message": "UserName ID Exists"}
        except Exception as exx:
            db.rollback()
            print(traceback.print_exc())
            print("the problem is here in :"+str(exx))
        return {"status": "SUCCESS", "message": "Inserted user Successfully"}

    else:
        # or Danger
        return {"status": "WARNING", "message": "User display name already exists"}


def create_role(db: Session, roles_req) -> SqlOpMsg:
    try:
        role_exists = (
            db.query(models.roles)
            .filter(models.roles.role_name == roles_req["role_name"])
            .first()
        )
        current_dt_field_rul = datetime.datetime.now().isoformat()
        if not role_exists:
            role1 = models.roles(
                role_name=roles_req["role_name"], role_desc="any role desc"
            )
            db.add(role1)
            db.commit()
            visible_tabs_rol = roles_req["visibleTabs"]
            all_visible_tabs = []

            try:
                # dtes = datetime.datetime.now().isoformat()
                for ii, index in enumerate(visible_tabs_rol):
                    vis_tab = visible_tabs_rol[ii]
                    visible_tab_exists = (
                        db.query(models.visible_tabs)
                        .filter(models.visible_tabs.tab_name == vis_tab["TabName"])
                        .first()
                    )
                    if not visible_tab_exists:
                        visible_tab = models.visible_tabs(
                            tab_name=vis_tab["TabName"],
                            head_tab_name=vis_tab["TabHeadDesc"],
                            tab_desc=["TabDesc"],
                        )
                        db.add(visible_tab)
                        db.commit()
                    else:
                        visible_tab = visible_tab_exists
                    permission_obj = vis_tab["TabAuth"]

                    role_tab_rel = roles_visible_tabs(
                        roleID=role1.id,
                        tabID=visible_tab.id,
                        AttachVisibleTabDate=current_dt_field_rul,
                        permission=permission_obj["value"],
                    )
                    db.add(role_tab_rel)
                    db.commit()
                    field_rules_objs = vis_tab["TabFieldsAuth"]
                    all_field_rules = []
                    all_visible_tab_field_rules = []
                    field_rules_objs = [
                        field_rule
                        for field_rule in field_rules_objs
                        if field_rule["FieldName"] != ""
                    ]
                    if len(field_rules_objs) > 0:
                        for field_rule in field_rules_objs:

                            field_rule_exists = (
                                db.query(models.field_rules)
                                .filter(
                                    models.field_rules.field_name
                                    == field_rule["FieldName"]
                                )
                                .filter(
                                    models.field_rules.field_rule
                                    == field_rule["FieldAuth"]
                                )
                                .first()
                            )
                            if not field_rule_exists and field_rule["FieldName"] != "":
                                field_rule_model = models.field_rules(
                                    field_name=field_rule["FieldName"],
                                    field_rule=field_rule["FieldAuth"],
                                )
                                db.add(field_rule_model)
                                db.commit()

                                all_field_rules.append(field_rule_model)
                            else:
                                field_rule_model = field_rule_exists
                            tab_role_field_rules = role_tabs_field_rules(
                                field_rules=field_rule_model.id,
                                role_tab_id=role_tab_rel.id,
                                AttachFieldRuleDate=current_dt_field_rul,
                            )
                            db.add(tab_role_field_rules)
                            db.commit()
                return {"status": "SUCCESS", "message": "Inserted Successfully"}
            except Exception as ex:
                print(traceback.format_exc())
                return {"status": "FAILED", "message": str(ex)}
        else:
            raise RecordExistsException("role already exists")

    except RecordExistsException as uee:
        print(traceback.format_exc())
        return {"status": "FAILED", "message": "role already exists"}
    except Exception as ex:
        print(traceback.format_exc())
        print(str(ex))
def get_role_to_modify(db:Session,role_id):
    db_role = (
        db.query(models.roles)
        .options(joinedload(roles.users))
        .options(joinedload(roles.visible_tabs))
        .filter(models.roles.id == role_id)
        .first()
    )
    return db_role

def update_role(db:Session,roles_req,role_id:int)->SqlOpMsg:
    try:
        db_role = get_role_to_modify(db, role_id)
        current_dt_field_rul = datetime.datetime.now().isoformat()
        db_role.role_name=roles_req["role_name"]
        db_role.visible_tabs_roles.clear()
        db.commit()
        db_role.visible_tabs.clear()
        db.commit()
        visible_tabs_rol = roles_req["visibleTabs"]
        all_visible_tabs = []
        # dtes = datetime.datetime.now().isoformat()
        for ii, index in enumerate(visible_tabs_rol):
            vis_tab = visible_tabs_rol[ii]
            visible_tab_exists = (
                db.query(models.visible_tabs)
                .filter(models.visible_tabs.tab_name == vis_tab["TabName"])
                .first()
            )
            if not visible_tab_exists:
                visible_tab = models.visible_tabs(
                    tab_name=vis_tab["TabName"],
                    head_tab_name=vis_tab["TabHeadDesc"],
                    tab_desc=["TabDesc"],
                )
                db.add(visible_tab)
                db.commit()
            else:
                visible_tab = visible_tab_exists
            permission_obj = vis_tab["TabAuth"]

            role_tab_rel = roles_visible_tabs(
                roleID=role_id,
                tabID=visible_tab.id,
                AttachVisibleTabDate=current_dt_field_rul,
                permission=permission_obj["value"],
            )
            db.add(role_tab_rel)
            db.commit()
            field_rules_objs = vis_tab["TabFieldsAuth"]
            all_field_rules = []
            all_visible_tab_field_rules = []
            field_rules_objs = [
                field_rule
                for field_rule in field_rules_objs
                if field_rule["FieldName"] != ""
            ]
            if len(field_rules_objs) > 0:
                for field_rule in field_rules_objs:

                    field_rule_exists = (
                        db.query(models.field_rules)
                        .filter(
                            models.field_rules.field_name
                            == field_rule["FieldName"]
                        )
                        .filter(
                            models.field_rules.field_rule
                            == field_rule["FieldAuth"]
                        )
                        .first()
                    )
                    if not field_rule_exists and field_rule["FieldName"] != "":
                        field_rule_model = models.field_rules(
                            field_name=field_rule["FieldName"],
                            field_rule=field_rule["FieldAuth"],
                        )
                        db.add(field_rule_model)
                        db.commit()

                        all_field_rules.append(field_rule_model)
                    else:
                        field_rule_model = field_rule_exists
                    tab_role_field_rules = role_tabs_field_rules(
                        field_rules=field_rule_model.id,
                        role_tab_id=role_tab_rel.id,
                        AttachFieldRuleDate=current_dt_field_rul,
                    )
                    db.add(tab_role_field_rules)
                    db.commit()
    except RecordExistsException as uee:
        print(traceback.format_exc())
        return {"status": "FAILED", "message": "role already exists"}
    except Exception as ex:
        print(traceback.format_exc())
        print(str(ex))

def get_all_roles_users(
    db: Session,
) -> list[roles]:
    return db.query(roles).options(joinedload(roles.users)).all()


def create_program_name(
    db: Session, program_name_pydantic: schemas_sql_alchemy.ProgramsNameC
) -> SqlOpMsg:
    db_program_name = get_program_name_if_exists(
        db, program_name=program_name_pydantic.program_name
    )
    if db_program_name:
        return {"status": "WARNING", "message": "Record Exists"}
    db_program_name: program_name_alchemy = models.program_name_alchemy(
        program_name=program_name_pydantic.program_name
    )
    db.add(db_program_name)
    db.commit()
    db.refresh(db_program_name)
    return {"status": "SUCCESS", "message": "Inserted Program Successfully"}


def get_programs_names(db: Session) -> program_name_alchemy:
    return db.query(program_name_alchemy).order_by(program_name_alchemy.id.desc()).all()


def delete_program_name(db: Session, program_id: int) -> SqlOpMsg:
    try:
        program_name: program_name_alchemy = (
            db.query(program_name_alchemy).filter_by(id=program_id).first()
        )
        if not program_name:
            raise RecordDoesNotExistException("Program not found")
        db.delete(program_name)
        db.commit()
        return {"status": "SUCCESS", "message": "Deleted Program Successfully"}
    except RecordDoesNotExistException:
        print(traceback.format_exc())
        return {"status": "FAILED", "message": "Deleting Program Failed"}
    except Exception as ex:
        print(traceback.format_exc())
        print(str(ex))


def get_episode_type_if_exists(db: Session, episode_type: str) -> episode_type_alchemy:
    return (
        db.query(models.episode_type_alchemy)
        .filter(models.episode_type_alchemy.episode_type == episode_type)
        .first()
    )
def get_episode_type_by_name(db: Session, episode_type: str):
    episode_type_obj=db.query(models.episode_type_alchemy).filter(models.episode_type_alchemy.episode_type == episode_type).first()
    ep_type=episode_type_obj.__dict__
    ep_type.pop('_sa_instance_state', None)
    return ep_type
def get_episode_type_by_id(db: Session, id):
    episode_type_obj=db.query(models.episode_type_alchemy).filter(models.episode_type_alchemy.id == id).first()
    ep_type=episode_type_obj.__dict__
    ep_type.pop('_sa_instance_state', None)
    return ep_type


def create_episode_type(
    db: Session, episode_type_pydantic: schemas_sql_alchemy.EpisodesTypeC
) -> SqlOpMsg:
    db_episode_type: models.episode_type_alchemy = get_episode_type_if_exists(
        db, episode_type=episode_type_pydantic.episode_type
    )
    if db_episode_type:
        return {"status": "WARNING", "message": "Record Exists"}
    db_episode_type = models.episode_type_alchemy(
        episode_type=episode_type_pydantic.episode_type
    )
    db.add(db_episode_type)
    db.commit()
    db.refresh(db_episode_type)
    return {"status": "SUCCESS", "message": "Inserted Episode Successfully"}


def get_episode_types(db: Session) -> list[models.episode_type_alchemy]:
    return (
        db.query(models.episode_type_alchemy)
        .order_by(models.episode_type_alchemy.id.desc())
        .all()
    )


def delete_episode_type(db: Session, episode_type_id: int) -> SqlOpMsg:
    try:
        episode_type: episode_type_alchemy = (
            db.query(models.episode_type_alchemy).filter_by(id=episode_type_id).first()
        )
        if not episode_type:
            raise RecordDoesNotExistException("episode type not found")
        db.delete(episode_type)
        db.commit()
        return {"status": "SUCCESS", "message": "Deleted Episode Type Successfully"}
    except RecordDoesNotExistException:
        print(traceback.format_exc())
        return {"status": "FAILED", "message": "Deleting episode type Failed"}
    except Exception as ex:
        print(traceback.format_exc())
        print(str(ex))

def get_graphic_if_exists(db: Session, graphic_name: str) -> graphic_alchemy:
    return (
        db.query(models.graphic_alchemy)
        .filter(models.graphic_alchemy.name == graphic_name)
        .first()
    )
def get_graphic_by_name(db: Session, graphic_name: str):
    graphic_person=db.query(models.graphic_alchemy).filter(models.graphic_alchemy.name == graphic_name).first()
    grphic=graphic_person.__dict__
    grphic.pop('_sa_instance_state', None)
    return grphic
def get_graphic_by_id(db: Session, graphic_id):
    graphic_person=db.query(models.graphic_alchemy).filter(models.graphic_alchemy.id == graphic_id).first()
    grphic=graphic_person.__dict__
    grphic.pop('_sa_instance_state', None)
    return grphic
def create_graphic(
    db: Session, graphic_pydantic: schemas_sql_alchemy.GraphicC
) -> SqlOpMsg:
    db_graphic: models.graphic_alchemy = get_graphic_if_exists(
        db, graphic_name=graphic_pydantic.name
    )
    if db_graphic:
        return {"status": "WARNING", "message": "Record Exists"}
    db_graphic_new = models.graphic_alchemy(
        name=graphic_pydantic.name
    )
    db.add(db_graphic_new)
    db.commit()
    db.refresh(db_graphic_new)
    return {"status": "SUCCESS", "message": "Inserted Graphic Successfully"}


def get_graphic(db: Session) -> list[models.graphic_alchemy]:
    return (
        db.query(models.graphic_alchemy)
        .order_by(models.graphic_alchemy.id.desc())
        .all()
    )


def delete_graphic(db: Session, graphic_id: int) -> SqlOpMsg:
    try:
        graphic_person: graphic_alchemy = (
            db.query(models.graphic_alchemy).filter_by(id=graphic_id).first()
        )
        if not graphic_person:
            raise RecordDoesNotExistException("graphic  not found")
        db.delete(graphic_person)
        db.commit()
        return {"status": "SUCCESS", "message": "Deleted Graphic Successfully"}
    except RecordDoesNotExistException:
        print(traceback.format_exc())
        return {"status": "FAILED", "message": "Deleting Graphic type Failed"}
    except Exception as ex:
        print(traceback.format_exc())
        print(str(ex))

def get_editor_if_exists(db: Session, editor_name: str) -> editor_alchemy:
    return (
        db.query(models.editor_alchemy)
        .filter(models.editor_alchemy.name == editor_name)
        .first()
    )
def get_editor_by_name(db: Session, editor_name: str)->dict:
    editor=db.query(models.editor_alchemy).filter(models.editor_alchemy.name == editor_name).first()
    edtor=editor.__dict__
    edtor.pop('_sa_instance_state', None)
    return edtor
def get_editor_by_id(db: Session, editor_id)->dict:
    editor=db.query(models.editor_alchemy).filter(models.editor_alchemy.id == editor_id).first()
    edtor=editor.__dict__
    edtor.pop('_sa_instance_state', None)
    return edtor

def create_editor(
    db: Session, editor_pydantic: schemas_sql_alchemy.EditorC
) -> SqlOpMsg:
    db_editor: models.editor_alchemy = get_editor_if_exists(
        db, editor_name=editor_pydantic.name
    )
    if db_editor:
        return {"status": "WARNING", "message": "Record Exists"}
    db_editor_new = models.editor_alchemy(
        name=editor_pydantic.name
    )
    db.add(db_editor_new)
    db.commit()
    db.refresh(db_editor_new)
    return {"status": "SUCCESS", "message": "Inserted Editor Successfully"}


def get_editor(db: Session) -> list[models.editor_alchemy]:
    return (
        db.query(models.editor_alchemy)
        .order_by(models.editor_alchemy.id.desc())
        .all()
    )


def delete_editor(db: Session, editor_id: int) -> SqlOpMsg:
    try:
        editor_person: editor_alchemy = (
            db.query(editor_alchemy).filter_by(id=editor_id).first()
        )
        if not editor_person:
            raise RecordDoesNotExistException("editor  not found")
        db.delete(editor_person)
        db.commit()
        return {"status": "SUCCESS", "message": "Deleted Editor Successfully"}
    except RecordDoesNotExistException:
        print(traceback.format_exc())
        return {"status": "FAILED", "message": "Deleting Editor type Failed"}
    except Exception as ex:
        print(traceback.format_exc())
        print(str(ex))
def get_action_if_exists(db: Session, action_name: str):
    return (
        db.query(models.actions)
        .filter(models.actions.action_name == action_name)
        .first()
    )
def create_action(
    db: Session, action_pydantic: schemas_sql_alchemy.UserActionC
) -> SqlOpMsg:
    db_action: models.actions = get_action_if_exists(
        db, action_name=action_pydantic.action_name
    )
    if db_action:
        return {"status": "WARNING", "message": "Record Exists"}
    db_action_new = models.actions(
        action_name=action_pydantic.action_name,action_desc=action_pydantic.action_desc
    )
    db.add(db_action_new)
    db.commit()
    db.refresh(db_action_new)
    return {"status": "SUCCESS", "message": "Inserted Action Successfully"}

def get_action(db: Session) -> list[models.actions]:
    return (
        db.query(models.actions)
        .order_by(models.actions.id.desc())
        .all()
    )


def delete_action(db: Session, action_id: int) -> SqlOpMsg:
    try:
        action: models.actions = (
            db.query(models.actions).filter_by(id=action_id).first()
        )
        if not action:
            raise RecordDoesNotExistException("action  not found")
        db.delete(action)
        db.commit()
        return {"status": "SUCCESS", "message": "Deleted Action Successfully"}
    except RecordDoesNotExistException:
        print(traceback.format_exc())
        return {"status": "FAILED", "message": "Deleting Action Failed"}
    except Exception as ex:
        print(traceback.format_exc())
        print(str(ex))
def get_tab_if_exists(
    db: Session, tab_name: str, tab_head_name: str
) -> models.visible_tabs:
    return (
        db.query(models.visible_tabs)
        .filter(models.visible_tabs.tab_name == tab_name)
        .first()
    )



def create_tab(
    db: Session, visible_tab_pydantic: schemas_sql_alchemy.VisibleTabsC
) -> SqlOpMsg:
    db_visible_tab = models.visible_tabs(
        tab_name=visible_tab_pydantic.tab_name,
        head_tab_name=visible_tab_pydantic.head_tab_name,
        tab_desc=visible_tab_pydantic.tab_desc,
    )
    db.add(db_visible_tab)
    db.commit()
    db.refresh(db_visible_tab)
    return {"status": "succuess", "message": "sucessfully inserted a tab"}


def get_role(db: Session, role_id: int) -> models.roles:
    try:
        role: models.roles = db.query(models.roles).filter_by(id=role_id).first()
        if not role:
            raise RecordDoesNotExistException("role  not found")
        return role
    except RecordDoesNotExistException:
        print(traceback.format_exc())
        return {"status": "Failed", "Message": "role not found cannot get"}
    except Exception as ex:
        print(traceback.format_exc())
        print(str(ex))


def update_user(db: Session, user_id: int, user_object_update) -> SqlOpMsg:
    db_user = get_user_to_modify(db, user_id)
    db_user.user_name = user_object_update["user_name"]
    db_user.user_display_name = user_object_update["user_display_name"]
    if user_object_update["user_password"] != "":
        hashed_password = auth_handler.get_password_hash(
            user_object_update["user_password"]
        )
        db_user.user_password = hashed_password

    db_user.roles.clear()
    db_user.actions.clear()
    db.commit()# this is in order to delete the supervisors before we delete the users

        #clear the supervisors relations to user before we later delete them, this is necessary
    db_user.supervised_by.clear()
    db_user.supervises_these_roles.clear()
    # db_user.roles.clear()
    # # db_user.supervisors.clear()
    # # db_user.supervised_by_roles.clear()
    # db_user.supervisors_these.clear()
    # db_user.supervised_by.clear()
    # db_user.supervised_by_roles.clear()
    db.commit()
    db.refresh(db_user)

    all_roles = []
    for rol in user_object_update["roles"]:
        role_exists = (
            db.query(models.roles)
            .filter(models.roles.role_name == rol["value"])
            .first()
        )
        all_roles.append(role_exists)
    db_user.roles = all_roles
    usernames_of_send_tasks_to_by_user = list()
    usernames_of_send_tasks_to_by_role = list()
    if 'send_tasks_to' in user_object_update:
        send_tasks_to = user_object_update['send_tasks_to']
        if send_tasks_to is not None:
            if len(send_tasks_to) > 0:
                usernames_of_send_tasks_to_user = [usr['value'] for usr in send_tasks_to]
                users_tasked_by_user = (
                    db.query(models.users)
                    .filter(models.users.user_name.in_(usernames_of_send_tasks_to_user))
                    .all()
                )
                for u_us in users_tasked_by_user:
                    db_user.add_user_supervisor(db_user, u_us, 'supervises_by_user')
                    # u_us.supervisor_type = 'supervises_by_user'
                    # db_user.supervisors.append(u_us)
            else:
                db_user.supervised_by.clear()

    if 'send_tasks_to_roles' in user_object_update:
        send_tasks_to_roles = user_object_update['send_tasks_to_roles']
        if send_tasks_to_roles is not None:
            if len(send_tasks_to_roles) > 0:
                roles_of_send_tasks_to = [rol['value'] for rol in send_tasks_to_roles]
                users_with_roles = get_users_with_roles_for_tasks(db=db)
                lst_of_roles_to_send_to = []
                for a_user in users_with_roles:
                    role_names_of_user = [us['role_name'] for us in a_user['roles']]
                    # if set(role_names_of_user).intersection(set(roles_of_send_tasks_to)):
                    #     user_tasked = (
                    #         db.query(models.users)
                    #         .filter(models.users.user_name == a_user["user_name"])
                    #         .first()
                    #     )
                    roles_to_send_tasks_to = db.query(roles).filter(
                            roles.role_name.in_(roles_of_send_tasks_to)).all()
                    lst_of_roles_to_send_to.extend(roles_to_send_tasks_to)
                # Use a set to store unique object IDs
                unique_ids = set()

                # Use a list comprehension to filter out duplicate objects based on the 'id' attribute
                unique_roles_to_send_to = [obj for obj in lst_of_roles_to_send_to if
                                           obj.id not in unique_ids and not unique_ids.add(obj.id)]
                db_user.supervised_by_roles = unique_roles_to_send_to
                # user1.add_supervisor(user1, user_tasked, 'supervises_by_role', '',roles_to_send_tasks_to)
            else:
                db_user.supervised_by_roles.clear()

    db.commit()
    db.refresh(db_user)

    return {"status": "SUCCESS", "message": "updated user Successfully"}

def delete_master_user(db: Session, master_user: str) -> SqlOpMsg:
    try:
        # https://stackoverflow.com/questions/26948397/how-to-delete-records-from-many-to-many-secondary-table-in-sqlalchemy

        user_name = db.query(models.users).filter_by(user_name=master_user).first()
        if not user_name:
            raise RecordDoesNotExistException("user does not exist to delete it")
        user_name.roles.clear()
        user_name.actions.clear()
        db.commit()
        db.delete(user_name)
        db.commit()
        return {"status": "SUCCESS", "message": "Deleted USER Successfully"}
    except RecordDoesNotExistException:
        return {"status": "FAILED", "message": "Deleting USER FAILED"}
    except Exception as ex:
        print(traceback.format_exc())
        print(str(ex))
def delete_user(db: Session, user_id: int, username_from_cookie: str) -> SqlOpMsg:
    try:
        # https://stackoverflow.com/questions/26948397/how-to-delete-records-from-many-to-many-secondary-table-in-sqlalchemy

        user_name = db.query(models.users).filter_by(id=user_id).first()
        if not user_name:
            raise RecordDoesNotExistException("user does not exist to delete it")
        if (
            user_name.user_name == MASTER_USERNAME
            or user_name.user_name == username_from_cookie
        ):
            return {"status": "FAILED", "message": "Deleting USER FAILED"}
        """The stale data error in SQLAlchemy typically occurs when you try to delete a record that has a relationship with other records, 
        and those related records have already been loaded into the session. In your case, when you try to delete a user who
         has many supervisors, you need to ensure that the related supervisors are also deleted before deleting the user."""

        #Remove the supervisors from the user to avoid any reference errors when deleting them.
        supervisors = user_name.supervisors_these[:]+user_name.supervised_by[:]
        user_name.send_actions_to.clear()
        user_name.sent_actions_by.clear()
        user_name.roles.clear()
        user_name.actions.clear()

        db.commit()# this is in order to delete the supervisors before we delete the users

        #clear the supervisors relations to user before we later delete them, this is necessary
        user_name.supervised_by.clear()
        user_name.supervises_these_roles.clear()

        # user_name.supervisors_these=[]
        # user_name.supervised_by=[]
        # user_name.supervised_by_roles=[]
        # #delete supervisors
        # for supervisor in supervisors:
        #     db.delete(supervisor)

        # add the two lines below worked
        db.commit()# this is in order to delete the supervisors before we delete the users
        db.refresh(user_name)# this is in order to refresh the user in the sql alchemy cache with supervisors deleted
        db.delete(user_name)
        db.commit()
        return {"status": "SUCCESS", "message": "Deleted USER Successfully"}
    except RecordDoesNotExistException:
        db.rollback()

        return {"status": "FAILED", "message": "Deleting USER FAILED"}
    except Exception as ex:

        db.rollback()

        print(traceback.format_exc())
        print(str(ex))

def delete_master_role(db: Session, master_name: str) -> SqlOpMsg:
    try:
        # https://stackoverflow.com/questions/26948397/how-to-delete-records-from-many-to-many-secondary-table-in-sqlalchemy
        role_name = db.query(models.roles).filter_by(role_name=master_name).first()
        if not role_name:
            raise RecordDoesNotExistException("role not found")
        # role_name.visible_tabs_roles=[]
        role_name.visible_tabs_roles.clear()
        role_name.users_roles.clear()

        db.commit()

        db.delete(role_name)
        db.commit()
        return {"status": "SUCCESS", "message": "Deleted Role Successfully"}
    except RecordDoesNotExistException:
        print(str(RecordDoesNotExistException))
        print(traceback.format_exc())
        return {"status": "Failed", "message": "role does not exist"}
    except Exception as ex:
        print(str(ex))
        print(traceback.format_exc())

def delete_role(db: Session, role_id: int) -> SqlOpMsg:
    try:
        role_name = db.query(models.roles).filter_by(id=role_id).first()
        if not role_name:
            raise RecordDoesNotExistException("role not found")
        # role_name.visible_tabs_roles=[]
        role_name.visible_tabs_roles.clear()
        role_name.users_roles.clear()
        role_name.supervises.clear()
        db.commit()
        db.refresh(role_name)
        # must delete supervises if they are connected to this role manualy ----TODO
        db.delete(role_name)
        db.commit()
        return {"status": "SUCCESS", "message": "Deleted Role Successfully"}
    except RecordDoesNotExistException:
        print(str(RecordDoesNotExistException))
        print(traceback.format_exc())
        return {"status": "Failed", "message": "role does not exist"}
    except Exception as ex:
        db.rollback()
        print(str(ex))
        print(traceback.format_exc())

def get_action_by_name(db: Session) -> models.actions:
        return (
            db.query(models.actions)
            .order_by(models.actions.id.desc())
            .all()
        )
import datetime as dtc
from dateutil.parser import parse
def create_send_actions(db: Session,user:users,episode_hash,subject='',program_name=''):

    action_commited="creating_episode_without_youtube"
    action= db.query(models.actions).filter_by(action_name=action_commited).first()
    if not action:
        action=schemas_sql_alchemy.UserActionC(action_name=action_commited,action_desc="creating an episode without adding youtube so that the multimedia inserts the youtube link later on after the producer insert the epsiode info")
        create_action(db,action)

    action= db.query(models.actions).filter_by(action_name=action_commited).first()

    current_date_time = dtc.datetime.now()
    episode_body = dict()
    episode_body['hash'] = episode_hash
    episode_body['subject'] = subject
    episode_body['program_name'] = program_name
    hash_checksum = hashlib.md5(
        json.dumps(episode_body, sort_keys=True, ensure_ascii=True).encode('utf-8')).hexdigest()
    episode_body['current_date_time']=str(current_date_time)

    users_supervised_by_users=user.supervised_by

    supervised_by_roles=user.supervised_by_roles
    all_users_with_roles = get_users_with_roles_for_tasks(db=db)
    roles_of_send_tasks_to = [rol.role_name for rol in supervised_by_roles]
    users_with_roles=[]
    for a_user in all_users_with_roles:
        role_names_of_user = [us['role_name'] for us in a_user['roles']]
        if set(role_names_of_user).intersection(set(roles_of_send_tasks_to)):
            user_tasked = (
                db.query(models.users)
                .filter(models.users.user_name == a_user["user_name"])
                .first()
            )
            users_with_roles.append(user_tasked)

    all_users_to_send_tasks_to=users_with_roles+users_supervised_by_users
    unique_ids = set()

    all_users_to_send_tasks_to = [obj for obj in all_users_to_send_tasks_to if
                               obj.id not in unique_ids and not unique_ids.add(obj.id)]
    for supervisor in all_users_to_send_tasks_to:
        db_send_action = models.send_actions(sender_id=user.id,receiver_id=supervisor.id,action_id=action.id,
                                             created_at=current_date_time,read_status='unread',completion_status='pending',
                                             is_task=True,task_type="sending_unfinished_episode_to_be_filled",action_body=episode_body)
        db_send_action.task_hash=hash_checksum
        db.add(db_send_action)
        db.commit()
        db.refresh(db_send_action)
    #send all actions to the super user
    usrs_with_admin_previlige = get_users_by_role(db=db,role_name='roleXF')
    for admin in usrs_with_admin_previlige:
        db_send_action = models.send_actions(sender_id=user.id, receiver_id=admin.id, action_id=action.id,
                                             created_at=current_date_time, read_status='unread',
                                             completion_status='pending',
                                             is_task=True, task_type="sending_unfinished_episode_to_be_filled",
                                             action_body=episode_body)
        db_send_action.task_hash=hash_checksum


        db.add(db_send_action)
        db.commit()
        db.refresh(db_send_action)
def get_send_actions(db: Session,current_user:models.users) -> list[models.send_actions]:
    # now = datetime.now()
    # last_48_hours = now - timedelta(hours=48)
    #.filter(models.send_actions.created_at >= last_48_hours)
    # this is for the notification
    return (
        db.query(models.send_actions).filter(
            (models.send_actions.completion_status == 'pending') &
            (models.send_actions.receiver_id == current_user.id))
           .order_by(models.send_actions.created_at.desc()).limit(30)
                .all()
            )
def get_send_actions_pending_sender(db: Session,current_user:models.users) -> list[models.send_actions]:
    # xx=db.query(models.send_actions).filter(models.send_actions.sender_id == current_user.id).group_by(models.send_actions.created_at).all()
    # grouped_records = db.query(models.send_actions, func.count(models.send_actions.id)).group_by(models.send_actions.created_at).all()
    # records = db.query(
    #     models.send_actions.created_at,
    #     func.MIN(models.send_actions.id).label('min_id')
    # ).filter(
    #     (models.send_actions.completion_status == 'pending') &
    #     (models.send_actions.sender_id == current_user.id)
    # ).group_by(models.send_actions.created_at).all()
    records = db.query(
        models.send_actions.created_at,
        func.MIN(models.send_actions.id).label('min_id')
    ).filter(
        (models.send_actions.sender_id == current_user.id)
    ).group_by(models.send_actions.created_at).all()

    # Iterate over the records and retrieve the corresponding rows
    rows = []
    for record in records:
        row = db.query(models.send_actions).filter(models.send_actions.id == record.min_id).first()
        rows.append(row)
    # records = db.query(models.send_actions.created_at).filter(
    #         (models.send_actions.completion_status == 'pending') &
    #         (models.send_actions.sender_id == current_user.id)).distinct().all()
    # l_values = [record.__dict__[l_columns[0]] for record in records]
    return rows
def get_send_actions_pending(db: Session,current_user:models.users) -> list[models.send_actions]:
    return (
        db.query(models.send_actions).filter(
            (models.send_actions.completion_status == 'pending') &
            (models.send_actions.receiver_id == current_user.id))
           .order_by(models.send_actions.created_at.desc())
                .all()
            )
def get_send_actions_for_me(db: Session,current_user:models.users) -> list[models.send_actions]:

    return (
        db.query(models.send_actions).filter(
            (models.send_actions.sender_id == current_user.id)  &
            (models.send_actions.receiver_id == models.send_actions.updater_id))
           .order_by(models.send_actions.created_at.desc())
                .all()
            )
def get_send_actions_received(db: Session,current_user:models.users) -> list[models.send_actions]:

    return (
        db.query(models.send_actions).filter(
            (models.send_actions.receiver_id == current_user.id))
           .order_by(models.send_actions.created_at.desc())
                .all()
            )
def get_send_actions_pending_by_hash(db: Session,task_hash) -> list[models.send_actions]:
    return (
        db.query(models.send_actions).filter(
            (models.send_actions.completion_status == 'pending') &
            (models.send_actions.task_hash == task_hash))
                .all()
            )
def update_send_actions(db: Session, task_hash: str,current_user:models.users) -> SqlOpMsg:
    db_send_actions:models.send_actions = get_send_actions_pending_by_hash(db, task_hash)
    current_date_time = dtc.datetime.now()

    for send_action in db_send_actions:
        send_action.completion_status = "completed"
        send_action.updater_id=current_user.id
        send_action.updated_at=current_date_time
        db.commit()
    return {"status": "SUCCESS", "message": "updated user Successfully"}

def delete_send_actions(db: Session, episode_hash):
    try:
        # to filter on specific key in json type in sql alchemy u must do the following
        # then delete all such records
        send_actions = db.query(models.send_actions).filter(
        text("action_body->>'hash' = :value").bindparams(value=episode_hash)
        ).delete(synchronize_session='fetch')
        #.delete(synchronize_session='fetch')
        db.commit()
        return {"status": "SUCCESS", "message": "Deleted  send action Successfully"}
    except RecordDoesNotExistException:
        print(traceback.format_exc())
        return {"status": "FAILED", "message": "Deleting send action Failed"}
    except Exception as ex:
        print(traceback.format_exc())
        print(str(ex))
        return {"status": "FAILED", "message": "Deleting send action Failed"}

def main():
    print("happy crud")


if __name__ == "__main__":
    main()
