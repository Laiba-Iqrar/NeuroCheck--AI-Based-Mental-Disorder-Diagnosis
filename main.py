# main.py

from src.load_data import load_data
from src.preprocess import preprocess_data, encode_labels
from src.train_model import train_and_save_model
from sklearn.model_selection import train_test_split

def main():
    data = load_data("data/mds.csv")
    data = data.drop(columns=['Patient Number'], errors='ignore')
    X = data.drop(columns=['Expert Diagnose'])
    y = data['Expert Diagnose']
    
    X = preprocess_data(X)
    y, label_encoder = encode_labels(y)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    train_and_save_model(X_train, y_train, label_encoder)

if __name__ == "__main__":
    main()
