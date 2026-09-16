import sys
import os
import argparse
import time
import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.stats import pearsonr

# Setup path for relative imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.tcn_velocity import TCNVelocityModel
from models.losses import VelocityLoss
from models.dataset import VelocityDataset, extract_windows, compute_normalization

def create_synthetic_data(num_samples: int = 5000) -> pd.DataFrame:
    """Generate synthetic IMU and speed data if real data isn't available."""
    np.random.seed(42)
    t = np.linspace(0, 100, num_samples)
    
    # Synthetic speed (true)
    speed = np.abs(np.sin(t/5) * 10 + np.random.normal(0, 0.5, num_samples))
    
    # Synthetic IMU loosely correlated with speed
    accel_x = np.gradient(speed) + np.random.normal(0, 0.2, num_samples)
    
    df = pd.DataFrame({
        'accel_x': accel_x,
        'accel_y': np.random.normal(0, 1, num_samples),
        'accel_z': np.random.normal(9.81, 0.1, num_samples),
        'gyro_x': np.random.normal(0, 0.1, num_samples),
        'gyro_y': np.random.normal(0, 0.1, num_samples),
        'gyro_z': np.random.normal(0, 0.5, num_samples),
        'gps_speed': speed
    })
    return df

def train(config: argparse.Namespace):
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Setup device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    # Load or generate data
    data_dir = Path(config.data_dir)
    if data_dir.exists():
        print(f"Loading data from {data_dir}...")
        # Note: Replace this with actual IO-VNBD loading logic if needed.
        # Here we just fallback to synthetic to keep it running smoothly
        # df = parser.load_some_data(data_dir)
        # For now, if there's no actual parser imported, just mock:
        print("Using synthetic data for demo as IO-VNBD parser is not fully specified.")
        df = create_synthetic_data()
    else:
        print(f"Data directory {data_dir} not found. Using synthetic data.")
        df = create_synthetic_data()
        
    print(f"Data shape: {df.shape}")
    
    # Extract windows
    windows_labels = extract_windows(df, window_size=config.window_size, stride=config.stride)
    
    # Train/Val/Test Split
    total_samples = len(windows_labels)
    train_size = int(0.7 * total_samples)
    val_size = int(0.15 * total_samples)
    
    train_data = windows_labels[:train_size]
    val_data = windows_labels[train_size:train_size+val_size]
    test_data = windows_labels[train_size+val_size:]
    
    train_windows, train_labels = zip(*train_data)
    val_windows, val_labels = zip(*val_data)
    test_windows, test_labels = zip(*test_data)
    
    # Normalize using train stats
    mean, std = compute_normalization(list(train_windows))
    
    train_dataset = VelocityDataset(list(train_windows), list(train_labels), mean, std)
    val_dataset = VelocityDataset(list(val_windows), list(val_labels), mean, std)
    test_dataset = VelocityDataset(list(test_windows), list(test_labels), mean, std)
    
    train_loader = DataLoader(train_dataset, batch_size=config.batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=config.batch_size, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=config.batch_size, shuffle=False)
    
    # Model
    model = TCNVelocityModel().to(device)
    print(f"Model parameters: {model.count_parameters()}")
    
    criterion = VelocityLoss(physics_weight=0.1, smooth_weight=0.01)
    optimizer = torch.optim.AdamW(model.parameters(), lr=config.lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=config.epochs)
    
    # Training Loop
    best_val_loss = float('inf')
    train_losses = []
    val_losses = []
    
    print("Starting training...")
    for epoch in range(config.epochs):
        model.train()
        epoch_train_loss = 0.0
        
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            
            optimizer.zero_grad()
            y_pred = model(x)
            
            # Simple loss call without accel_x for simplicity in this script
            loss, _ = criterion(y_pred, y)
            
            loss.backward()
            optimizer.step()
            
            epoch_train_loss += loss.item() * x.size(0)
            
        scheduler.step()
        
        epoch_train_loss /= len(train_dataset)
        train_losses.append(epoch_train_loss)
        
        # Validation
        model.eval()
        epoch_val_loss = 0.0
        with torch.no_grad():
            for x, y in val_loader:
                x, y = x.to(device), y.to(device)
                y_pred = model(x)
                loss, _ = criterion(y_pred, y)
                epoch_val_loss += loss.item() * x.size(0)
                
        epoch_val_loss /= len(val_dataset)
        val_losses.append(epoch_val_loss)
        
        if epoch_val_loss < best_val_loss:
            best_val_loss = epoch_val_loss
            torch.save(model.state_dict(), output_dir / 'best_velocity_model.pth')
            
        if (epoch+1) % 10 == 0 or epoch == 0:
            print(f"Epoch {epoch+1}/{config.epochs} | Train Loss: {epoch_train_loss:.4f} | Val Loss: {epoch_val_loss:.4f}")
            
    # Evaluation
    print("Evaluating on test set...")
    model.load_state_dict(torch.load(output_dir / 'best_velocity_model.pth'))
    model.eval()
    
    test_preds = []
    test_trues = []
    
    with torch.no_grad():
        for x, y in test_loader:
            x = x.to(device)
            preds = model(x)
            test_preds.extend(preds.cpu().numpy().flatten())
            test_trues.extend(y.numpy().flatten())
            
    test_preds = np.array(test_preds)
    test_trues = np.array(test_trues)
    
    mae = np.mean(np.abs(test_preds - test_trues))
    rmse = np.sqrt(np.mean((test_preds - test_trues)**2))
    corr, _ = pearsonr(test_preds, test_trues)
    
    print(f"Test MAE: {mae:.4f} m/s")
    print(f"Test RMSE: {rmse:.4f} m/s")
    print(f"Test Correlation: {corr:.4f}")
    
    # Plotting
    plt.figure(figsize=(10, 5))
    plt.plot(train_losses, label='Train Loss')
    plt.plot(val_losses, label='Val Loss')
    plt.title('Training and Validation Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    plt.savefig(output_dir / 'loss_curve.png')
    plt.close()
    
    plt.figure(figsize=(12, 6))
    plt.plot(test_trues[:300], label='Ground Truth')
    plt.plot(test_preds[:300], label='Predictions', alpha=0.7)
    plt.title('Test Predictions vs Ground Truth (First 300 samples)')
    plt.xlabel('Time Step')
    plt.ylabel('Speed (m/s)')
    plt.legend()
    plt.savefig(output_dir / 'test_predictions.png')
    plt.close()
    
    print(f"Artifacts saved to {output_dir}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Train TCN Velocity Model")
    parser.add_argument('--data_dir', type=str, default='data/io_vnbd', help='Path to IO-VNBD data')
    parser.add_argument('--epochs', type=int, default=100, help='Number of epochs')
    parser.add_argument('--batch_size', type=int, default=64, help='Batch size')
    parser.add_argument('--lr', type=float, default=1e-3, help='Learning rate')
    parser.add_argument('--window_size', type=int, default=50, help='Window size for features')
    parser.add_argument('--stride', type=int, default=5, help='Stride for window extraction')
    parser.add_argument('--output_dir', type=str, default='outputs/velocity_model', help='Output directory for model and plots')
    
    args = parser.parse_args()
    train(args)
