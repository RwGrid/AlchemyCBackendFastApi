from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from app.connection_to_postgre.models import guest_names_alchemy, guests_info
from fastapi import Depends
from fastapi import Request, Cookie, APIRouter
from sqlalchemy.orm import Session  # type: ignore
# from ..CustomClasses.typeHintMsh import SqlOpMsg
# from ..connection_to_postgre import crud, schemas_sql_alchemy
# from ..dependencies import verify_cookie
from app.CustomClasses.typeHintMsh import SqlOpMsg
from app.connection_to_postgre import crud, schemas_sql_alchemy
from app.dependencies import verify_cookie
from app.SessionFactory import get_db
from app.utilities.img_utility import base64_to_image

guests_router = APIRouter(
    tags=["episode_types"],
    dependencies=[Depends(verify_cookie)],
    responses={404: {"description": "Not found"}},
)


@guests_router.post("/CreateGuestInfo")
async def read_item(
        guest_info: schemas_sql_alchemy.GuestsInfoC, db: Session = Depends(get_db)
) -> SqlOpMsg:
    image = guest_info.image.split(';base64,')[1]
    image_hash=base64_to_image(image)
    return crud.create_guest_info(db=db, guest_info_pydantic=guest_info,img_hash=image_hash)
    # image = guest_info.image.split(';base64,')[1]
    # # Assuming base64_str is the string value without 'data:image/jpeg;base64,'
    # img = Image.open(io.BytesIO(base64.decodebytes(bytes(image, "utf-8"))))
    # img.save('my-image.png')


@guests_router.post("/CreateGuestN/")
async def create_guest_name(
        guest_name: schemas_sql_alchemy.GuestsNameC, db: Session = Depends(get_db)
):
    # raise HTTPException(status_code=400, detail="guest name already exists")
    return crud.create_guest_name(db=db, guest_names_pydantic=guest_name)


@guests_router.get(
    "/GetGuestsI",
    response_model=list[schemas_sql_alchemy.GuestInfo]
)
async def get_guest_info(db: Session = Depends(get_db)):
    # returning the base64 image is reducing the speed of the page as a whole
    # the solution is to create nginx and save the path in the database to the file system
    guest_info_recs: list[guests_info] = crud.get_guests_info(db)
    return guest_info_recs


@guests_router.get("/GetGuestI/{guest_info_id}", response_model=schemas_sql_alchemy.GuestInfo)
async def get_user_by_id(
        guest_info_id: int,
        db: Session = Depends(get_db),
):
    db_guest_info: dict = crud.get_guest_info(db, guest_info_id)
    json_compatible_item_data = jsonable_encoder(db_guest_info)
    return JSONResponse(content=json_compatible_item_data)


@guests_router.put("/UpdateGuestI/{g_id}")
async def update_guest_info(
        guestInfo: schemas_sql_alchemy.GuestsInfoC,g_id: int,
        db: Session = Depends(get_db),
):
    image = guestInfo.image.split(';base64,')[1]
    image_hash=base64_to_image(image)
    return crud.update_guest_info(db=db, guest_info_id=g_id, guest_object_update=guestInfo,img_hash=image_hash)


@guests_router.delete("/DeleteGuestI/{g_id}")
async def delete_guest_info(
        g_id: int,
        db: Session = Depends(get_db),
):
    return crud.delete_guest_info(db=db, guest_info_id=g_id)
    #  CommonEmployeesList in full template


@guests_router.post("/CreateGuestE")
async def create_guest_expertise(
        expertise: schemas_sql_alchemy.GuestsExpertiseC, db: Session = Depends(get_db)
):
    db_expertise = crud.get_guest_expertise_if_exists(
        db, guest_expertise=expertise.expertise
    )
    if db_expertise:
        return {"status": "WARNING", "message": "Record Exists"}

        # raise HTTPException(status_code=400, detail="guest expertise already exists")
    crud.create_guest_expertise(db=db, guest_expertise_pydantic=expertise)
    return {"status": "SUCCESS", "message": "Inserted Successfully"}


@guests_router.delete("/DeleteGuestE/{guest_expertise_id}")
async def delete_expertise(guest_expertise_id: int, db: Session = Depends(get_db)):
    return crud.delete_guest_expertise(db=db, id=guest_expertise_id)


@guests_router.get(
    "/GetGuestE", response_model=list[schemas_sql_alchemy.GuestsExpertise]
)
async def get_guest_expertises(db: Session = Depends(get_db)):
    expertises = crud.get_guest_expertises(db)
    return expertises


# -------------------end guest expertise--------------------
# ------------------ guest desc--------------------
@guests_router.post("/CreateGuestD")
async def create_guest_desc(
        desc: schemas_sql_alchemy.GuestsDescC, db: Session = Depends(get_db)
):
    db_desc = crud.get_guest_desc_if_exists(db, guest_desc=desc.guest_desc)
    if db_desc:
        return {"status": "WARNING", "message": "Record Exists"}
        # raise HTTPException(status_code=400, detail="guest desc already exists")
    crud.create_guest_desc(db=db, guest_desc_pydantic=desc)
    return {"status": "SUCCESS", "message": "Inserted Successfully"}


@guests_router.delete("/DeleteGuestD/{guest_desc_id}")
async def delete_desc(guest_desc_id: int, db: Session = Depends(get_db)):
    return crud.delete_guest_desc(db=db, guest_desc_id=guest_desc_id)


@guests_router.get("/GetGuestsD", response_model=list[schemas_sql_alchemy.GuestsDesc])
async def get_guest_expertises(
        db: Session = Depends(get_db), access_token: dict = Depends(verify_cookie)
):
    descriptions = crud.get_guest_desc(db)
    return descriptions
