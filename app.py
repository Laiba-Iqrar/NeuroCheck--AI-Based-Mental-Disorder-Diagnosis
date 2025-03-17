# app.py
from flask import Flask, render_template,request,jsonify,redirect,url_for,flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin,login_user,login_required,logout_user,current_user
import pandas as pd
import joblib
import os
from werkzeug.security import generate_password_hash, check_password_hash
from retrain_model import retrain_with_new_data
from flask import request, jsonify
import os
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Ilikeyouverymuch'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100),nullable=False)
    email = db.Column(db.String(100),unique=True, nullable=False)
    password = db.Column(db.String(200),nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
try:
    model = joblib.load("model/trained_model.pkl")
    label_encoder = joblib.load("model/label_encoder.pkl")
except Exception as e:
    raise RuntimeError(f"Failed to load ML models: {str(e)}")

USER_DATA_FILE = "data/user_responses.csv"

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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password,password):
            login_user(user)
            return redirect(url_for('home'))
        flash('Invalid email or password','danger')
    return render_template('login.html')

@app.route('/signup',methods=['GET','POST'])
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
        
        new_user = User(name=name,email=email,password=generate_password_hash(password,method='pbkdf2:sha256',salt_length=8))
        
        try:
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'danger')
    
    return render_template('signup.html')

@app.route('/about')
def about():
    return render_template('about.html')



@app.route('/chat', methods=['POST'])
@login_required
def chat():
    try:
        data = request.get_json()
        user_message = data['message']
        print(f"\nReceived message: {user_message}")

        API_URL= "https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill"
        headers= {"Authorization": f"Bearer {os.getenv('HUGGINGFACE_API_KEY')}"}
        
        payload = {
            "inputs": user_message,
            "parameters": {
                "max_length": 200,
                "temperature": 0.7
            }
        }
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.text}")
        if response.status_code == 503:
            retry_after = response.json().get('estimated_time', 30)
            print(f"Model loading, waiting {retry_after} seconds...")
            time.sleep(retry_after)
            response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()    
        result = response.json()
        return jsonify({'response': result[0]['generated_text']})
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500 

@app.route('/seek-help')
@login_required
def seek_help():
    return render_template('seek_help.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/') #application route
@login_required
def home():
    return render_template('index.html',symptoms=symptoms)

@app.route('/predict',methods=['POST'])
@login_required
def predict():
    try:
        user_input = request.form.to_dict()
        input_df = pd.DataFrame([user_input])
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