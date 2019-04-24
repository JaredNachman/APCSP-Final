# Imports
import os
import sys

from database_setup import Base, Course, Recipe, User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Connect to Database Session
engine = create_engine('sqlite:///recipecollection.db')

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won\'t be persisted into the database until you call
# session.commit(). If you\'re not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Database Templates
# User Template
User1 = User(name="Jared Nachman", email="jarednachman@gmail.com",
             picture='...')
session.add(User1)
session.commit()

# Coruse Template
course1 = Course(name="Appetizer")

session.add(course1)
session.commit()

recipe1= Recipe(user_id=1, name="Stuffed Mushrooms", total_time="35 Minutes", prep_time="10 Minutes", cook_time="25 Minutes",
                difficulty="3", directions="Heat oven on high and combine all ingreients in a bowl Then drizzle olive oil on mushrooms on a baking pan Finally use a spoon and fill the mushrooms with the filling",
              ingredients="Mushrooms, Bread Crumbs, Garlic, Mint, Black, Pepper", output="28 Mushrooms", course=course1)

session.add(recipe1)
session.commit()

course2 = Course(name="Main Course")

session.add(course2)
session.commit()


recipe1=Recipe(user_id=1, name="Salmon", total_time="45 Minutes", prep_time="15 Minutes", cook_time="30 Minutes",
                difficulty="5", directions="First wash the salmon and pat dry Then add garlic salt and pepper on all sides Bake for 30 Minutes",
                ingredients="Salmon, Salt, Pepper, Garlic, Lemon", output="2 Servings", course=course2)

session.add(recipe1)
session.commit()

course3 = Course(name="Dessert")

session.add(course3)
session.commit()

recipe1=Recipe(user_id=1, name="Chocolate Chip Cookies", total_time="35 Minutes", prep_time="20 Minutes", cook_time="25 Minutes",
                difficulty="3", directions="Mix all dry ingreients in one bowl In another add all wet Then combine dry in wet and stir in chocolate chips and place balls on sheet and bake",
                ingredients="Butter, Sugar, Flour, Baking, Soda, Chocolate Chips, Eggs", output="40 cookies", course=course3)

session.add(recipe1)
session.commit()

print "template course and recipes added"
