from Models import Hacker as ModelHacker
from Models import HackerGroup as ModelHackerGroup

from schema import HackerGroup as SchemaHackerGroup

from database import get_db

from sqlalchemy.orm import Session
from fastapi import Depends, Response, APIRouter

router = APIRouter(
    prefix="/hackergroup",
    tags=["HackerGroup"],
    # dependencies=[Depends(get_db)],
    # dependencies=[Depends(get_token_header)],
    # responses={404: {"description": "Not found"}},
)

@router.get("/all", tags=["Hacker Group"])
async def get_hacker_groups(db: Session = Depends(get_db)):
    return db.query(ModelHackerGroup).all()

@router.get("/{groupId}", tags=["Hacker Group"])
async def get_hacker_group(groupId: int, response: Response, db: Session = Depends(get_db)):
    return db.query(ModelHackerGroup).filter(ModelHackerGroup.id == groupId).first()

@router.post("/", tags=["Hacker Group"])
async def add_hacker_group(payload:SchemaHackerGroup, response: Response, db: Session = Depends(get_db)):
    new_hacker_group = ModelHackerGroup(name=payload.name,
                                        description=payload.description,
    )
    db.add(new_hacker_group)
    db.commit()
    return {"success": True, "created_id": new_hacker_group.id}

@router.put("/{groupId}", tags=["Hacker Group"])
async def update_hacker_group(groupId: int, payload: SchemaHackerGroup, response: Response, db: Session = Depends(get_db)):
    hacker_group = db.query(ModelHackerGroup).filter(ModelHackerGroup.id == groupId).first()
    hacker_group.name = payload.name
    hacker_group.description = payload.description
    db.commit()


@router.delete("/{groupId}", tags=["Hacker Group"])
async def delete_hacker_group(groupId:int, response: Response, db: Session = Depends(get_db)):
    # result = VerifyToken(token.credentials).verify()
    # if result.get("status"):
    #    response.status_code = status.HTTP_400_BAD_REQUEST
    #    return result
    db.query(ModelHackerGroup).filter(ModelHackerGroup.id == groupId).delete()
    return {"success": True}

@router.get("/{groupId}/members", tags=["Hacker Group"])
async def get_hacker_group_members(groupId: int, response: Response, db: Session = Depends(get_db)):
    return db.query(ModelHackerGroup).filter(ModelHackerGroup.id == groupId).all().members

@router.post("/{groupId}/add/{hackerId}", tags=["Hacker Group"])
async def add_hacker_to_group(groupId: int, hackerId: int, response: Response, db: Session = Depends(get_db)):
    hacker_group = db.query(ModelHackerGroup).filter(ModelHackerGroup.id == groupId).first()
    hacker = db.query(ModelHacker).filter(ModelHacker.id == hackerId).first()
    hacker_group.members.routerend(hacker)
    db.commit()