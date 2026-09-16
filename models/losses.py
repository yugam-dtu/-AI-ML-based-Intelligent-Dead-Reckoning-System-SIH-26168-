import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, Dict, Optional

class VelocityLoss(nn.Module):
    """
    Custom loss function for velocity estimation incorporating physical constraints.
    """
    def __init__(self, physics_weight: float = 0.1, smooth_weight: float = 0.01):
        super().__init__()
        self.physics_weight = physics_weight
        self.smooth_weight = smooth_weight
        self.primary_loss = nn.SmoothL1Loss()

    def forward(self, v_pred: torch.Tensor, v_true: torch.Tensor, accel_x: Optional[torch.Tensor] = None, dt: float = 0.1) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        """
        Computes the weighted loss.
        Args:
            v_pred: Predicted velocities (batch_size, 1)
            v_true: Ground truth velocities (batch_size, 1)
            accel_x: Forward acceleration for physics loss (batch_size, time_steps). None to skip physics loss.
            dt: Time step for integration
        Returns:
            Tuple of total loss and dictionary of individual components.
        """
        # Ensure correct shape
        v_pred = v_pred.view(-1)
        v_true = v_true.view(-1)
        
        loss_primary = self.primary_loss(v_pred, v_true)
        
        loss_physics = torch.tensor(0.0, device=v_pred.device)
        if accel_x is not None and len(v_pred) > 1:
            # Simple physics consistency: delta V should match integrated accel
            # Sum of forward acceleration * dt
            delta_v_pred = v_pred[1:] - v_pred[:-1]
            # Average accel for the sequence (this is a simplified proxy since each prediction is from a window)
            integrated_accel = accel_x[:-1, -1] * dt # Use last accel value of the previous window
            loss_physics = F.mse_loss(delta_v_pred, integrated_accel)

        loss_smooth = torch.tensor(0.0, device=v_pred.device)
        if len(v_pred) > 1:
            # Penalize large jumps in velocity prediction (temporal smoothness)
            loss_smooth = F.mse_loss(v_pred[1:], v_pred[:-1])
            
        total_loss = loss_primary + self.physics_weight * loss_physics + self.smooth_weight * loss_smooth
        
        loss_components = {
            'total_loss': total_loss.detach(),
            'huber_loss': loss_primary.detach(),
            'physics_loss': loss_physics.detach(),
            'smooth_loss': loss_smooth.detach()
        }
        
        return total_loss, loss_components
