# from app.connection_to_postgre.database import AlchemySession
from connection_to_postgre.database import AlchemySession

"""
This is a Singelton Pattern at module level in python, see this link 
"""
# https://stackoverflow.com/questions/12223335/sqlalchemy-creating-vs-reusing-a-session
# https://fastapi.tiangolo.com/tutorial/bigger-applications/
alchemy_session = AlchemySession()
print("going through session")
session_maker = AlchemySession().get_session_only()
engine = alchemy_session.get_engine()


def get_db():
    db = session_maker()
    print("created new session")
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    else:
        db.commit()
    finally:
        db.close()
