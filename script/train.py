import torch
import torch.nn as nn
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from torch.utils.data import DataLoader, TensorDataset
import joblib
import os

class StackedLSTM(nn.Module):
    def __init__(self, input_dim, hidden_dim=128, num_layers=2):
        super(StackedLSTM, self).__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers=num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_dim, 1)

    def forward(self, x):
        out, _ = self.lstm(x)
        return self.fc(out[:, -1, :])

def train():
    X_train = np.load('../data/X_train.npy')
    y_train = np.load('../data/y_train.npy')
    X_val = np.load('../data/X_val.npy')
    y_val = np.load('../data/y_val.npy')
    X_test = np.load('../data/X_test.npy')
    y_test = np.load('../data/y_test.npy')
    target_scaler = joblib.load('../data/target_scaler.pkl')

    X_train = torch.tensor(X_train, dtype=torch.float32)
    y_train = torch.tensor(y_train, dtype=torch.float32).unsqueeze(1)
    X_val = torch.tensor(X_val, dtype=torch.float32)
    y_val = torch.tensor(y_val, dtype=torch.float32).unsqueeze(1)
    X_test = torch.tensor(X_test, dtype=torch.float32)
    y_test = torch.tensor(y_test, dtype=torch.float32).unsqueeze(1)

    train_loader = DataLoader(TensorDataset(X_train, y_train), batch_size=32, shuffle=True)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = StackedLSTM(input_dim=X_train.shape[2]).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.MSELoss()

    best_val_loss = float('inf')
    patience = 10
    counter = 0

    for epoch in range(100):
        model.train()
        total_loss = 0
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad()
            pred = model(xb)
            loss = criterion(pred, yb)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        avg_train_loss = total_loss / len(train_loader)

        model.eval()
        with torch.no_grad():
            val_pred = model(X_val.to(device)).cpu()
            val_loss = criterion(val_pred, y_val).item()

        print(f"Epoch {epoch+1:03d} | Train Loss: {avg_train_loss:.6f} | Val Loss: {val_loss:.6f}")

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), '../models/best_lstm.pth')
            counter = 0
        else:
            counter += 1
            if counter >= patience:
                print("Early stopping triggered.")
                break

    model.load_state_dict(torch.load('../models/best_lstm.pth'))
    model.eval()
    with torch.no_grad():
        preds = model(X_test.to(device)).cpu().numpy()
        y_true = y_test.numpy()
        pred_denorm = target_scaler.inverse_transform(preds)
        y_true_denorm = target_scaler.inverse_transform(y_true)

        mse = mean_squared_error(y_true_denorm, pred_denorm)
        mae = mean_absolute_error(y_true_denorm, pred_denorm)
        r2 = r2_score(y_true_denorm, pred_denorm)

        print("\n=== Evaluation ===")
        print(f"MSE  = {mse:.2f}")
        print(f"MAE  = {mae:.2f}")
        print(f"R²   = {r2:.4f}")

if __name__ == '__main__':
    os.makedirs('../models', exist_ok=True)
    train()