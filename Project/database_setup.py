import os
import sys

from sqlalchemy import Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

# Course Class
class Course(Base):
    __tablename__ = 'course'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)


# Recipe Class
class Recipe(Base):
    __tablename__ = 'recipe'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    total_time = Column(Integer, nullable=False)
    prep_time = Column(Integer, nullable=False)
    cook_time = Column(Integer, nullable=False)
    difficulty = Column(Integer, nullable=False)
    directions = Column(String(500), nullable=False)
    ingredients = Column(String(500), nullable=False)
    output = Column(String(250), nullable=False)
    course_id = Column(Integer, ForeignKey('course.id'))
    course = relationship(Course)





engine = create_engine('sqlite:///recipecollection.db')


Base.metadata.create_all(engine)
