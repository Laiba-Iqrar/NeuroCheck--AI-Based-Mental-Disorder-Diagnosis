import pandas as pd
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, MinMaxScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib
import os

# Load the dataset
file_path = 'Dataset-Mental-Disorders (1).csv'
data = pd.read_csv(file_path)

# Drop Patient Number column if present
if 'Patient Number' in data.columns:
    data.drop(columns=['Patient Number'], inplace=True)

# Fuzzy logic settings for symptoms with different levels
def setup_fuzzy_logic():
    # Define symptom input variables with fuzzy levels (Low, Medium, High)
    symptoms = {}
    for col in data.columns:
        if col != 'Expert Diagnose':
            symptoms[col] = ctrl.Antecedent(np.arange(0, 11, 1), col)
            symptoms[col]['Low'] = fuzz.trimf(symptoms[col].universe, [0, 0, 5])
            symptoms[col]['Medium'] = fuzz.trimf(symptoms[col].universe, [3, 5, 7])
            symptoms[col]['High'] = fuzz.trimf(symptoms[col].universe, [5, 10, 10])

    # Define output variable for diagnosis
    diagnosis = ctrl.Consequent(np.arange(0, 11, 1), 'diagnosis')
    diagnosis['Low'] = fuzz.trimf(diagnosis.universe, [0, 0, 5])
    diagnosis['Medium'] = fuzz.trimf(diagnosis.universe, [3, 5, 7])
    diagnosis['High'] = fuzz.trimf(diagnosis.universe, [5, 10, 10])

    return symptoms, diagnosis

# Preprocess dataset
for col in data.columns:
    if data[col].dtype == 'object':
        if data[col].str.contains('From').any():  # For columns with "From 10" format
            data[col] = data[col].str.extract('(\d+)').astype(int)  # Extract integer part
        elif col != 'Expert Diagnose':  # Skip target column for encoding
            data[col] = LabelEncoder().fit_transform(data[col])

# Define features (X) and target (y)
X = data.drop(columns=['Expert Diagnose'])
y = data['Expert Diagnose']

# Normalize the feature data
scaler = MinMaxScaler()
X_normalized = scaler.fit_transform(X)

# Train the model
def train_model():
    X_train, X_test, y_train, y_test = train_test_split(X_normalized, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier(random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    print(f"Model Accuracy: {accuracy_score(y_test, y_pred):.2f}")
    joblib.dump(model, 'mental_disorder_classifier.pkl')
    joblib.dump(scaler, 'scaler.pkl')

# Perform initial training
train_model()

# Fuzzy membership calculation function
def fuzzy_symptom_evaluation(symptoms, symptom_data):
    results = {}
    for col, value in symptom_data.items():
        # Fuzzify each input value
        level_low = fuzz.interp_membership(symptoms[col].universe, symptoms[col]['Low'].mf, value)
        level_medium = fuzz.interp_membership(symptoms[col].universe, symptoms[col]['Medium'].mf, value)
        level_high = fuzz.interp_membership(symptoms[col].universe, symptoms[col]['High'].mf, value)
        results[col] = {'Low': level_low, 'Medium': level_medium, 'High': level_high}
    return results

# Function to take input with options
def get_symptom_input(symptoms):
    symptom_data = {}
    for symptom in symptoms:
        while True:
            try:
                print(f"Enter severity for {symptom} (choose 'Low', 'Medium', or 'High'):")
                level = input(f"{symptom} severity: ").strip().capitalize()
                if level == 'Low':
                    symptom_data[symptom] = 2
                elif level == 'Medium':
                    symptom_data[symptom] = 5
                elif level == 'High':
                    symptom_data[symptom] = 8
                else:
                    print("Invalid input. Please choose from 'Low', 'Medium', or 'High'.")
                    continue
                break
            except ValueError:
                print("Invalid input. Please enter a valid severity level.")
    return symptom_data

# Function to predict disorder with fuzzy inputs
def predict_disorder(symptom_data):
    input_df = pd.DataFrame([symptom_data])

    # Apply the same encoding to input data
    for col in input_df.columns:
        if col in X.columns and input_df[col].dtype == 'object':
            if 'From' in str(input_df[col].values[0]):
                input_df[col] = int(input_df[col].str.extract('(\d+)').values[0])
            else:
                input_df[col] = LabelEncoder().fit(X[col]).transform(input_df[col])

    # Normalize the input using the same scaler
    input_normalized = scaler.transform(input_df)

    # Load model and predict
    model = joblib.load('mental_disorder_classifier.pkl')
    prediction = model.predict(input_normalized)
    return prediction[0]

# Save new data for periodic retraining
def save_new_data(symptom_data, diagnosis):
    new_data = symptom_data.copy()
    new_data['Expert Diagnose'] = diagnosis
    df_new = pd.DataFrame([new_data])
    df_new.to_csv(file_path, mode='a', header=False, index=False)

# Retrain the model periodically
def retrain_model():
    global data, X_normalized, X, y
    data = pd.read_csv(file_path)
    for col in data.columns:
        if data[col].dtype == 'object':
            if data[col].str.contains('From').any():
                data[col] = data[col].str.extract('(\d+)').astype(int)
            elif col != 'Expert Diagnose':
                data[col] = LabelEncoder().fit_transform(data[col])
    X = data.drop(columns=['Expert Diagnose'])
    y = data['Expert Diagnose']
    X_normalized = scaler.fit_transform(X)
    train_model()

# Interactive loop for user input, prediction, and retraining
symptoms, _ = setup_fuzzy_logic()
while True:
    symptom_data = get_symptom_input(symptoms)
    diagnosis = predict_disorder(symptom_data)
    print(f"Predicted Diagnosis: {diagnosis}")

    # Save new data for optimization
    save_new_data(symptom_data, diagnosis)
    
    # Periodically retrain the model with new data
    retrain_model()

    if input("Would you like to input another case? (yes/no): ").strip().lower() != 'yes':
        break
