from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from itsdangerous import URLSafeTimedSerializer
from datetime import datetime
import re
import logging
from config import Config  # Import configuration from config.py
from quiz_data import quiz_questions  # Import quiz questions


app = Flask(__name__)
app.config.from_object(Config)  # Load configuration from config.py

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
mail = Mail(app)

# Initialize rate limiter
limiter = Limiter(
    app,
    key_func=get_remote_address
)

csrf = CSRFProtect(app)

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize token serializer for password reset
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    is_admin = db.Column(db.Boolean, default=False)
    scores = db.relationship('Score', backref='user', lazy=True)

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    score = db.Column(db.Integer)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    message = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)

# Load user for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Helper functions
def send_email(subject, recipient, template, **kwargs):
    msg = Message(subject, recipients=[recipient])
    msg.html = render_template(template, **kwargs)
    mail.send(msg)

def generate_token(email):
    return serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])

def verify_token(token, expiration=3600):
    try:
        email = serializer.loads(token, salt=app.config['SECURITY_PASSWORD_SALT'], max_age=expiration)
        return email
    except:
        return None

def calculate_score(user_answers):
    score = 0
    for q in quiz_questions:
        correct_answer = q['answer']
        user_answer = user_answers.get(q['question'])
        if user_answer == correct_answer:
            score += 1
    return score

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if request.method == 'POST':
        username_or_email = request.form['username_or_email']
        password = request.form['password']
        user = User.query.filter((User.username == username_or_email) | (User.email == username_or_email)).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            logger.info(f"User {user.username} logged in.")
            return redirect(url_for('quiz'))
        flash('Invalid username/email or password', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'error')
        elif User.query.filter_by(email=email).first():
            flash('Email already exists!', 'error')
        elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('Invalid email address', 'error')
        else:
            new_user = User(username=username, email=email, password=generate_password_hash(password))
            db.session.add(new_user)
            db.session.commit()
            send_email('Welcome to Quiz App', email, 'email_templates/welcome.html')
            flash('Registration successful! Please login.', 'success')
            logger.info(f"New user registered: {username}")
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('home'))

@app.route('/quiz', methods=['GET', 'POST'])
@login_required
def quiz():
    page = request.args.get('page', 1, type=int)
    per_page = 5
    start = (page - 1) * per_page
    end = start + per_page
    paginated_questions = quiz_questions[start:end]

    if request.method == 'POST':
        if 'user_answers' not in session:
            session['user_answers'] = {}
        for q in paginated_questions:
            user_answer = request.form.get(q['question'])
            if user_answer:  # Ensure we store only non-empty answers
                session['user_answers'][q['question']] = user_answer
        logger.info(f"User answers updated: {session['user_answers']}")

        if page >= (len(quiz_questions) // per_page) + 1:
            score = calculate_score(session['user_answers'])
            session['score'] = score
            new_score = Score(user_id=current_user.id, score=score)
            db.session.add(new_score)
            db.session.commit()
            logger.info(f"User {current_user.username} scored {score} points.")
            return redirect(url_for('results'))

    return render_template(
        'quiz.html', 
        questions=paginated_questions, 
        page=page, 
        total_pages=(len(quiz_questions) // per_page) + 1
    )

@app.route('/results')
@login_required
def results():
    score = session.get('score', 0)
    user_answers = session.get('user_answers', {})
    session.pop('score', None)
    session.pop('user_answers', None)
    return render_template('results.html', score=score, total=len(quiz_questions), admin_questions=quiz_questions, user_answers=user_answers)

@app.route('/leaderboard')
def leaderboard():
    scores = Score.query.order_by(Score.score.desc()).limit(10).all()
    return render_template('leaderboard.html', scores=scores)

@app.route('/profile')
@login_required
def profile():
    scores = Score.query.filter_by(user_id=current_user.id).order_by(Score.date.desc()).all()
    return render_template('profile.html', scores=scores)

@app.route('/feedback', methods=['GET', 'POST'])
@login_required
def feedback():
    if request.method == 'POST':
        message = request.form['message']
        new_feedback = Feedback(user_id=current_user.id, message=message)
        db.session.add(new_feedback)
        db.session.commit()
        flash('Thank you for your feedback!', 'success')
        logger.info(f"Feedback submitted by {current_user.username}.")
        return redirect(url_for('home'))
    return render_template('feedback.html')

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        return "Access Denied", 403
    users = User.query.all()
    return render_template('admin.html', users=users)

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            token = generate_token(user.email)
            reset_url = url_for('reset_password_token', token=token, _external=True)
            send_email('Password Reset', user.email, 'email_templates/reset_password.html', reset_url=reset_url)
            flash('Password reset link sent to your email.', 'info')
            return redirect(url_for('login'))
        else:
            flash('Email not found.', 'error')
    return render_template('reset_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password_token(token):
    email = verify_token(token)
    if not email:
        flash('Invalid or expired token.', 'error')
        return redirect(url_for('reset_password'))
    user = User.query.filter_by(email=email).first()
    if request.method == 'POST':
        new_password = request.form['new_password']
        user.password = generate_password_hash(new_password)
        db.session.commit()
        flash('Your password has been reset!', 'success')
        return redirect(url_for('login'))
    return render_template('reset_password_token.html', token=token)

# Run the application
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
