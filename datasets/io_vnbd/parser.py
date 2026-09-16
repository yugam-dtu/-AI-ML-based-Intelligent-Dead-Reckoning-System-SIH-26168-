import os
import pandas as pd
import numpy as np
import glob
import random

class IOVNBDDataset:
    """
    Parser for the IO-VNBD dataset (smartphone sensor data).
    """

    def __init__(self, data_dir: str):
        """
        Initialize the dataset parser.
        
        Args:
            data_dir (str): Directory containing the CSV files.
        """
        self.data_dir = data_dir
        self.files = glob.glob(os.path.join(data_dir, "*.csv"))
        if not self.files:
            # Maybe nested directories?
            self.files = glob.glob(os.path.join(data_dir, "**", "*.csv"), recursive=True)

    def load_smartphone_data(self, filepath: str) -> pd.DataFrame:
        """
        Loads CSV data and standardizes column names.
        
        Args:
            filepath (str): Path to CSV file.
            
        Returns:
            pd.DataFrame: Standardized dataframe.
        """
        try:
            df = pd.read_csv(filepath)
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            return pd.DataFrame()
            
        # Standard column mapping attempts
        # Map keys to standardized names
        col_mapping = {
            'time': 'timestamp',
            'timestamp': 'timestamp',
            'time (s)': 'timestamp',
            
            'accel_x': 'accel_x', 'ax': 'accel_x', 'accelerometer_x': 'accel_x',
            'accel_y': 'accel_y', 'ay': 'accel_y', 'accelerometer_y': 'accel_y',
            'accel_z': 'accel_z', 'az': 'accel_z', 'accelerometer_z': 'accel_z',
            
            'gyro_x': 'gyro_x', 'gx': 'gyro_x', 'gyroscope_x': 'gyro_x',
            'gyro_y': 'gyro_y', 'gy': 'gyro_y', 'gyroscope_y': 'gyro_y',
            'gyro_z': 'gyro_z', 'gz': 'gyro_z', 'gyroscope_z': 'gyro_z',
            
            'mag_x': 'mag_x', 'mx': 'mag_x', 'magnetometer_x': 'mag_x',
            'mag_y': 'mag_y', 'my': 'mag_y', 'magnetometer_y': 'mag_y',
            'mag_z': 'mag_z', 'mz': 'mag_z', 'magnetometer_z': 'mag_z',
            
            'lat': 'gps_lat', 'latitude': 'gps_lat',
            'lon': 'gps_lon', 'longitude': 'gps_lon', 'lng': 'gps_lon',
            'speed': 'gps_speed', 'gps_speed': 'gps_speed',
            'bearing': 'gps_bearing', 'heading': 'gps_bearing'
        }
        
        # Rename columns to lowercase for mapping matching
        original_cols = df.columns
        new_cols = []
        for c in original_cols:
            c_lower = str(c).lower().strip()
            found = False
            for k, v in col_mapping.items():
                if k in c_lower:
                    new_cols.append(v)
                    found = True
                    break
            if not found:
                new_cols.append(c)
        df.columns = new_cols
        
        # Drop rows where all critical IMU data is NaN
        imu_cols = [c for c in ['accel_x', 'accel_y', 'accel_z', 'gyro_x', 'gyro_y', 'gyro_z'] if c in df.columns]
        if imu_cols:
            df = df.dropna(subset=imu_cols, how='all')
            
        if 'timestamp' in df.columns:
            df = df.sort_values(by='timestamp').reset_index(drop=True)
            
        return df

    def split_into_trajectories(self, df: pd.DataFrame, gap_threshold_s: float = 60.0) -> list[pd.DataFrame]:
        """
        Splits a single dataframe into multiple trajectories based on time gaps.
        
        Args:
            df (pd.DataFrame): The continuous dataframe.
            gap_threshold_s (float): Gap in seconds to split trajectory.
            
        Returns:
            list[pd.DataFrame]: List of individual trajectories.
        """
        if 'timestamp' not in df.columns or len(df) == 0:
            return [df]
            
        diffs = df['timestamp'].diff()
        split_indices = df.index[diffs > gap_threshold_s].tolist()
        
        trajectories = []
        start_idx = 0
        for idx in split_indices:
            trajectories.append(df.iloc[start_idx:idx].copy())
            start_idx = idx
        trajectories.append(df.iloc[start_idx:].copy())
        
        return [t for t in trajectories if len(t) > 0]

    def _haversine(self, lat1, lon1, lat2, lon2):
        R = 6371000.0
        phi1 = np.radians(lat1)
        phi2 = np.radians(lat2)
        dphi = np.radians(lat2 - lat1)
        dlambda = np.radians(lon2 - lon1)
        a = np.sin(dphi/2)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        return R * c

    def get_trajectory_stats(self, traj: pd.DataFrame) -> dict:
        """
        Calculates basic statistics for a trajectory.
        
        Args:
            traj (pd.DataFrame): Trajectory dataframe.
            
        Returns:
            dict: Dictionary with duration_s, distance_m, mean_speed_mps, n_samples.
        """
        if len(traj) == 0:
            return {'duration_s': 0, 'distance_m': 0, 'mean_speed_mps': 0, 'n_samples': 0}
            
        n_samples = len(traj)
        duration_s = 0.0
        if 'timestamp' in traj.columns:
            duration_s = traj['timestamp'].max() - traj['timestamp'].min()
            
        distance_m = 0.0
        if 'gps_lat' in traj.columns and 'gps_lon' in traj.columns:
            lats = traj['gps_lat'].dropna().values
            lons = traj['gps_lon'].dropna().values
            if len(lats) > 1:
                # Vectorized haversine over consecutive points
                distances = self._haversine(lats[:-1], lons[:-1], lats[1:], lons[1:])
                distance_m = np.sum(distances)
                
        mean_speed_mps = 0.0
        if duration_s > 0:
            mean_speed_mps = distance_m / duration_s
            
        return {
            'duration_s': duration_s,
            'distance_m': distance_m,
            'mean_speed_mps': mean_speed_mps,
            'n_samples': n_samples
        }

    def trajectory_split(self, trajectories: list, ratios: list = [0.7, 0.15, 0.15], seed: int = 42) -> tuple:
        """
        Splits a list of trajectories into train, val, and test sets to avoid data leakage.
        
        Args:
            trajectories (list): List of DataFrames.
            ratios (list): Proportions for train, val, test. Must sum to 1.
            seed (int): Random seed.
            
        Returns:
            tuple: (train_trajs, val_trajs, test_trajs)
        """
        random.seed(seed)
        trajectories_copy = list(trajectories)
        random.shuffle(trajectories_copy)
        
        n = len(trajectories_copy)
        train_end = int(n * ratios[0])
        val_end = train_end + int(n * ratios[1])
        
        train_trajs = trajectories_copy[:train_end]
        val_trajs = trajectories_copy[train_end:val_end]
        test_trajs = trajectories_copy[val_end:]
        
        return train_trajs, val_trajs, test_trajs
