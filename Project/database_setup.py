# Imports
import os
import sys

from sqlalchemy import Column, ForeignKey, Integer, String, Table, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref

Base = declarative_base()

# Association Table
user_fav = Table('user_fav', Base.metadata,
                             Column('recipe_id', String(500),
                                    ForeignKey('recipe.id')),
                             Column('user_id', String(500),
                                    ForeignKey('user.id')))

# User Class
class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))
    favorites = relationship('Recipe', secondary=user_fav, backref='favs')


# Course Class
class Course(Base):
    __tablename__ = 'course'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)


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
    image = Column(String(500), nullable=True)
    course_id = Column(Integer, ForeignKey('course.id'))
    course = relationship(Course)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)



# Create Database

engine = create_engine('sqlite:///recipecollection.db')


Base.metadata.create_all(engine)
