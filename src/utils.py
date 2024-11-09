# src/utils.py

def get_ordinal_encoding_columns():
    return ['Sadness', 'Euphoric', 'Exhausted', 'Sleep dissorder']

def get_binary_encoding_columns():
    return [
        'Mood Swing', 'Suicidal thoughts', 'Anorxia', 'Authority Respect',
        'Try-Explanation', 'Aggressive Response', 'Ignore & Move-On',
        'Nervous Break-down', 'Admit Mistakes', 'Overthinking'
    ]

def extract_numerical_part(column):
    return column.str.extract('(\d+)').astype(float)
