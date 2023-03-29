from . import models, schemas_sql_alchemy
from .auth import AuthHandler
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
    editor_alchemy
)

import json
import traceback
import datetime
import hashlib, json
from fastapi import HTTPException
from  sqlalchemy import text
from sqlalchemy.orm import Session, joinedload
from app.CustomClasses.typeHintMsh import SqlOpMsg
from app.MyExceptions.RecordExistsException import RecordExistsException
from app.MyExceptions.RecordDoesNotExistException import RecordDoesNotExistException

# https://stackoverflow.com/questions/5756559/how-to-build-many-to-many-relations-using-sqlalchemy-a-good-example
from .schemas_sql_alchemy import UsersSchema,GuestInfo
# from marshmalow_sqlalchemy import ModelSerializer
MASTER_USERNAME = "12345"


def get_host_name_if_exists(db: Session, host_name: str) -> models.host_names_alchemy:
    return (
        db.query(models.host_names_alchemy)
        .filter(models.host_names_alchemy.host_name == host_name)
        .first()
    )


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


def create_guest_info(
    db: Session, guest_info_pydantic: schemas_sql_alchemy.GuestsInfoC
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
        image=guest_info_pydantic.image,expertise=guest_expert,
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

def update_guest_info(db: Session, guest_info_id: int, guest_object_update:schemas_sql_alchemy.GuestsInfoC) -> SqlOpMsg:
    db_guest_info:models.guests_info = get_guest_info_to_modify(db, guest_info_id)
    db_guest_info.name=guest_object_update.name
    db_guest_info.image=guest_object_update.image
    db_guest_info.phone_number=guest_object_update.phone_number
    db_guest_info.country=guest_object_update.country
    db_guest_info.country=guest_object_update.country
    db_guest_info.email=guest_object_update.email
    db_guest_info.landline=guest_object_update.landline

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
    db_user = (
        db.query(models.users)
        .options(joinedload(users.roles))
        .options(joinedload(users.actions))
        .options(joinedload(users.supervisors))
        .filter(models.users.user_name == user_name)
        .first()
    )
    return db_user
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
        )
    ).all()
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
        if 'send_tasks_to' in user:
            send_tasks_to=user['send_tasks_to']
            if send_tasks_to is not None:
                usernames_of_send_tasks_to=[usr['value'] for usr in send_tasks_to]
                users_tasked = (
                    db.query(models.users)
                    .filter(models.users.user_name.in_(usernames_of_send_tasks_to))
                    .all()
                )
                user1.supervisors = users_tasked

        try:
            db.commit()
        except IntegrityError as e:
            db.rollback()
            print("the username already exists")
            print(f"Insert failed due to unique constraint violation: {e}")
            return {"status": "WARNING", "message": "UserName ID Exists"}

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
                dtes = datetime.datetime.now().isoformat()
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
                        AttachVisibleTabDate=dtes,
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
        print(str(ex))
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
    all_roles = []
    for rol in user_object_update["roles"]:
        role_exists = (
            db.query(models.roles)
            .filter(models.roles.role_name == rol["value"])
            .first()
        )
        all_roles.append(role_exists)
    db_user.roles = all_roles
    if 'send_tasks_to' in user_object_update:
        send_tasks_to = user_object_update['send_tasks_to']
        if send_tasks_to is not None:
            usernames_of_send_tasks_to = [usr['value'] for usr in send_tasks_to]
            users_tasked = (
                db.query(models.users)
                .filter(models.users.user_name.in_(usernames_of_send_tasks_to))
                .all()
            )
            db_user.supervisors = users_tasked
    db.commit()
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
        # role_name.visible_tabs_roles=[]
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
        # https://stackoverflow.com/questions/26948397/how-to-delete-records-from-many-to-many-secondary-table-in-sqlalchemy
        role_name = db.query(models.roles).filter_by(id=role_id).first()
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

    for supervisor in user.supervisors:
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
    return (
        db.query(models.send_actions).filter(
            (models.send_actions.completion_status == 'pending') &
            (models.send_actions.receiver_id == current_user.id))
           .order_by(models.send_actions.created_at.desc()).limit(30)
                .all()
            )
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
            (models.send_actions.sender_id == current_user.id) )
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
