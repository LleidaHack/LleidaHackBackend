from pydantic import BaseModel
class CompanyUser(BaseModel):
    role: str

    # class Config:
        # orm_mode = True
