import matplotlib.pyplot as plt
import os
import pandas as pd

def plot_trajectory(df: pd.DataFrame, title: str = 'Trajectory', save_path: str = None):
    """
    Plots GPS lat/lon trajectory on 2D plot.
    """
    if 'gps_lat' not in df.columns or 'gps_lon' not in df.columns:
        print("Missing GPS columns.")
        return
        
    plt.figure(figsize=(10, 8))
    plt.plot(df['gps_lon'], df['gps_lat'], 'b-', label='Trajectory')
    plt.plot(df['gps_lon'].iloc[0], df['gps_lat'].iloc[0], 'go', label='Start')
    plt.plot(df['gps_lon'].iloc[-1], df['gps_lat'].iloc[-1], 'ro', label='End')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.title(title)
    plt.legend()
    plt.grid(True)
    if save_path:
        plt.savefig(save_path)
    plt.show()

def plot_imu_timeseries(df: pd.DataFrame, start_idx: int = 0, n_samples: int = 1000, save_path: str = None):
    """
    Plots a 3-panel plot of accelerometer, gyroscope, and speed timeseries.
    """
    end_idx = min(start_idx + n_samples, len(df))
    subset = df.iloc[start_idx:end_idx]
    
    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    
    # Accelerometer
    if all(c in subset.columns for c in ['accel_x', 'accel_y', 'accel_z']):
        axes[0].plot(subset['timestamp'], subset['accel_x'], label='Acc X')
        axes[0].plot(subset['timestamp'], subset['accel_y'], label='Acc Y')
        axes[0].plot(subset['timestamp'], subset['accel_z'], label='Acc Z')
        axes[0].set_ylabel('Acceleration (m/s²)')
        axes[0].legend()
        axes[0].grid(True)
        axes[0].set_title('Accelerometer Data')
        
    # Gyroscope
    if all(c in subset.columns for c in ['gyro_x', 'gyro_y', 'gyro_z']):
        axes[1].plot(subset['timestamp'], subset['gyro_x'], label='Gyro X')
        axes[1].plot(subset['timestamp'], subset['gyro_y'], label='Gyro Y')
        axes[1].plot(subset['timestamp'], subset['gyro_z'], label='Gyro Z')
        axes[1].set_ylabel('Angular Vel (rad/s)')
        axes[1].legend()
        axes[1].grid(True)
        axes[1].set_title('Gyroscope Data')
        
    # Speed
    if 'gps_speed' in subset.columns:
        axes[2].plot(subset['timestamp'], subset['gps_speed'], label='GPS Speed')
        axes[2].set_ylabel('Speed (m/s)')
        axes[2].legend()
        axes[2].grid(True)
        axes[2].set_title('Speed Data')
        
    axes[2].set_xlabel('Timestamp (s)' if 'timestamp' in subset.columns else 'Index')
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path)
    plt.show()

def plot_trajectory_enu(east: list, north: list, title: str = 'Trajectory (ENU)', save_path: str = None):
    """
    Plots trajectory in ENU coordinates.
    """
    plt.figure(figsize=(10, 8))
    plt.plot(east, north, 'b-', label='Trajectory')
    if len(east) > 0:
        plt.plot(east[0], north[0], 'go', label='Start')
        plt.plot(east[-1], north[-1], 'ro', label='End')
    plt.xlabel('East (m)')
    plt.ylabel('North (m)')
    plt.title(title)
    plt.legend()
    plt.grid(True)
    plt.axis('equal')
    if save_path:
        plt.savefig(save_path)
    plt.show()
