import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset
from typing import List, Tuple, Optional

class VelocityDataset(Dataset):
    """
    PyTorch Dataset for velocity estimation.
    """
    def __init__(self, windows: List[np.ndarray], labels: List[float], mean: Optional[np.ndarray] = None, std: Optional[np.ndarray] = None):
        self.windows = windows
        self.labels = labels
        self.mean = mean
        self.std = std
        
        if self.mean is not None and self.std is not None:
            # Normalize windows
            eps = 1e-8
            self.windows = [(w - self.mean) / (self.std + eps) for w in self.windows]

    def __len__(self) -> int:
        return len(self.windows)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        x = torch.tensor(self.windows[idx], dtype=torch.float32)
        y = torch.tensor([self.labels[idx]], dtype=torch.float32)
        return x, y

def extract_windows(df: pd.DataFrame, window_size: int = 50, stride: int = 5, feature_cols: Optional[List[str]] = None, label_col: str = 'gps_speed') -> List[Tuple[np.ndarray, float]]:
    """
    Extracts sliding windows from trajectory dataframe.
    """
    if feature_cols is None:
        feature_cols = ['accel_x', 'accel_y', 'accel_z', 'gyro_x', 'gyro_y', 'gyro_z']
        
    # Check if necessary columns exist
    missing = [c for c in feature_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing feature columns in dataframe: {missing}")
    if label_col not in df.columns:
        raise ValueError(f"Missing label column in dataframe: {label_col}")

    # Compute derived features
    df = df.copy()
    df['accel_magnitude'] = np.sqrt(df['accel_x']**2 + df['accel_y']**2 + df['accel_z']**2)
    df['gyro_magnitude'] = np.sqrt(df['gyro_x']**2 + df['gyro_y']**2 + df['gyro_z']**2)
    df['accel_x_cumsum'] = df['accel_x'].cumsum() # Simplified integration
    
    all_features = feature_cols + ['accel_magnitude', 'gyro_magnitude', 'accel_x_cumsum']
    
    data = df[all_features].values
    labels = df[label_col].values
    
    windows_list = []
    
    num_windows = (len(df) - window_size) // stride + 1
    
    for i in range(0, len(df) - window_size + 1, stride):
        win_data = data[i:i+window_size]
        # Use the label at the end of the window
        win_label = labels[i+window_size-1]
        
        if not np.isnan(win_data).any() and not np.isnan(win_label):
            windows_list.append((win_data, win_label))
            
    return windows_list

def compute_normalization(windows: List[np.ndarray]) -> Tuple[np.ndarray, np.ndarray]:
    """
    Computes mean and std across a list of windows for normalization.
    """
    all_data = np.concatenate(windows, axis=0) # Shape: (Total_T, Features)
    mean = np.mean(all_data, axis=0)
    std = np.std(all_data, axis=0)
    return mean, std
