# Imports
import json
import random
import string
import httplib2
from flask import (Flask, flash, jsonify, make_response, redirect,
                   render_template, request)
from oauth2client.client import FlowExchangeError, flow_from_clientsecrets
from flask import session as login_session
from flask import url_for
import requests
from database_setup import Base, Course, Recipe, User
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker


# Database Binding
app = Flask(__name__)
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Recipe Application"

engine = create_engine('sqlite:///recipecollection.db')

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Anti-forgery state token
@app.route('/login')
def showLogin():
    print 'done'
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

# Google Connect
@app.route('/gconnect', methods=['POST'])
def gconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    request.get_data()
    code = request.data.decode('utf-8')
    try:
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    response = h.request(url, 'GET')[1]
    str_response = response.decode('utf-8')
    result = json.loads(str_response)
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    login_session['access_token'] = access_token
    login_session['gplus_id'] = gplus_id
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = answer.json()
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id
    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    return output

# Random Functions
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id
def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user
def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# Google Disconnect
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# App Home
@app.route('/')
def appHome():
    session = DBSession()
    courses = session.query(Course).all()
    if 'username' not in login_session:
        return render_template('home.html', courses=courses)
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
        newItem = Recipe(name=request.form.get('name'), total_time=request.form.get('total_time'), prep_time=request.form.get('prep_time'), cook_time=request.form.get('cook_time'), difficulty=request.form.get('difficulty'), directions=request.form.get('directions'), ingredients=request.form.get('ingredients'), output=request.form.get('output'), image=request.form.get('image'), course_id=course_id)
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
