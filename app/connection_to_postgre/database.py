import os
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import json
from sqlalchemy.orm import configure_mappers
script_directory = os.path.dirname(os.path.abspath(__file__))
with open(script_directory+"/postgre.json") as json_file:
    auth_data = json.load(json_file)
DATABASE_URI_INIT_DB_BASE = (
        "postgresql://"
        + auth_data["postgre_user"]
        + ":"
        + auth_data["postgre_pass"]
        + "@"
        + auth_data["postgre_host"]
        + ":"
        + auth_data["postgre_port"]
        + "/postgres"
)


class AlchemySession:
    def __init__(self, database_name: Optional[str] = "alchemy"):
        script_directory = os.path.dirname(os.path.abspath(__file__))
        with open(script_directory+"/postgre_initialized.json") as json_file:
            initialization = json.load(json_file)
            if initialization['postgre_initialized'] == 'false':
                # first we connect to postgres database as the 'postgres' user with the 'postgres' database
                engine = create_engine(DATABASE_URI_INIT_DB_BASE)
                # after connecting to the postgres database,we must create our own database to connect to
                # :https://stackoverflow.com/questions/6506578/how-to-create-a-new-database-using-sqlalchemy
                try:
                    with engine.connect() as conn:  # here use context manager of sql alchemy , because this is a
                        # connection to a resource
                        conn.execute("commit")
                        conn.execute("create database " + database_name)
                except Exception as ex:
                    print("database alchemy already exists")
        # then we reconnect to the newly created database
        SQLALCHEMY_DATABASE_URL = (
                "postgresql://"
                + auth_data["postgre_user"]
                + ":"
                + auth_data["postgre_pass"]
                + "@"
                + auth_data["postgre_host"]
                + ":"
                + auth_data["postgre_port"]
                + "/"
                + database_name
        )

        self.engine = create_engine(SQLALCHEMY_DATABASE_URL)
        self.Base = declarative_base(self.engine)

        # Base.metadata.bind(engine)
        self.session_maker = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine, expire_on_commit=True
        )  # factory method that creates 'Session' object when called,creating a session into our postgre database
        # then we reconnect to the newly created database

    def get_engine(self):
        """

        :return: return a session maker object that can create many sessions because it is a
        """
        return self.engine

    def get_session_only(self):
        """

        :return: return a session maker object that can create many sessions because it is a
        """
        return self.session_maker

# SQLALCHEMY_DATABASE_URL = (
#                 "postgresql://"
#                 + auth_data["postgre_user"]
#                 + ":"
#                 + auth_data["postgre_pass"]
#                 + "@"
#                 + auth_data["postgre_host"]
#                 + ":"
#                 + auth_data["postgre_port"]
#                 + "/"
#                 + "alchemy"
#         )
#
# engine = create_engine(SQLALCHEMY_DATABASE_URL)
#         # Base.metadata.bind(engine)
# session_maker = sessionmaker(
#             autocommit=False, autoflush=False, bind=engine, expire_on_commit=True
#         )  # factory method that creates 'Session' object when called,creating a session into our postgre database
# Base = declarative_base()
# sdf=0
