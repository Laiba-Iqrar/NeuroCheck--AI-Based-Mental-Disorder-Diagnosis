import pandas as pd
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

# Check for missing values and handle them
data.fillna(data.mode().iloc[0], inplace=True)  # Fill NaN values with the mode for categorical data

# Encoding categorical columns
for col in data.columns:
    if data[col].dtype == 'object':
        if data[col].str.contains('From').any():  # For columns with "From 10" format
            data[col] = data[col].str.extract('(\d+)').astype(int)  # Extract integer part
        elif col != 'Expert Diagnose':  # Skip target column for encoding
            data[col] = LabelEncoder().fit_transform(data[col])

# Continue with feature-target definition, normalization, and model training as before
X = data.drop(columns=['Expert Diagnose'])
y = data['Expert Diagnose']

# Normalize the feature data
scaler = MinMaxScaler()
X_normalized = scaler.fit_transform(X)

# Split the data
X_train, X_test, y_train, y_test = train_test_split(X_normalized, y, test_size=0.2, random_state=42)

# Train the model
model = RandomForestClassifier(random_state=42)
model.fit(X_train, y_train)

# Predict and evaluate
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"Model Accuracy: {accuracy:.2f}")

# Save the model and scaler
joblib.dump(model, 'mental_disorder_classifier.pkl')
joblib.dump(scaler, 'scaler.pkl')


# Function to get prediction based on user input symptoms
def predict_disorder(symptom_data):
    # Convert input into DataFrame for easier processing
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

    # Predict using the loaded model
    prediction = model.predict(input_normalized)
    return prediction[0]

# Function to save new input/output to CSV for optimization
def save_new_data(symptom_data, diagnosis):
    # Append new data with prediction for incremental learning
    new_data = symptom_data.copy()
    new_data['Expert Diagnose'] = diagnosis
    df_new = pd.DataFrame([new_data])
    df_new.to_csv(file_path, mode='a', header=False, index=False)

# Example: Interactive input for symptoms
def interactive_prediction():
    symptom_data = {}
    for col in X.columns:
        symptom_data[col] = input(f"Enter value for {col}: ")
    
    diagnosis = predict_disorder(symptom_data)
    print(f"Predicted Diagnosis: {diagnosis}")

    # Save for model optimization
    save_new_data(symptom_data, diagnosis)

# Interactive prediction loop
interactive_prediction()
