import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import os
import joblib

def create_sequences(data_X, data_y, seq_length=60):
    X, y = [], []
    for i in range(seq_length, len(data_X)):
        X.append(data_X[i - seq_length:i])
        y.append(data_y[i])
    return np.array(X), np.array(y)

def preprocess(file_path='../data/latest_data.csv', seq_length=60, save=True):
    df = pd.read_csv(file_path)
    df = df[['Close', 'Volume']]
    df['Close_t-1'] = df['Close'].shift(1)
    df['Volume_t-1'] = df['Volume'].shift(1)
    df['Close_target'] = df['Close'].shift(-1)
    df.dropna(inplace=True)

    features = df[['Close', 'Volume', 'Close_t-1', 'Volume_t-1']].values
    targets = df['Close_target'].values.reshape(-1, 1)

    feature_scaler = MinMaxScaler()
    target_scaler = MinMaxScaler()

    features_scaled = feature_scaler.fit_transform(features)
    targets_scaled = target_scaler.fit_transform(targets).flatten()

    split1 = int(len(features_scaled) * 0.7)
    split2 = int(len(features_scaled) * 0.8)

    X_train_raw = features_scaled[:split1]
    y_train_raw = targets_scaled[:split1]
    X_val_raw = features_scaled[split1:split2]
    y_val_raw = targets_scaled[split1:split2]
    X_test_raw = features_scaled[split2:]
    y_test_raw = targets_scaled[split2:]

    X_train, y_train = create_sequences(X_train_raw, y_train_raw, seq_length)
    X_val, y_val = create_sequences(X_val_raw, y_val_raw, seq_length)
    X_test, y_test = create_sequences(X_test_raw, y_test_raw, seq_length)

    if save:
        os.makedirs('../data', exist_ok=True)
        np.save('../data/X_train.npy', X_train)
        np.save('../data/y_train.npy', y_train)
        np.save('../data/X_val.npy', X_val)
        np.save('../data/y_val.npy', y_val)
        np.save('../data/X_test.npy', X_test)
        np.save('../data/y_test.npy', y_test)
        joblib.dump(feature_scaler, '../data/feature_scaler.pkl')
        joblib.dump(target_scaler, '../data/target_scaler.pkl')
        print("Preprocessed data saved.")

    return X_train, y_train, X_val, y_val, X_test, y_test, feature_scaler, target_scaler

if __name__ == '__main__':
    preprocess()
