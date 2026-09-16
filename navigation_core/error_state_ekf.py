import numpy as np
from navigation_core.coordinate_transforms import skew_symmetric

class ErrorStateEKF:
    def __init__(self, config=None):
        if config is None:
            config = {
                'accel_noise': 1e-3,
                'gyro_noise': 1e-4,
                'accel_bias_walk': 1e-5,
                'gyro_bias_walk': 1e-5
            }
        self.config = config
        
        # 15-dimensional error state: [dp(3), dv(3), dtheta(3), dba(3), dbg(3)]
        self.P = np.eye(15) * 1e-4
        self.P[9:12, 9:12] = np.eye(3) * 1e-2  # accel bias
        self.P[12:15, 12:15] = np.eye(3) * 1e-2  # gyro bias

    def predict(self, accel_body, gyro_body, R_body_to_nav, dt):
        F = np.eye(15)
        
        # dp row
        F[0:3, 3:6] = np.eye(3) * dt
        
        # dv row
        accel_nav_skew = skew_symmetric(R_body_to_nav @ accel_body)
        F[3:6, 6:9] = -accel_nav_skew * dt
        F[3:6, 9:12] = -R_body_to_nav * dt
        
        # dtheta row
        gyro_body_skew = skew_symmetric(gyro_body)
        F[6:9, 6:9] = np.eye(3) - gyro_body_skew * dt
        F[6:9, 12:15] = -np.eye(3) * dt
        
        # biases
        F[9:12, 9:12] = np.eye(3)
        F[12:15, 12:15] = np.eye(3)
        
        G = np.zeros((15, 12))
        G[3:6, 0:3] = -R_body_to_nav * dt
        G[6:9, 3:6] = -np.eye(3) * dt
        G[9:12, 6:9] = np.eye(3) * dt
        G[12:15, 9:12] = np.eye(3) * dt
        
        Q = np.zeros((12, 12))
        Q[0:3, 0:3] = np.eye(3) * self.config['accel_noise']
        Q[3:6, 3:6] = np.eye(3) * self.config['gyro_noise']
        Q[6:9, 6:9] = np.eye(3) * self.config['accel_bias_walk']
        Q[9:12, 9:12] = np.eye(3) * self.config['gyro_bias_walk']
        
        self.P = F @ self.P @ F.T + G @ Q @ G.T

    def update_gnss(self, pos_innovation, vel_innovation, R_pos, R_vel):
        H = np.zeros((6, 15))
        H[0:3, 0:3] = np.eye(3)
        H[3:6, 3:6] = np.eye(3)
        
        innovation = np.concatenate([pos_innovation, vel_innovation])
        R = np.zeros((6, 6))
        R[0:3, 0:3] = R_pos
        R[3:6, 3:6] = R_vel
        
        if not self.innovation_gate(innovation, H, R):
            return np.zeros(15)
            
        S = H @ self.P @ H.T + R
        K = self.P @ H.T @ np.linalg.inv(S)
        dx = K @ innovation
        
        self.P = (np.eye(15) - K @ H) @ self.P
        return dx

    def update_velocity(self, vel_innovation, R_vel):
        H = np.zeros((3, 15))
        H[0:3, 3:6] = np.eye(3)
        
        if not self.innovation_gate(vel_innovation, H, R_vel):
            return np.zeros(15)
            
        S = H @ self.P @ H.T + R_vel
        K = self.P @ H.T @ np.linalg.inv(S)
        dx = K @ vel_innovation
        
        self.P = (np.eye(15) - K @ H) @ self.P
        return dx

    def update_nhc(self, R_body_to_nav, vel_nav, R_nhc):
        R_nav_to_body = R_body_to_nav.T
        v_body = R_nav_to_body @ vel_nav
        
        innovation = np.array([0.0, 0.0]) - np.array([v_body[1], v_body[2]])
        
        H = np.zeros((2, 15))
        H[0:2, 3:6] = R_nav_to_body[1:3, :]
        
        if not self.innovation_gate(innovation, H, R_nhc):
            return np.zeros(15)
            
        S = H @ self.P @ H.T + R_nhc
        K = self.P @ H.T @ np.linalg.inv(S)
        dx = K @ innovation
        
        self.P = (np.eye(15) - K @ H) @ self.P
        return dx

    def update_zupt(self, vel_nav, R_zupt):
        innovation = np.array([0.0, 0.0, 0.0]) - vel_nav
        
        H = np.zeros((3, 15))
        H[0:3, 3:6] = np.eye(3)
        
        if not self.innovation_gate(innovation, H, R_zupt):
            return np.zeros(15)
            
        S = H @ self.P @ H.T + R_zupt
        K = self.P @ H.T @ np.linalg.inv(S)
        dx = K @ innovation
        
        self.P = (np.eye(15) - K @ H) @ self.P
        return dx

    def innovation_gate(self, innovation, H, R, chi2_threshold=9.21):
        S = H @ self.P @ H.T + R
        gamma = innovation.T @ np.linalg.inv(S) @ innovation
        return gamma < chi2_threshold

    def get_position_uncertainty(self) -> float:
        return float(np.sqrt(np.trace(self.P[0:3, 0:3])))

    def reset_error_state(self):
        # We don't maintain internal dx, it is computed in updates.
        # But we could reset internal states if we accumulated them.
        pass
