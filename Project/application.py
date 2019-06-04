"""Imports"""
import os
import json
import random
import string
import requests
import httplib2
from flask import (Flask, flash, make_response, redirect,
                   render_template, request, url_for, session as login_session)
from oauth2client.client import FlowExchangeError, flow_from_clientsecrets
from sqlalchemy import create_engine
from werkzeug.utils import secure_filename
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Course, Recipe, User


# File Upload



# Database Binding
APP = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Recipe Application"

UPLOAD_FOLDER = './static/images'
ALLOWED_EXTENSIONS = set(['jpg', 'pdf', 'jpeg', 'png'])

APP.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
APP.jinja_env.globals['login_session'] = login_session



ENGINE = create_engine('sqlite:///recipecollection.db')

Base.metadata.bind = ENGINE

DBSESSION = sessionmaker(bind=ENGINE)

# Anti-forgery state token
@APP.route('/login')
def show_login():
    """Create random state token and render login html file"""
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)

# Random Functions
def create_user():
    """If user does not exist in database, create new user"""
    session = DBSESSION()
    new_user = User(name=login_session['username'], email=login_session[
        'email'], picture=login_session['picture'])
    session.add(new_user)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id

def get_user_info(user_id):
    """Pull user from user id and get user info

    Keyword arguments:
    user_id -- the id of the user from the database
    """
    session = DBSESSION()
    user = session.query(User).filter_by(id=user_id).one()
    return user

def get_user_id(email):
    """Pull user from email and get user id

    Keyword arguments:
    email -- a valid email address
    """
    session = DBSESSION()
    user = session.query(User).filter_by(email=email).first()
    if user:
        return user.id
    return None


def get_user(email):
    """Pull user from email and return user

    Keyword arguments:
    email -- a valid email address
    """
    session = DBSESSION()
    user = session.query(User).filter_by(email=email).first()
    return user


# Google Connect
@APP.route('/gconnect', methods=['POST'])
def gconnect():
    """Validate state token and connect to google servers, redirect to login screen, then redirect home"""
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    header = httplib2.Http()
    result = json.loads(header.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = get_user_id(data["email"])
    if not user_id:
        user_id = create_user()
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius:\
     150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("You are now logged in as %s" % login_session['username'])
    print "done!"
    return output






@APP.route('/gdisconnect')
def gdisconnect():
    """Disconnect the user from the session"""
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    header = httplib2.Http()
    result = header.request(url, 'GET')[0]
    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    response = make_response(json.dumps('Failed to revoke token for given user.', 400))
    response.headers['Content-Type'] = 'application/json'
    return response

# Logout
@APP.route('/logout')
def disconnect():
    """Delete info stored in the login session and run the disconnect method"""
    gdisconnect()
    del login_session['gplus_id']
    del login_session['access_token']
    del login_session['username']
    del login_session['email']
    del login_session['picture']
    flash("You have been successfully logged out.")
    return redirect(url_for('app_home'))



# App Home
@APP.route('/')
def app_home():
    """Render one of the home html files based on user login status"""
    session = DBSESSION()
    courses = session.query(Course).all()
    print login_session
    if 'username' not in login_session:
        return render_template('publichome.html', courses=courses)

    return render_template('home.html', courses=courses)


# Course Home
@APP.route('/course/<int:course_id>/')
def course_menu(course_id):
    """Render html file and populate it with recipes for each course

    Keyword arguments:
    course_id -- the id of the course from the databse that the course menu will fall under
    """
    session = DBSESSION()
    course = session.query(Course).filter_by(id=course_id).one()
    items = session.query(Recipe).filter_by(course_id=course.id)
    if 'username' not in login_session:
        return render_template('publiccourse.html', course=course, items=items)

    user = get_user(login_session['email'])
    return render_template('course.html', course=course, items=items, user=user)



# Create Recipe
@APP.route('/courses/<int:course_id>/new', methods=['GET', 'POST'])
def new_recipe(course_id):
    """Pull input from form to create a new item in the database_setup

    Keyword arguments:
    course_id -- id of the course from the database that the ne recipe will go to
    """
    session = DBSESSION()
    if request.method == 'POST':
        input_file = request.files['image']
        if input_file:
            filename = secure_filename(input_file.filename)
            input_file.save(os.path.join(APP.config['UPLOAD_FOLDER'], filename))
            print filename
        new_item = Recipe(name=request.form.get('name'), \
        total_time=request.form.get('total_time'), \
        prep_time=request.form.get('prep_time'), \
        cook_time=request.form.get('cook_time'), \
        difficulty=request.form.get('difficulty'),\
         directions=request.form.get('directions'), \
         ingredients=request.form.get('ingredients'), \
         output=request.form.get('output'), image=filename, \
         user_id=login_session['user_id'], course_id=course_id)
        session.add(new_item)
        flash('%s Successfully Created!' % new_item.name)
        session.commit()
        return redirect(url_for('course_menu', course_id=course_id))
    else:
        return render_template('newrecipe.html', course_id=course_id)


# Edit Recipe
@APP.route('/courses/<int:course_id>/<int:recipe_id>/edit', methods=['GET', 'POST'])
def edit_recipe(course_id, recipe_id):
    """Edit information from a pre-existing recipe

    Keyword arguments:

    course_id -- the id of the couse from the database that the edited recipe is in
    recipe_id -- the id of the recipe from the database that the user is editng
    """
    session = DBSESSION()
    edited_item = session.query(Recipe).filter_by(id=recipe_id).one()

    if get_user_id(login_session['email']) != edited_item.user_id:
        flash("You are not authorized to edit this recipe.")
        return redirect(url_for('course_menu', course_id=course_id))

    if request.method == 'POST':
        if request.form.get('name'):
            edited_item.name = request.form.get('name')
        if request.form.get('total_time'):
            edited_item.total_time = request.form.get('total_time')
        if request.form.get('prep_time'):
            edited_item.prep_time = request.form.get('prep_time')
        if request.form.get('cook_time'):
            edited_item.cook_time = request.form.get('cook_time')
        if request.form.get('difficulty'):
            edited_item.difficulty = request.form.get('difficulty')
        if request.form.get('directions'):
            edited_item.directions = request.form.get('directions')
        if request.form.get('ingredients'):
            edited_item.ingredients = request.form.get('ingredients')
        if request.form.get('output'):
            edited_item.output = request.form.get('output')
        session.add(edited_item)
        session.commit()
        return redirect(url_for('course_menu', course_id=course_id))

    return render_template('editrecipe.html', course_id=course_id, \
    recipe_id=recipe_id, item=edited_item)


# Delete Recipe
@APP.route('/courses/<int:course_id>/<int:recipe_id>/delete', methods=['GET', 'POST'])
def delete_recipe(course_id, recipe_id):
    """Delete item from database

    Keyword arguments:
    course_id -- the id of the course from the database that the recipe is being deleted from
    recipe_id -- the id of the recipe from the database for the recipe that is being deleted
     """
    session = DBSESSION()
    item_to_delete = session.query(Recipe).filter_by(id=recipe_id).one()

    if request.method == 'POST':
        session.delete(item_to_delete)
        flash('%s Deleted' % item_to_delete.name)
        session.commit()
        return redirect(url_for('course_menu', course_id=course_id))

    if get_user_id(login_session['email']) != item_to_delete.user_id:
        flash("You are not authorized to delete this recipe.")
        return redirect(url_for('course_menu', course_id=course_id))
    return render_template('deleterecipe.html', item=item_to_delete)


# Add favorites
@APP.route('/favorites/<int:user_id>/<int:recipe_id>/newfavorite', methods=['GET', 'POST'])
def new_favorite(user_id, recipe_id):
    """Save the recipe that is favorited to the database

    Keyword arguments:

    user_id -- the id of the valid user from the database who is adding the favorite
    recipe_id -- the id of the recipe that is being added to the favorite list
    """
    session = DBSESSION()
    recipe = session.query(Recipe).filter_by(id=recipe_id).one()
    user = session.query(User).filter_by(id=user_id).one()
    user.favorites.append(recipe)
    session.add(user)
    session.commit()
    return render_template('favorites.html', user=user, favorites=user.favorites)
    flash("New Favorite Added!")

# Favorites
@APP.route('/favorites')
def find_favorite():
    """Render template of all favorites for the logged in user"""
    user = get_user(login_session['email'])
    return render_template('favorites.html', user=user, favorites=user.favorites)


@APP.route('/favorites/<int:user_id>/<int:recipe_id>/delete', methods=['GET', 'POST'])
def delete_favorite(user_id, recipe_id):
    """Delete a selected favorite from the database

    Keyword arguments:

    user_id -- the id of the user from the database who is deleting a recipe from the favorite list
    recipe_id -- the id of the recipe that is being removed from the favorite list
    """
    session = DBSESSION()
    recipe = session.query(Recipe).filter_by(id=recipe_id).one()
    user = session.query(User).filter_by(id=user_id).one()
    user.favorites.remove(recipe)
    session.add(user)
    session.commit()
    return render_template('favorites.html', user=user, favorites=user.favorites)
    flash("New Favorite Added!")




if __name__ == '__main__':
    APP.secret_key = 'super_secret-key'
    APP.debug = True
    APP.run(host='0.0.0.0', port=5000)
