# src/preprocess.py

import pandas as pd
from sklearn.preprocessing import OrdinalEncoder, LabelEncoder
from sklearn.impute import SimpleImputer
from src.utils import get_binary_encoding_columns, get_ordinal_encoding_columns, extract_numerical_part

def preprocess_data(data):
    ordinal_columns = get_ordinal_encoding_columns()
    binary_columns = get_binary_encoding_columns()
    
    # Ensure all expected columns exist
    for col in ordinal_columns + binary_columns + ['Sexual Activity', 'Concentration', 'Optimisim']:
        if col not in data.columns:
            data[col] = pd.NA
    
    # Ordinal Encoding
    ordinal_order = [['Seldom', 'Sometimes', 'Usually', 'Most-Often']]
    ordinal_encoder = OrdinalEncoder(categories=ordinal_order * len(ordinal_columns))
    data[ordinal_columns] = ordinal_encoder.fit_transform(data[ordinal_columns])
    
    # Binary Encoding
    for col in binary_columns:
        data[col] = data[col].map({'YES': 1, 'NO': 0})
    
    # Normalize numerical columns
    for col in ['Sexual Activity', 'Concentration', 'Optimisim']:
        data[col] = extract_numerical_part(data[col]) / 10

    # Imputation for missing values
    imputer = SimpleImputer(strategy='mean')
    data = pd.DataFrame(imputer.fit_transform(data), columns=data.columns)
    
    return data

def encode_labels(labels):
    label_encoder = LabelEncoder()
    encoded_labels = label_encoder.fit_transform(labels)
    return encoded_labels, label_encoder
