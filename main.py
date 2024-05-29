from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SubmitField, FileField
from wtforms.validators import DataRequired, Email
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail, Message
import secrets
import os


# Initialize Flask app
app = Flask(__name__)
app.secret_key = "sachinshahvisiotrack"

# Configure CSRF protection
csrf = CSRFProtect(app)

# Initialize Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = '123nihcas@gmail.com'
app.config['MAIL_PASSWORD'] = 'ouxp nexs ttjp eulh'
app.config['MAIL_DEFAULT_SENDER'] = '123nihcas@gmail.com'
mail = Mail(app)


# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blogpost.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    mobile_number = db.Column(db.String(20), nullable=False)
    image = db.Column(db.String(200), nullable=True)
    posts = db.relationship('BlogPost', backref='author', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

# BlogPost model
class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<BlogPost {self.title}>'

# User loader function
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize database and create table if not exists
def init_db():
    with app.app_context():
        db.create_all()

# Forms
class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    mobile_number = StringField('Mobile Number', validators=[DataRequired()])
    profile_photo = FileField('Profile Photo')
    submit = SubmitField('Update Profile')
    
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    mobile_number = StringField('Mobile Number', validators=[DataRequired()])
    profile_photo = FileField('Profile Photo')
    submit = SubmitField('Register')

class BlogPostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Post Blog')
    
class ContactForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Send Message')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('User logged in')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password')
    return render_template('login.html', form=form)

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        mobile_number = form.mobile_number.data
        profile_photo = form.profile_photo.data

        hashed_password = generate_password_hash(password)
        
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            if existing_user.username == username:
                flash('Username already exists')
            elif existing_user.email == email:
                flash('Email already exists')
            return redirect(url_for('register'))

        profile_photo_path = None
        if profile_photo:
            base_dir = os.path.dirname(__file__)
            profile_photo_dir = os.path.join(base_dir, 'static/profile_photos')
            os.makedirs(profile_photo_dir, exist_ok=True)
            profile_photo_path = os.path.join(profile_photo_dir, profile_photo.filename)
            profile_photo.save(profile_photo_path)
            profile_photo_path = os.path.join('static/profile_photos', profile_photo.filename)

        new_user = User(username=username, password=hashed_password, email=email, mobile_number=mobile_number, image=profile_photo_path)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


# Profile route
@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

# Edit profile route
@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.mobile_number = form.mobile_number.data
        if form.profile_photo.data:
            profile_photo = form.profile_photo.data
            base_dir = os.path.dirname(__file__)
            profile_photo_dir = os.path.join(base_dir, 'static/profile_photos')
            os.makedirs(profile_photo_dir, exist_ok=True)
            profile_photo_path = os.path.join(profile_photo_dir, profile_photo.filename)
            profile_photo.save(profile_photo_path)
            profile_photo_path = os.path.join('static/profile_photos', profile_photo.filename)
            current_user.image = profile_photo_path
        db.session.commit()
        flash('Profile updated successfully')
        return redirect(url_for('profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.mobile_number.data = current_user.mobile_number
    return render_template('edit_profile.html', form=form, user=current_user)

@app.route('/')
def home():
    query = request.args.get('query')
    if query:
        posts = BlogPost.query.join(User).filter(
            (BlogPost.title.contains(query)) | 
            (BlogPost.content.contains(query)) | 
            (User.username.contains(query))
        ).all()
    else:
        posts = BlogPost.query.all()
    return render_template('index.html', posts=posts)


#contact page route
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        message_body = form.message.data
        message = Message(subject=f"New message from {name}",
                          sender=app.config['MAIL_DEFAULT_SENDER'],
                          recipients=[app.config['MAIL_USERNAME']],
                          body=f"From: {name} <{email}>\n\n{message_body}")
        mail.send(message)
        flash('Message sent successfully')
        return redirect(url_for('contact'))
    return render_template('contact.html', form=form)


# New post route
@app.route('/new_post')
@login_required
def new_post():
    form = BlogPostForm()
    return render_template('new_post.html', form=form)

# Create a new blog post route
@app.route('/create_post', methods=['POST'])
@login_required
def create_post():
    form = BlogPostForm()
    if form.validate_on_submit():
        new_post = BlogPost(title=form.title.data, content=form.content.data, user_id=current_user.id)
        db.session.add(new_post)
        db.session.commit()
        flash('Post created successfully')
        return redirect(url_for('home'))
    return render_template('new_post.html', form=form)

# Edit post route
@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    if post.author != current_user:
        flash('You do not have permission to edit this post')
        return redirect(url_for('profile'))
    form = BlogPostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Post updated successfully')
        return redirect(url_for('profile'))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('edit_post.html', form=form)

# Delete post route
@app.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    if post.author != current_user:
        flash('You do not have permission to delete this post')
        return redirect(url_for('profile'))
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted successfully')
    return redirect(url_for('profile'))

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route('/about')
def about():
    return render_template('about.html')

# Run the app
if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)
