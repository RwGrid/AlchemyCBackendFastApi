import string
from typing import Union, List, Optional

import pydantic
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, SecretStr, Json
from pydantic.schema import datetime


class CustomBaseModel(BaseModel):
    def dict(self, **kwargs):
        hidden_fields = set(
            attribute_name
            for attribute_name, model_field in self.__fields__.items()
            if model_field.field_info.extra.get("hidden") is True
        )
        kwargs.setdefault("exclude", hidden_fields)
        return super().dict(**kwargs)


# the optional data type is when giving filling this field is not necessary, can be filled or not
# THE LINK HERE IS VERY IMPORTANT
# https://www.gormanalysis.com/blog/many-to-many-relationships-in-fastapi/

# https://super-unix.com/database/postgresql-insert-into-three-tables-with-many-to-many-from-one-table/
# https://www.gormanalysis.com/blog/many-to-many-relationships-in-fastapi/
# https://stackoverflow.com/questions/68394091/fastapi-sqlalchemy-pydantic-%E2%86%92-how-to-process-many-to-many-relations
# https://stackoverflow.com/questions/25668092/flask-sqlalchemy-many-to-many-insert-data
class AuthDetails(BaseModel):
    user_name: str
    user_password: str


class UsersC(BaseModel):
    user_name: str
    user_display_name: str
    user_password: SecretStr
    supervises_my_tasks_to: Optional[list]
    monitors_actions_of: Optional[list]

    class Config:
        orm_mode = True

    @pydantic.validator("user_name")
    @classmethod
    def username_valid(cls, value):
        # here we are wrapping this function to perform validation on the 'user_name' field passed to this class
        # what is returned here will be what is returned when calling this class on 'user_name' just like formik
        if any(p in value for p in string.punctuation):
            raise ValueError("Username must not include punctuation")
        else:
            return value

    @pydantic.validator("user_password")
    @classmethod
    def user_password_valid(cls, value):
        validated_value = value.get_secret_value()
        if len(validated_value) < 8:
            raise ValueError("Password must be at least 8 characters")

        if any(p in validated_value for p in string.punctuation):
            if any(d in validated_value for d in string.digits):
                if any(l in validated_value for l in string.ascii_lowercase):
                    if any(g in validated_value for g in string.ascii_uppercase):
                        return value
        raise ValueError(
            "Password needs at least one punctuation symbol,digit,upper and lower case character"
        )


class Users(UsersC):
    id: int

    class Config:
        orm_mode = True


class GuestsInfoC(BaseModel):
    name: str
    expertise: str
    phone_number: Optional[str]
    phone_extension: Optional[str]
    landline: Optional[str]
    descriptions: list
    image: Optional[str]
    email: Optional[str]
    country: Optional[str]

    class Config:
        orm_mode = True

    @classmethod
    def from_orm_guest_info_full(cls, orm_instance):
        data = dict(orm_instance.__dict__)
        data['descriptions'] = [desc.guest_desc for desc in orm_instance.descriptions]
        data['expertise'] = orm_instance.expertise.expertise
        return cls(**data)


class SendActionsC(BaseModel):
    action_name: str
    created_at: datetime
    updated_at: datetime
    read_status: str
    completion_status: str
    is_task: bool
    task_type: str  # sending_unfinished_episode_to_be_filled,#filling_an_episode
    action_body: Json

    class Config:
        orm_mode = True


class GuestInfo(GuestsInfoC):
    id: int

    class Config:
        orm_mode = True


class RolesC(BaseModel):
    role_name: str
    role_desc: Optional[str] = None


class Roles(RolesC):
    id: int

    class Config:
        orm_mode = True


class UsersSchema(Users):
    roles: List[Roles]
    supervisors: List[Users]


class VisibleTabsC(BaseModel):
    tab_name: str
    tab_desc: Optional[str] = None
    head_tab_name: str


class VisibleTabs(VisibleTabsC):
    id: int

    class Config:
        orm_mode = True


class PermissionsC(BaseModel):
    permission_name: str
    permission_desc: Optional[str] = None


class Permissions(PermissionsC):
    id: int

    class Config:
        orm_mode = True


class Field_RulesC(BaseModel):
    field_name: str
    field_rule: str


class Field_Rule(Field_RulesC):
    id: int

    class Config:
        orm_mode = True


class Field_RuleSchema(Field_Rule):
    visible_tabs: List[VisibleTabs]


class Roles_Users_Visible_Tabs_Schema(Roles):
    users: List[Users]
    visible_tabs: List[VisibleTabs]


class Roles_Visible_Tabs_Field_Roles_Permissions(Roles):
    visible_tabs: List[VisibleTabs]
    permissions: str
    field_rules: List[Field_Rule]


class VisibleTabs_Roles_Permissions_Field_Rules_Schema(VisibleTabs):
    roles: List[Roles]
    permissions: str
    field_rules: List[Field_Rule]


class HostsBaseC(BaseModel):
    host_name: str


class Hosts(HostsBaseC):
    id: int

    class Config:
        orm_mode = True


class GuestsNameC(BaseModel):
    guest_name: str


class GuestsNames(GuestsNameC):
    id: int

    class Config:
        orm_mode = True


class GuestsExpertiseC(BaseModel):
    expertise: str


class GuestsExpertise(GuestsExpertiseC):
    id: int

    class Config:
        orm_mode = True


class GuestsDescC(BaseModel):
    guest_desc: str


class GuestsDesc(GuestsDescC):
    id: int

    class Config:
        orm_mode = True


class ProgramsNameC(BaseModel):
    program_name: str


class ProgramsName(ProgramsNameC):
    id: int

    class Config:
        orm_mode = True


class EpisodesTypeC(BaseModel):
    episode_type: str


class EpisodesType(EpisodesTypeC):
    id: int

    class Config:
        orm_mode = True


class UserActionC(BaseModel):
    action_name: str
    action_desc: str


class UserAction(UserActionC):
    id: int

    class Config:
        orm_mode = True


class GraphicC(BaseModel):
    name: str


class Graphic(GraphicC):
    id: int

    class Config:
        orm_mode = True


class EditorC(BaseModel):
    name: str


class Editor(EditorC):
    id: int

    class Config:
        orm_mode = True


users = [
    {
        "username": "ali",
        "password": "xxx",
        "roles": [
            {
                "role_name": "this is the role name",
                "role_desc": "this is the role description",
                "visible_tabs": [
                    {
                        "tab_name": "insert",
                        "tab_desc": "insert an episode",
                        "head_tab_name": "insertion_tab",
                        "field_rules": [
                            {"field_name": "youtube_url", "field_rule": "readonly"},
                            {"field_name": "episode_type", "field_rule": "none"},
                        ],
                        "permissions": [
                            {"permission_name": "read"},
                            {"permission_name": "write"},
                        ],
                    }
                ],
            },
            {},
        ],
        "actions": [
            {"action_name": "notification", "action_desc": "received a notification"},
            {"action_name": "export", "action_desc": "received an export"},
        ],
    }
]
