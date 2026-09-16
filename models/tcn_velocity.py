import torch
import torch.nn as nn
import torch.nn.functional as F

class TCNBlock(nn.Module):
    """
    Dilated causal Conv1d block for Temporal Convolutional Network.
    """
    def __init__(self, in_channels: int, out_channels: int, kernel_size: int, dilation: int, dropout: float = 0.1):
        super().__init__()
        # Causal padding = (kernel_size - 1) * dilation
        self.padding = (kernel_size - 1) * dilation
        self.conv1 = nn.Conv1d(
            in_channels, out_channels, kernel_size, 
            padding=self.padding, dilation=dilation
        )
        self.bn1 = nn.BatchNorm1d(out_channels)
        self.relu1 = nn.ReLU()
        self.dropout1 = nn.Dropout(dropout)
        
        self.conv2 = nn.Conv1d(
            out_channels, out_channels, kernel_size,
            padding=self.padding, dilation=dilation
        )
        self.bn2 = nn.BatchNorm1d(out_channels)
        self.relu2 = nn.ReLU()
        self.dropout2 = nn.Dropout(dropout)
        
        # 1x1 conv for residual connection if channels change
        self.downsample = nn.Conv1d(in_channels, out_channels, 1) if in_channels != out_channels else None
        self.relu = nn.ReLU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        res = x if self.downsample is None else self.downsample(x)
        
        # First layer
        out = self.conv1(x)
        out = out[:, :, :-self.padding]  # Remove padding for causal convolution
        out = self.bn1(out)
        out = self.relu1(out)
        out = self.dropout1(out)
        
        # Second layer
        out = self.conv2(out)
        out = out[:, :, :-self.padding]
        out = self.bn2(out)
        out = self.relu2(out)
        out = self.dropout2(out)
        
        return self.relu(out + res)

class TCNVelocityModel(nn.Module):
    """
    TCN-based velocity estimation model.
    """
    def __init__(self):
        super().__init__()
        
        # Input features: 9 (accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z, accel_mag, gyro_mag, accel_x_cumsum)
        self.tcn_blocks = nn.Sequential(
            TCNBlock(9, 32, kernel_size=3, dilation=1, dropout=0.1),
            TCNBlock(32, 32, kernel_size=3, dilation=2, dropout=0.1),
            TCNBlock(32, 32, kernel_size=3, dilation=4, dropout=0.1),
            TCNBlock(32, 32, kernel_size=3, dilation=8, dropout=0.1),
            TCNBlock(32, 16, kernel_size=3, dilation=16, dropout=0.1)
        )
        self.linear = nn.Linear(16, 1)
        self.final_relu = nn.ReLU() # To ensure non-negative velocity

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.
        Args:
            x (torch.Tensor): Input shape (batch, time_steps, features)
        Returns:
            torch.Tensor: Predicted velocity, shape (batch, 1)
        """
        # Transpose to (batch, features, time_steps) for Conv1d
        x = x.transpose(1, 2)
        
        # TCN features
        x = self.tcn_blocks(x)
        
        # Global Average Pooling over time
        x = x.mean(dim=2)
        
        # Linear output and non-negativity constraint
        out = self.linear(x)
        out = self.final_relu(out)
        
        return out

    def count_parameters(self) -> int:
        """
        Count total trainable parameters in the model.
        """
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
