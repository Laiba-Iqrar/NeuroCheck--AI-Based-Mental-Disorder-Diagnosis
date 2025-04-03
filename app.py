# app.py
from flask import Flask, render_template,request,jsonify,redirect,url_for,flash,session
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
from core.assessment.depression import DepressionAssessor
from core.safety.crisis import CrisisDetector
from utils.helpers import get_recommendations
import importlib
import sys

load_dotenv()
def reload_dependencies():
    """Force reload modules during development"""
    if app.debug:
        importlib.reload(sys.modules['core.assessment.depression'])
        globals()['DepressionAssessor'] = getattr(importlib.import_module('core.assessment.depression'), 'DepressionAssessor')


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
    reload_dependencies()  
    try:
        data = request.get_json()
        user_message = data['message']
        
        crisis_result = CrisisDetector().detect_crisis(user_message)
        if crisis_result['is_crisis']:
            session.pop('phq9', None)  # Clear any existing assessment
            return jsonify(crisis_result)

        if 'phq9' in session:
            try:
                assessor = DepressionAssessor(
                    score=session['phq9']['score'],
                    current_question=session['phq9']['current_question']
                )
                result = assessor.assess(user_message)
                
                if 'error' in result:
                    session.pop('phq9', None)  # Clear invalid session
                    return jsonify({
                        "error": result['error'],
                        "status": "error"
                    })

                if result.get('status') == 'continue':
                    session['phq9'] = {
                        'score': assessor.score,
                        'current_question': assessor.current_question
                    }
                    return jsonify({
                        "response": result['question'],
                        "options": [{"text": opt["text"], "score": opt["score"]} 
                                  for opt in assessor.questions[assessor.current_question]["options"]],
                        "status": "assessment_continue"
                    })
                
                # Assessment complete
                session.pop('phq9', None)
                return jsonify({
                    "response": "Assessment complete",
                    "diagnosis": result['diagnosis'],
                    "recommendations": get_recommendations(result['diagnosis']),
                    "status": "complete"
                })

            except ValueError:
                session.pop('phq9', None)
                return jsonify({
                    "error": "Invalid assessment session. Please start over.",
                    "status": "error"
                })

        # Check for depression keywords
        depression_keywords = ['depress', 'sad', 'hopeless', 'miserable']
        if any(key in user_message.lower() for key in depression_keywords):
            assessor = DepressionAssessor()
            session['phq9'] = {
                'score': assessor.score,
                'current_question': assessor.current_question
            }
            return jsonify({
                "response": assessor.questions[0]["text"],
                "options": [{"text": opt["text"], "score": opt["score"]} 
                          for opt in assessor.questions[0]["options"]],
                "status": "assessment_start"
            })


        # Replace BlenderBot with Gemma
        API_URL = "https://api-inference.huggingface.co/models/google/gemma-3.1b-it"
        headers = {"Authorization": f"Bearer {os.getenv('HUGGINGFACE_API_KEY')}"}
        
        try:
            # Updated payload with generation parameters
            payload = {
                "inputs": user_message,
                "parameters": {
                    "max_new_tokens": 512,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "repetition_penalty": 1.1
                }
            }
            
            response = requests.post(
                API_URL,
                headers=headers,
                json=payload,
                timeout=60
            )
           

            
            if response.status_code == 200:
                # Handle Gemma's response format
                response_data = response.json()
                
                # Gemma typically returns a list of generated texts
                if isinstance(response_data, list):
                    bot_response = response_data[0].get('generated_text', "Could you  rephrase that?")
                else:
                    bot_response = response_data.get('generated_text', "Could you  rephrase that?")
                
                # Clean up any special tokens
                bot_response = bot_response.replace("<start_of_turn>", "").replace("<end_of_turn>", "")
                
                # Add basic conversation handling
                if user_message.lower() in ['hi', 'hello', 'hey']:
                    bot_response = "Hello! How can I support you today?"
                    
                return jsonify({'response': bot_response})
            
            # Handle model loading time
            if response.status_code == 503:
                return jsonify({
                    'response': "I'm still getting ready. Please give me a moment!",
                    'status': 'retry'
                })
            
            return jsonify({
                'response': "I'm having trouble processing that. Could you rephrase?",
                'error': f"API Error: {response.status_code}"
            })

        except requests.Timeout:
            return jsonify({
                'response': "I'm taking longer than usual to respond. Please try again.",
                'error': 'API Timeout'
            })


    except Exception as e:
        app.logger.error(f"Chat error: {str(e)}")
        return jsonify({
            'response': "Something went wrong. Please try again.",
            'error': str(e)
        }), 500   
    
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
# app.py - Update main block
if __name__ == '__main__':
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    with app.app_context():
        db.create_all()
    app.run(debug=True, extra_files=['core/assessment/depression.py'])