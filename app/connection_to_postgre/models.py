from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table, Date, JSON, DateTime, ARRAY
from sqlalchemy.orm import relationship
from .database import AlchemySession
from sqlalchemy.ext.declarative import declarative_base

ses = AlchemySession()
Base = declarative_base(ses.engine)


# sqlalchemy.url = postgresql://postgres:postgres_ali@0.0.0.0:5446/alchemy


# THE LINK HERE IS VERY IMPORTANT
# https://www.gormanalysis.com/blog/many-to-many-relationships-in-fastapi/
# https://www.mariokandut.com/how-to-setup-https-ssl-in-localhost-react/
# https://www.thesharpener.net/how-to-use-https-in-your-react-app-production/
# https://www.youtube.com/watch?v=neT7fmZ6sDE
# https://www.nginx.com/blog/using-free-ssltls-certificates-from-lets-encrypt-with-nginx/
#
class host_names_alchemy(Base):
    """here we add host names into our app"""

    __tablename__ = "hosts"
    id = Column(Integer, primary_key=True, index=True)
    host_name = Column(String, index=True)


class guest_info_descriptions(Base):
    __tablename__ = "guest_info_descriptions"
    id = Column(Integer, primary_key=True, index=True)
    guestID = Column(Integer, ForeignKey("guests_info.id", ondelete="CASCADE"))
    descID = Column(Integer, ForeignKey("guests_desc.id", ondelete="CASCADE"))
    AttachRoleDate = Column(Date)


class guests_info(Base):
    """
    :param name

    :param expertise

    :param image optional

    :param phone_number optional

    :param phone_extension optional
    """
    __tablename__ = "guests_info"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    expertise_id = Column(Integer, ForeignKey('guest_expertise.id'), nullable=True)
    image = Column(
        String,
        nullable=True,
        default="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAQAAAAEACAYAAABccqhmAAAevUlEQVR4Xu2dC5BdRZnHvz73znvymJnMKwmS8EiiJGBCgmBwC5HdUgEphVURkfVR6q66bq2v3XIfllr7cHfVcrd8lhYCC6LlKquA7qJZEYIQMBAChAB5QDLvzCMzc+/cmbmn9/tuZsLMZCa3z50+97z+XZWaJNOnT/evu//n69fXikIa+vv1svocrR/XtF457nqlnXXk0hnaoXpFVKs1NfDPOk26MqRFQLYSQECR4iZKo0rRQOGnS6Pk0Etaufsd19nnVtKzOYf2NzaqoTDi4D4UjqC1rs/10MVE7hX5vHMFA93M/+eEI3fIBQgsjoBS6oDW7n1KOfeNj9N9y89UA4tL0c7TgQrA4GHdUFFBb+dM3EiKLuYOn7JTLKQCAuElwGKQdzXt5HZ/23iOftiwVg0GlduyC4B81XN99GZ3km4iTVezCV8VVOHxXhAImgAPIcb44/czNnW/X9VG97I4uOXMU9kEQDp+touu5XHS50jrV5WzkHgXCESCgFJP86D3n+ta6HYWgsly5Nl3AeCOn8500vt4TP8Z/vtZ5SgU3gECUSbAnf8F7i//VN1KN/stBL4KwESPvnQ8T1/nL/6mKFcI8g4CgRBw1B6Vpz+rXaUe9Ov9vgiAHtKNo6Pu3zvK+Shm8v2qOqSbBAJsAWhF7m2T9c4nlyxRPbbLbF0Ach36bTx4+Q6RbrSdWaQHAskloI7xpPn761apu2wysCYA/KWvyPW4X3Bd59P8d2vp2iws0gKB6BPQ365tdz7GlsG4jbJY6ah6UJ+VzdKd3PG32sgU0gABEFiYAHf+R1QNvbNmuTq4WE6LFoDRPr2NJuhunuhrXmxm8DwIgIApAdXPOwauql2tHjJ9Yr54ixKA7BH9BkrRT1ytlywmE3gWBEDAOwG2BEZ5R+F19SvVL7w/feKJkgUg26XfxQ",
    )
    image_hash = Column(
        String,
        nullable=True,
        default="a53d1042509d41a22787b51ba800d4f2",
    )
    phone_number = Column(String, nullable=True)
    phone_extension = Column(String, nullable=True)
    landline = Column(String, nullable=True)
    descriptions = relationship(
        "guests_desc", secondary=guest_info_descriptions.__table__, backref="guest_info_descriptions"
    )
    expertise = relationship("guest_expertise", back_populates="guests")
    email = Column(String, nullable=True)
    country = Column(String, nullable=True)


class options_tag_model(Base):
    __tablename__ = "options_tag_model"

    id = Column(Integer, primary_key=True, index=True)
    label = Column(String)
    value = Column(String)


class guests_desc(Base):
    """here we add guest descriptions into our app"""

    __tablename__ = "guests_desc"
    id = Column(Integer, primary_key=True, index=True)
    guest_desc = Column(String, index=True)
    guests = relationship(
        "guests_info", secondary=guest_info_descriptions.__table__, backref="descriptions_of_guests"
    )


class guest_expertise(Base):
    __tablename__ = "guest_expertise"
    id = Column(Integer, primary_key=True, index=True)
    expertise = Column(String)
    guests = relationship("guests_info", back_populates="expertise")


class guest_names_alchemy(Base):
    """here we add guest names into our app"""

    __tablename__ = "guests_name"
    id = Column(Integer, primary_key=True, index=True)
    guest_name = Column(String, index=True)


# class guest_expertise_alchemy(Base):
#     """here we add guest expertise into our app"""
#
#     __tablename__ = "guests_expertise"
#     id = Column(Integer, primary_key=True, index=True)
#     guest_expertise = Column(String, index=True)
#

# class guest_desc_alchemy(Base):
#     """here we add guest descriptions into our app"""
#
#     __tablename__ = "guests_desc"
#     id = Column(Integer, primary_key=True, index=True)
#     guest_desc = Column(String, index=True)


class program_name_alchemy(Base):
    """here we add program names into our app"""

    __tablename__ = "programs_name"
    id = Column(Integer, primary_key=True, index=True)
    program_name = Column(String, index=True)


class episode_type_alchemy(Base):
    """here we add episode types into our app"""

    __tablename__ = "episodes_type"
    id = Column(Integer, primary_key=True, index=True)
    episode_type = Column(String, index=True)


class graphic_alchemy(Base):
    """here we add graphic into our app"""

    __tablename__ = "graphic"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)


class editor_alchemy(Base):
    """here we add graphic into our app"""

    __tablename__ = "editor"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)


class users_roles(Base):
    __tablename__ = "users_roles"
    id = Column(Integer, primary_key=True, index=True)
    userID = Column(Integer, ForeignKey("users.id"))
    RoleID = Column(Integer, ForeignKey("roles.id"))
    AttachRoleDate = Column(Date)


class users_actions(Base):
    __tablename__ = "users_actions"
    id = Column(Integer, primary_key=True, index=True)
    userID = Column(Integer, ForeignKey("users.id"))
    actionID = Column(Integer, ForeignKey("actions.id"))
    AttachActionDate = Column(Date)


class actions(Base):
    __tablename__ = "actions"
    id = Column(Integer, primary_key=True, index=True)
    action_name = Column(String(255), index=True)
    action_desc = Column(String, index=True)
    users = relationship(
        "users", secondary=users_actions.__table__, backref="actions_users"
    )


class supervises_roles(Base):
    __tablename__ = 'supervises_roles'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"))
    role_supervises_id = Column(Integer, ForeignKey('roles.id', ondelete="CASCADE"))


class supervises_users(Base):
    __tablename__ = 'supervises_users'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    supervisor_id = Column(Integer, ForeignKey('users.id'))
    supervisor_type = Column(String)
    supervised_user = relationship('users', foreign_keys=[supervisor_id])
class send_actions(Base):
    """here we add episode types into our app"""

    __tablename__ = "send_actions"
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey('users.id'))
    receiver_id = Column(Integer, ForeignKey('users.id'))
    sender = relationship("users", foreign_keys=[sender_id])
    receiver = relationship("users", foreign_keys=[receiver_id])
    action_id = Column(Integer, ForeignKey('actions.id'))
    created_at = Column(DateTime)
    updated_at = Column(DateTime, nullable=True)
    read_status = Column(String(255))  # read or unread
    completion_status = Column(String(255))  # pending or completed
    is_task = Column(Boolean,
                     index=True)  # if true and receiver is current logged-in user then i can see the tasks and who
    task_type = Column(String(255))  # sending_unfinished_episode_to_be_filled,#filling_an_episode
    action_body = Column(JSON, nullable=True)
    task_hash = Column(String(1000))
    updater_id = Column(Integer)

    # updater_id = Column(Integer, ForeignKey('users.id'))
    # updater = relationship("users", foreign_keys=[updater_id])
    def get_updater(self,db):
        # Assuming you have a SQLAlchemy session named `session`
        updater = db.query(users).filter(users.id == self.updater_id).first()
        return updater
    # issued those tasks  to me
    # in the user form i must add a dropdown list on which users this new user will his actions(tasks) be transmitted to


class users(Base):
    """here we add episode types into our app"""

    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String(255), index=True, unique=True)
    user_display_name = Column(String(255))
    user_password = Column(String, index=True)
    roles = relationship(
        "roles", secondary=users_roles.__table__, backref="users_roles"
    )
    actions = relationship(
        "actions", secondary=users_actions.__table__, backref="users_actions"
    )
    supervises_these_roles = relationship(
        "roles", secondary=supervises_roles.__table__,
        primaryjoin=id == supervises_roles.role_supervises_id,
        secondaryjoin=id == supervises_roles.user_id, backref="supervised_by_roles",
    )
    supervisors_these = relationship('users', secondary='supervises_users',
                                 primaryjoin=id == supervises_users.supervisor_id,
                                 secondaryjoin=id == supervises_users.user_id,
                                 backref='supervised_by')


    send_actions_to = relationship('send_actions', foreign_keys=[send_actions.sender_id],
                                          cascade="all, delete, delete-orphan")
    sent_actions_by = relationship('send_actions', foreign_keys=[send_actions.receiver_id],
                                      cascade="all, delete, delete-orphan")
    supervisors_these_usrs = relationship('supervises_users', foreign_keys=[supervises_users.supervisor_id],
                                          cascade="all, delete, delete-orphan")
    supervised_by_usrs = relationship('supervises_users', foreign_keys=[supervises_users.user_id],
                                      cascade="all, delete, delete-orphan")

    # supervised_by_roles = relationship('supervises_roles', foreign_keys=[supervises_roles.role_supervises_id],  cascade="all, delete, delete-orphan")

    # supervises = relationship('supervises', backref='supervisor_user', foreign_keys=[supervises.user_id])

    def add_user_supervisor(self, user, supervisor, supervisor_type: str):
        """
        :param user:
        :param supervisor: object user that is a supervisor
        :param supervisor_type: type of supervisor, can by supervisor_by_role or supervisor_by_user
        :param supervisor_role_name: supervisor role
        :param supervises_these_roles:
        :return:
        """
        supervision = supervises_users(user_id=user.id, supervisor_id=supervisor.id, supervisor_type=supervisor_type)
        self.supervised_by_usrs.append(supervision)

    def add_role_supervisor(self, user, supervisor_role):
        """

        :return:
        """
        supervision = supervises_roles(user_id=user.id, role_supervises_id=supervisor_role.id)
        self.supervised_by_roles.append(supervision)



class role_tabs_field_rules(Base):
    __tablename__ = "role_tabs_field_rules"
    id = Column(Integer, primary_key=True, index=True)
    role_tab_id = Column(
        Integer, ForeignKey("roles_visible_tabs.id", ondelete="CASCADE")
    )
    field_rules = Column(Integer, ForeignKey("field_rules.id", ondelete="CASCADE"))
    AttachFieldRuleDate = Column(Date)


class field_rules(Base):
    __tablename__ = "field_rules"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    field_name = Column(String)
    field_rule = Column(String)
    roles_visible_tabs = relationship(
        "roles_visible_tabs",
        secondary=role_tabs_field_rules.__tablename__,
        backref="role_tabs_field_rules",
    )


class roles_visible_tabs(Base):
    __tablename__ = "roles_visible_tabs"
    id = Column(Integer, primary_key=True, index=True)
    roleID = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"))
    tabID = Column(Integer, ForeignKey("visible_tabs.id", ondelete="CASCADE"))
    permission = Column(String)
    field_rules = relationship(
        "field_rules",
        secondary=role_tabs_field_rules.__tablename__,
        backref="role_tabs_field_rules",
    )
    AttachVisibleTabDate = Column(Date)


"""
(psycopg2.errors.ForeignKeyViolation) update or delete on table "roles_visible_tabs" violates foreign key constraint "role_tab_permissions_role_tab_ID_fkey" on table "role_tab_permissions"
DETAIL:  Key (id)=(1) is still referenced from table "role_tab_permissions".

[SQL: DELETE FROM roles_visible_tabs WHERE roles_visible_tabs."roleID" = %(roleID)s AND roles_visible_tabs."tabID" = %(tabID)s]
[parameters: ({'roleID': 1, 'tabID': 1}, {'roleID': 1, 'tabID': 2}, {'roleID': 1, 'tabID': 3}, {'roleID': 1, 'tabID': 4}, {'roleID': 1, 'tabID': 5}, {'roleID': 1, 'tabID': 6}, {'roleID': 1, 'tabID': 7}, {'roleID': 1, 'tabID': 8}  ... displaying 10 of 15 total bound parameter sets ...  {'roleID': 1, 'tabID': 14}, {'roleID': 1, 'tabID': 15})]
(Background on this error at: https://sqlalche.me/e/14/gkpj)"""


class roles(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    role_name = Column(String)
    role_desc = Column(String)
    users = relationship(
        "users", secondary=users_roles.__tablename__, backref="roles_users"
    )
    visible_tabs = relationship(
        "visible_tabs",
        secondary=roles_visible_tabs.__tablename__,
        backref="roles_visible_tabs",
    )
    supervises = relationship(
        "users",
        secondary=supervises_roles.__tablename__,
        backref="supervised_by_roles",
    )
    # supervises_rol = relationship(
    #     "supervises_roles",
    #     secondary=supervises_roles.__tablename__,
    #     backref="supervises_roles",
    #     primaryjoin="roles.id == supervises_roles.role_id",
    #     secondaryjoin="roles.id == supervises_roles.supervisor_id"
    # )


class visible_tabs(Base):
    __tablename__ = "visible_tabs"
    id = Column(Integer, primary_key=True)
    tab_name = Column(String, unique=True)
    head_tab_name = Column(String)
    tab_desc = Column(String)
    roles = relationship(
        "roles",
        secondary=roles_visible_tabs.__tablename__,
        backref="visible_tabs_roles",
    )
