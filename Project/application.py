# Imports
import json
import random
import string

import httplib2
from flask import (Flask, flash, jsonify, make_response, redirect,
                   render_template, request)
from flask import session as login_session
from flask import url_for

import requests
from database_setup import Base, Course, Recipe
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Database Binding
app = Flask(__name__)


engine = create_engine('sqlite:///recipecollection.db')

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# App Home
@app.route('/')
def appHome():
    session = DBSession()
    courses = session.query(Course).all()
    if 'username' not in login_session:
        return render_template('publichome.html', courses=courses)
    else:
        return render_template('home.html', courses=courses)

# Course Home
@app.route('/course/<int:course_id>/')
def courseMenu(course_id):
    session = DBSession()
    course = session.query(Course).filter_by(id=course_id).one()
    items = session.query(Recipe).filter_by(course_id=course.id)
    return render_template('course.html', course=course, items=items)


# Create Recipe
@app.route('/courses/<int:course_id>/new', methods=['GET', 'POST'])
def newRecipe(course_id):
    session = DBSession()
    if request.form:
        newItem = Recipe(name=request.form.get('name'), total_time=request.form.get('total_time'), prep_time=request.form.get(
            'prep_time'), cook_time=request.form.get('cook_time'), difficulty=request.form.get('difficulty'), directions=request.form.get('directions'), ingredients=request.form.get('ingredients'), output=request.form.get('output'), course_id=course_id)
        session.add(newItem)
        session.commit()
        print "New Team Created"
        return redirect(url_for('courseMenu', course_id=course_id))
    else:
        return render_template('newrecipe.html', course_id=course_id)


# Edit Recipe
session = DBSession()
@app.route('/courses/<int:course_id>/<int:recipe_id>/edit', methods=['GET', 'POST'])
def editRecipe(course_id, recipe_id):
    session = DBSession()
    editedItem = session.query(Recipe).filter_by(id=recipe_id).one()

    if request.form:
        if request.form.get('name'):
            editedItem.name = request.form.get('name')
        if request.form.get('total_time'):
            editedItem.total_time = request.form.get('total_time')
        if request.form.get('prep_time'):
            editedItem.prep_time = request.form.get('prep_time')
        if request.form.get('cook_time'):
            editedItem.cook_time = request.form.get('cook_time')
        if request.form.get('difficulty'):
            editedItem.difficulty = request.form.get('difficulty')
        if request.form.get('directions'):
            editedItem.directions = request.form.get('directions')
        if request.form.get('ingredients'):
            editedItem.ingredients = request.form.get('ingredients')
        if request.form.get('output'):
            editedItem.output = request.form.get('output')
        session.add(editedItem)
        session.commit()
        return redirect(url_for('courseMenu', course_id=course_id))
    else:
        return render_template('editrecipe.html', course_id=course_id, recipe_id=recipe_id, item=editedItem)


# Delete Recipe
@app.route('/courses/<int:course_id>/<int:recipe_id>/delete', methods=['GET', 'POST'])
def deleteRecipe(course_id, recipe_id):
    session = DBSession()
    itemToDelete = session.query(Recipe).filter_by(id=recipe_id).one()
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        return redirect(url_for('courseMenu', course_id=course_id))
    else:
        return render_template('deleterecipe.html', item=itemToDelete)


if __name__ == '__main__':
    app.secret_key = 'super_secret-key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
