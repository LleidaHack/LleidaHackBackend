from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlmodel import Relationship, SQLModel, Field

from src.impl.LleidaHacker.model import LleidaHacker

class LleidaHackerGroupUser(SQLModel, table=True):
    __tablename__ = 'lleida_hacker_group_user'
    group_id: int = Field(foreign_key='lleida_hacker_group.id', primary_key=True)
    user_id: int = Field(foreign_key='lleida_hacker.user_id',primary_key=True)


class LleidaHackerGroup(SQLModel, table=True):
    __tablename__ = 'lleida_hacker_group'
    id: int = Field(primary_key=True, index=True)
    name: str
    description: str
    leader_id: int = Field(foreign_key='lleida_hacker.user_id', nullable=True)
    # members: List[LleidaHacker] = relationship('LleidaHacker', secondary='group_lleida_hacker_user', backref='lleida_hacker_group')
    # members: List[LleidaHacker] = relationship('LleidaHacker', back_populates='lleida_hacker_group')
    members: list['LleidaHacker'] = Relationship(link_model=LleidaHackerGroupUser)
