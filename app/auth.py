from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import db, User

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')  # Render the registration page

    username = request.form['username']
    password = request.form['password']
    hashed_password = generate_password_hash(password)

    # Check if the user already exists in the database
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({"message": "User already exists!"}), 400

    # Create a new user and add to the database
    new_user = User(username=username, password_hash=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('auth.login'))  # Redirect to the login page after registration

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')  # Render the login page

    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()

    # Check the password and log the user in if correct
    if user and check_password_hash(user.password_hash, password):
        session['user_id'] = user.id  # Save the user's id in the session
        return redirect(url_for('main.home'))  # Redirect to the home page after successful login
    return jsonify({"message": "Invalid credentials"}), 401