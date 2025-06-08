from sqlalchemy.orm import DeclarativeBase


class BaseModel(DeclarativeBase):
    """
    Base model class using SQLAlchemy 2.0 best practices.

    This base model provides:
    - Modern SQLAlchemy 2.0 syntax with Mapped[] type annotations
    - DeclarativeBase as the foundation
    - __allow_unmapped__ = True for backward compatibility
    - Common utility methods

    Models can inherit from this base and add their own fields using the modern syntax:

    Example:
        class User(BaseModel):
            __tablename__ = 'users'

            id: Mapped[int] = mapped_column(primary_key=True)
            name: Mapped[str] = mapped_column(String(50))
            email: Mapped[Optional[str]] = mapped_column(String(100))
            created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    """

    __allow_unmapped__ = True

    def __repr__(self) -> str:
        """String representation of the model instance."""
        return f'<{self.__class__.__name__}(id={getattr(self, "id", None)})>'

    def to_dict(self) -> dict:
        """Convert model instance to dictionary."""
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }
