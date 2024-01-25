import os

from flask import Flask, render_template,request, flash, redirect, session,abort,g
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from flask_bcrypt import Bcrypt
from flask_login import current_user

from forms import UserAddForm, LoginForm, MessageForm,UserEditForm
from models import db, connect_db, User, Message,Likes

CURR_USER_KEY = "curr_user"
bcrypt = Bcrypt()
app = Flask(__name__)

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql:///warbler'))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
toolbar = DebugToolbarExtension(app)

connect_db(app)


##############################################################################
# User signup/login/logout


@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        id = session[CURR_USER_KEY]
        g.user = User.query.get(id)

    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]
        
    return redirect("/login")


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return redirect('/login')


@app.route('/logout')
def logout():
    """Handle logout of user."""
    user_id = session[CURR_USER_KEY]
    user = User.query.get(user_id)
    do_logout()
    flash("You are successfuly logged out!")
    return redirect("/login")
    # IMPLEMENT THIS


##############################################################################
# General user routes:

@app.route('/users')
def list_users():
    """Page with listing of users.

    Can take a 'q' param in querystring to search by that username.
    """

    search = request.args.get('q')

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()

    return render_template('users/index.html', users=users)



@app.route('/users/<int:user_id>')
def users_show(user_id):
    """Show user profile."""


    if CURR_USER_KEY in session:
        user_id = session[CURR_USER_KEY]
        user = User.query.get_or_404(user_id)
   
    # snagging messages in order from the database;
    # user.messages won't be in order by default
        messages = (Message
                .query
                .filter(Message.user_id == user_id)
                .order_by(Message.timestamp.desc())
                .limit(100)
                .all())
    
        message_ids = [m.id for m in messages]
        
        likes = Likes.query.filter(Likes.user_id == g.user.id, Likes.message_id.in_(message_ids)).all()
    
        return render_template('users/show.html', user=user, messages=messages,likes=likes)
    return redirect("/login")



@app.route('/users/<int:user_id>/following')
def show_following(user_id):
    """Show list of people this user is following."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/following.html', user=user)



@app.route('/users/<int:user_id>/followers')
def users_followers(user_id):
    """Show list of followers of this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/followers.html', user=user)



@app.route('/users/follow/<int:follow_id>', methods=['POST'])
def add_follow(follow_id):
    """Add a follow for the currently-logged-in user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get_or_404(follow_id)
    g.user.following.append(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")



@app.route('/users/stop-following/<int:follow_id>', methods=['POST'])
def stop_following(follow_id):
    """Have currently-logged-in-user stop following this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get(follow_id)
    g.user.following.remove(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")



@app.route('/users/profile', methods=["GET", "POST"])
def profile():
    """Update profile for current user."""
    

    if CURR_USER_KEY in session:
        user_id = session[CURR_USER_KEY]
        user = User.query.get(user_id)
        form = UserEditForm(obj=user) if request.method == 'GET' else UserEditForm()
        

        if form.validate_on_submit():
            password = form.password.data
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                user.username = form.username.data 
                user.email = form.email.data
                user.image_url = form.image_url.data
                user.header_image_url = form.header_image_url.data
                user.bio = form.bio.data

                db.session.add(user)
                db.session.commit()
                return redirect(f'/users/{user.id}')
        
        return render_template("/users/edit.html", form=form, user=user)
            
    else:
        return redirect('/login')
  
  
  
@app.route('/users/likes', methods=["GET"])
def show_all_likes():
    """Show all the messages with likes"""
    likedMessage_ids =[]
    messages = []
    
    if g.user:
       allLikes = Likes.query.filter(Likes.user_id == g.user.id).all()
       likedMessage_ids.extend(l.message_id for l in allLikes)     
       
       for like_id in likedMessage_ids:
            message = Message.query.filter_by(id=like_id).first()
            if message:
                messages.append(message)
            
       
       return render_template("/users/show-liked-message.html",messages=messages)
   
    return redirect("/login")
        
        
    
    

@app.route('/users/<int:user_id>/delete', methods=["POST"])
def delete_user(user_id):
    """Delete user."""

    if not g.user.id == user_id:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    do_logout()

    db.session.delete(g.user)
    db.session.commit()

    return redirect("/signup")


##############################################################################
# Messages routes:

@app.route('/messages/new', methods=["GET", "POST"])
def messages_add():
    """Add a message:

    Show form if GET. If valid, update message and redirect to user page.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = MessageForm()

    if form.validate_on_submit():
        msg = Message(text=form.text.data)
        g.user.messages.append(msg)
        db.session.commit()

        return redirect(f"/users/{g.user.id}")

    return render_template('messages/new.html', form=form)



@app.route('/messages/<int:message_id>', methods=["GET"])
def messages_show(message_id):
    """Show a message."""
    if CURR_USER_KEY in session:
        msg = Message.query.get(message_id)
        return render_template('messages/show.html', message=msg)

    return redirect("/login")


@app.route('/messages/<int:message_id>/delete', methods=["POST"])
def messages_destroy(message_id):
    """Delete a message."""

    message = Message.query.get_or_404(message_id)

    # Check if the current user has permission to delete the message
    if session[CURR_USER_KEY] != message.user_id:
        abort(403)  
        
    db.session.delete(message)
    db.session.commit()

    return redirect(f"/users/{message.user_id}")



@app.route('/users/add_like/<int:msg_id>', methods=["POST"])
def handle_like(msg_id):
    
    if CURR_USER_KEY in session:
        user_id = session[CURR_USER_KEY]
        existing_like = Likes.query.filter(Likes.user_id == user_id).filter(Likes.message_id == msg_id).first()
        if not existing_like:
            new_like = Likes(user_id = user_id, message_id = msg_id)
            db.session.add(new_like)
        else:
            db.session.delete(existing_like)
        db.session.commit()
        return redirect("/")
    return redirect("/login")
        
##############################################################################
# Homepage and error pages


@app.route('/')
def homepage():
    """Show homepage:

    - anon users: no messages
    - logged in: 100 most recent messages of followed_users
    """
    messages = []
    if g.user:
        following_users = g.user.following
        for u in following_users:
            messages.extend(u.messages)
            
        messages=messages[:100]
        message_ids = [m.id for m in messages]
        
        allLikes = Likes.query.filter(Likes.user_id == g.user.id).all()
        likes = Likes.query.filter(Likes.user_id == g.user.id, Likes.message_id.in_(message_ids)).all()
            

        return render_template('home.html', messages=messages, likes=likes, allLikes=allLikes)

    else:
        return render_template('home-anon.html')


##############################################################################
# Turn off all caching in Flask
#   (useful for dev; in production, this kind of stuff is typically
#   handled elsewhere)
#
# https://stackoverflow.com/questions/34066804/disabling-caching-in-flask

@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""

    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    return req
