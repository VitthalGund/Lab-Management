from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from app.db.base import Base


class School(Base):
    """
    Represents a school entity in the database.
    """

    __tablename__ = "schools"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    location = Column(Text, nullable=True)
    principal_name = Column(String, nullable=True)
    trustees = Column(Text, nullable=True)
    about = Column(Text, nullable=True)

    # Relationship to Lab: A school can have multiple labs.
    labs = relationship("Lab", back_populates="school")
