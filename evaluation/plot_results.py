import matplotlib.pyplot as plt
import numpy as np

def plot_gt_vs_ins(gt_east, gt_north, ins_east, ins_north, title, save_path):
    plt.figure(figsize=(8,8))
    plt.plot(gt_east, gt_north, 'b-', label='Ground Truth')
    plt.plot(ins_east, ins_north, 'r--', label='Raw INS')
    plt.axis('equal')
    plt.plot(gt_east[0], gt_north[0], 'go', label='Start')
    plt.plot(gt_east[-1], gt_north[-1], 'ro', label='End')
    plt.title(title, fontsize=14)
    plt.legend()
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()

def plot_gt_vs_aided(gt_east, gt_north, est_east, est_north, title, save_path, label='AI-Aided INS'):
    plt.figure(figsize=(8,8))
    plt.plot(gt_east, gt_north, 'b-', label='Ground Truth')
    plt.plot(est_east, est_north, 'g--', label=label)
    plt.axis('equal')
    plt.plot(gt_east[0], gt_north[0], 'go', label='Start')
    plt.title(title, fontsize=14)
    plt.legend()
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()

def plot_error_vs_time(time_s, errors_dict, title, save_path):
    plt.figure(figsize=(10,6))
    for label_str, errors in errors_dict.items():
        plt.plot(time_s, errors, label=label_str)
    plt.axhline(y=10.0, color='r', linestyle=':', label='10% Drift Threshold')
    plt.xlabel('Time (s)', fontsize=12)
    plt.ylabel('Position Error (m)', fontsize=12)
    plt.title(title, fontsize=14)
    plt.legend()
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()

def plot_velocity_comparison(time_s, gt_speed, pred_speed, title, save_path):
    plt.figure(figsize=(10,5))
    plt.plot(time_s, gt_speed, 'b-', label='Ground Truth')
    plt.plot(time_s, pred_speed, 'g--', label='Predicted Speed')
    mae = np.mean(np.abs(np.array(gt_speed) - np.array(pred_speed)))
    plt.annotate(f'MAE: {mae:.2f} m/s', xy=(0.05, 0.9), xycoords='axes fraction', 
                 fontsize=12, bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", lw=1))
    plt.xlabel('Time (s)', fontsize=12)
    plt.ylabel('Speed (m/s)', fontsize=12)
    plt.title(title, fontsize=14)
    plt.legend()
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()

def plot_drift_vs_distance(distances_m, drift_percentages_dict, title, save_path):
    plt.figure(figsize=(10,6))
    n_groups = len(distances_m)
    n_methods = len(drift_percentages_dict)
    width = 0.8 / n_methods
    x = np.arange(n_groups)
    
    for i, (label_str, drifts) in enumerate(drift_percentages_dict.items()):
        offset = (i - n_methods/2) * width + width/2
        plt.bar(x + offset, drifts, width, label=label_str)
        
    plt.axhline(y=10.0, color='r', linestyle='--', label='10% Target')
    plt.xticks(x, [f'{d}m' for d in distances_m])
    plt.xlabel('Blackout Distance', fontsize=12)
    plt.ylabel('Drift (%)', fontsize=12)
    plt.title(title, fontsize=14)
    plt.legend()
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()

def plot_ablation_table(results_dict, save_path):
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.axis('tight')
    ax.axis('off')
    
    cols = ['Method', 'RMSE (m)', 'Max Error (m)', 'Velocity MAE', 'Drift %']
    cell_text = []
    
    for method, metrics in results_dict.items():
        cell_text.append([
            method, 
            f"{metrics.get('rmse', 0):.2f}", 
            f"{metrics.get('max_error_m', 0):.2f}", 
            f"{metrics.get('velocity_mae', 0):.2f}", 
            f"{metrics.get('drift_pct', 0):.2f}%"
        ])
        
    table = ax.table(cellText=cell_text, colLabels=cols, loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1.2, 1.8)
    
    # Style header
    for j, _ in enumerate(cols):
        table[(0, j)].set_facecolor('#dddddd')
        
    plt.title("Ablation Study Results", fontsize=16, pad=20)
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()
