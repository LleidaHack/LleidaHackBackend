from sqlalchemy import Boolean, Column, ForeignKey, Integer, String


class UserRegistration(BaseModel):
    __tablename__ = "user_event_registration"
    user_id = Column(Integer,
                     ForeignKey("my_user.id"),
                     primary_key=True,
                     index=True)
    event_id = Column(Integer,
                      ForeignKey("event.id"),
                      primary_key=True,
                      index=True)
    shirt_size: str = Column(String)
    food_restrictions: str = Column(String)
    cv: str = Column(String, nullable=True)
    description: str = Column(String, default="")
    github: str = Column(String, default="")
    linkedin: str = Column(String, default="")
    studies: str = Column(String, default="")
    study_center: str = Column(String, default="")
    location: str = Column(String, default="")
    how_did_you_meet_us: str = Column(String, default="")
    update_user: bool = Column(Boolean, default=True)
    confirmed_assistance: bool = Column(Boolean, default=False)
    confirm_assistance_token: str = Column(String, default="")
    # accepted: bool = Column(Boolean, default=False)