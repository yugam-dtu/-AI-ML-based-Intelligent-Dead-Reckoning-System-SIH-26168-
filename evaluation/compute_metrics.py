import numpy as np

def compute_trajectory_metrics(gt_pos, est_pos, gt_vel=None, est_vel=None, gt_heading=None, est_heading=None):
    metrics = {}
    
    gt_pos = np.array(gt_pos)
    est_pos = np.array(est_pos)
    
    errs = np.linalg.norm(gt_pos - est_pos, axis=1)
    metrics['final_error_m'] = errs[-1]
    metrics['rmse'] = np.sqrt(np.mean(errs**2))
    metrics['ate'] = np.mean(errs)
    metrics['max_error_m'] = np.max(errs)
    
    if gt_heading is not None and est_heading is not None:
        metrics['heading_error_deg'] = np.mean(np.abs(np.array(gt_heading) - np.array(est_heading)))
        
    if gt_vel is not None and est_vel is not None:
        vel_errs = np.abs(np.array(gt_vel) - np.array(est_vel))
        metrics['velocity_mae'] = np.mean(vel_errs)
        metrics['velocity_rmse'] = np.sqrt(np.mean(vel_errs**2))
        
    return metrics

def compute_drift_percentage(final_error_m, distance_travelled_m):
    if distance_travelled_m <= 0:
        return 0.0
    return (final_error_m / distance_travelled_m) * 100.0
