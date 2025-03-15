# app.py
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import pandas as pd
import joblib
import os
from werkzeug.security import generate_password_hash, check_password_hash
from retrain_model import retrain_with_new_data

# Initialize Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Replace with a real secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable modification tracking

# Initialize database
db = SQLAlchemy(app)

# Configure Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Load ML components
try:
    model = joblib.load("model/trained_model.pkl")
    label_encoder = joblib.load("model/label_encoder.pkl")
except Exception as e:
    raise RuntimeError(f"Failed to load ML models: {str(e)}")

USER_DATA_FILE = "data/user_responses.csv"

# Symptoms configuration
symptoms = {
    "Sadness": {"type": "ordinal"},
    "Euphoric": {"type": "ordinal"},
    "Exhausted": {"type": "ordinal"},
    "Sleep dissorder": {"type": "ordinal"},
    "Mood Swing": {"type": "binary"},
    "Suicidal thoughts": {"type": "binary"},
    "Anorxia": {"type": "binary"},
    "Authority Respect": {"type": "binary"},
    "Try-Explanation": {"type": "binary"},
    "Aggressive Response": {"type": "binary"},
    "Ignore & Move-On": {"type": "binary"},
    "Nervous Break-down": {"type": "binary"},
    "Admit Mistakes": {"type": "binary"},
    "Overthinking": {"type": "binary"},
    "Sexual Activity": {"type": "numerical"},
    "Concentration": {"type": "numerical"},
    "Optimisim": {"type": "numerical"},
}

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('home'))
        flash('Invalid email or password', 'danger')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return redirect(url_for('signup'))
        
        new_user = User(
            name=name,
            email=email,
            password=generate_password_hash(
                password, 
                method='pbkdf2:sha256',  # Correct method name
                salt_length=8
            )
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'danger')
    
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Application routes
@app.route('/')
@login_required
def home():
    return render_template('index.html', symptoms=symptoms)

@app.route('/predict', methods=['POST'])
@login_required
def predict():
    try:
        user_input = request.form.to_dict()
        input_df = pd.DataFrame([user_input])
        
        # Validate input data
        if not all(key in symptoms for key in user_input.keys()):
            return jsonify({"error": "Invalid input data"}), 400
            
        prediction = model.predict(input_df)
        input_df['Diagnosis'] = prediction
        save_user_response(input_df)
        
        return jsonify({
            "diagnosis": prediction.tolist(),
            "message": "Prediction successful"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def save_user_response(data):
    try:
        header = not os.path.exists(USER_DATA_FILE)
        data.to_csv(USER_DATA_FILE, mode='a', header=header, index=False)
    except Exception as e:
        app.logger.error(f"Failed to save user response: {str(e)}")

@app.route('/retrain', methods=['POST'])
@login_required
def retrain():
    try:
        retrain_with_new_data()
        global model, label_encoder
        model = joblib.load("model/trained_model.pkl")
        label_encoder = joblib.load("model/label_encoder.pkl")
        return jsonify({"status": "Model retrained successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)