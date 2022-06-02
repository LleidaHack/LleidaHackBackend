from sqlalchemy import Column, ForeignKey, Integer, String
from models.User import User

class CompanyUser(User):
    __tablename__ = 'company_user'
    user_id = Column(Integer, ForeignKey('llhk_user.id'), primary_key=True)
    company_id = Column(Integer, ForeignKey('company.id'), primary_key=True)
    role: str = Column(String)
    
    __mapper_args__ = {
        "polymorphic_identity": "company",
    }
