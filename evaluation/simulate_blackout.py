import numpy as np
import pandas as pd

def simulate_gnss_blackouts(trajectory_df, blackout_distances_m, n_trials=5, nav_engine_fn=None):
    results = []
    
    if 'cum_dist' not in trajectory_df.columns:
        pos = trajectory_df[['pos_x', 'pos_y']].values
        diffs = np.sqrt(np.sum(np.diff(pos, axis=0)**2, axis=1))
        cum_dist = np.concatenate([[0], np.cumsum(diffs)])
        trajectory_df['cum_dist'] = cum_dist
        
    total_dist = trajectory_df['cum_dist'].iloc[-1]
        
    for dist in blackout_distances_m:
        valid_starts = trajectory_df[trajectory_df['cum_dist'] <= (total_dist - dist)].index.tolist()
        if not valid_starts:
            continue
            
        chosen_starts = np.random.choice(valid_starts, min(n_trials, len(valid_starts)), replace=False)
        
        for start_idx in chosen_starts:
            start_dist = trajectory_df.loc[start_idx, 'cum_dist']
            target_dist = start_dist + dist
            
            end_idx_candidates = trajectory_df[trajectory_df['cum_dist'] >= target_dist].index
            if len(end_idx_candidates) == 0:
                continue
            end_idx = end_idx_candidates[0]
            
            if nav_engine_fn:
                est_traj, metrics = nav_engine_fn(trajectory_df, start_idx, end_idx)
            else:
                est_traj, metrics = simple_dead_reckoning(trajectory_df, start_idx, end_idx)
                
            time_start = trajectory_df.loc[start_idx, 'time']
            time_end = trajectory_df.loc[end_idx, 'time']
            duration = time_end - time_start
            
            final_err = metrics.get('final_error_m', 0.0)
            
            results.append({
                'distance': dist,
                'final_error_m': final_err,
                'drift_pct': (final_err / dist) * 100 if dist > 0 else 0.0,
                'duration_s': duration,
                'speed_mps': dist / duration if duration > 0 else 0.0
            })
            
    return results

def simple_dead_reckoning(trajectory_df, mask_start, mask_end, velocity_model=None):
    df_subset = trajectory_df.loc[mask_start:mask_end].copy()
    
    if len(df_subset) == 0:
        return np.array([]), {}
        
    dt_arr = np.diff(df_subset['time'].values)
    dt_arr = np.append(dt_arr, dt_arr[-1] if len(dt_arr) > 0 else 0.1)
    
    pos = df_subset[['pos_x', 'pos_y']].values
    vel = df_subset[['vel_x', 'vel_y']].values
    gyro_z = df_subset['gyro_z'].values
    
    est_pos = np.zeros_like(pos)
    est_pos[0] = pos[0]
    
    if velocity_model:
        pred_speed = velocity_model.predict(df_subset)
    else:
        last_speed = np.linalg.norm(vel[0])
        pred_speed = np.full(len(df_subset), last_speed)
        
    heading = np.arctan2(vel[0, 1], vel[0, 0])
    
    for i in range(1, len(df_subset)):
        dt = dt_arr[i-1]
        heading += gyro_z[i-1] * dt
        v = pred_speed[i-1]
        
        est_pos[i, 0] = est_pos[i-1, 0] + v * np.cos(heading) * dt
        est_pos[i, 1] = est_pos[i-1, 1] + v * np.sin(heading) * dt
        
    errs = np.linalg.norm(pos - est_pos, axis=1)
    metrics = {
        'final_error_m': errs[-1],
        'rmse': np.sqrt(np.mean(errs**2))
    }
    
    return est_pos, metrics
