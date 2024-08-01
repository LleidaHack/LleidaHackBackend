from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from src.utils.Base.BaseModel import BaseModel


class LleidaHackerGroupUser(BaseModel):
    __tablename__ = 'lleida_hacker_group_user'
    group_id = Column(Integer,
                      ForeignKey('lleida_hacker_group.id'),
                      primary_key=True)
    user_id = Column(Integer,
                     ForeignKey('lleida_hacker.user_id'),
                     primary_key=True)


class LleidaHackerGroup(BaseModel):
    __tablename__ = 'lleida_hacker_group'
    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String)
    description: str = Column(String)
    leader_id: int = Column(Integer,
                            ForeignKey('lleida_hacker.user_id'),
                            nullable=True)
    # members: List[LleidaHacker] = relationship('LleidaHacker', secondary='group_lleida_hacker_user', backref='lleida_hacker_group')
    # members: List[LleidaHacker] = relationship('LleidaHacker', back_populates='lleida_hacker_group')
    members = relationship('LleidaHacker',
                           secondary='lleida_hacker_group_user')
