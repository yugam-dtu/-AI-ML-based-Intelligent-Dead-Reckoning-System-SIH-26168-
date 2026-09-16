import numpy as np
from scipy.spatial.transform import Rotation as R_scipy

# Fallback implementations in case navigation_core modules are not ready yet
def quat_mult(q1, q2):
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    return np.array([
        w1*w2 - x1*x2 - y1*y2 - z1*z2,
        w1*x2 + x1*w2 + y1*z2 - z1*y2,
        w1*y2 - x1*z2 + y1*w2 + z1*x2,
        w1*z2 + x1*y2 - y1*x2 + z1*w2
    ])

def get_rot_matrix(q):
    w, x, y, z = q
    return np.array([
        [1 - 2*y**2 - 2*z**2, 2*x*y - 2*z*w, 2*x*z + 2*y*w],
        [2*x*y + 2*z*w, 1 - 2*x**2 - 2*z**2, 2*y*z - 2*x*w],
        [2*x*z - 2*y*w, 2*y*z + 2*x*w, 1 - 2*x**2 - 2*y**2]
    ])

class StrapdownINS:
    """
    Basic Strapdown Inertial Navigation System.
    Uses ENU (East-North-Up) local frame.
    """
    def __init__(self, initial_pos_enu, initial_vel_enu, initial_quaternion):
        """
        Args:
            initial_pos_enu: Initial position (E, N, U) in meters.
            initial_vel_enu: Initial velocity (Ve, Vn, Vu) in m/s.
            initial_quaternion: Initial orientation [w, x, y, z] from body to nav frame.
        """
        self.bias_accel = np.zeros(3)
        self.bias_gyro = np.zeros(3)
        self.gravity_enu = np.array([0.0, 0.0, -9.81])
        self.reset(initial_pos_enu, initial_vel_enu, initial_quaternion)

    def reset(self, pos, vel, quat):
        """Reset INS state."""
        self.pos = np.array(pos, dtype=float)
        self.vel = np.array(vel, dtype=float)
        self.quat = np.array(quat, dtype=float)
        self.quat = self.quat / np.linalg.norm(self.quat)

    def propagate(self, accel_body, gyro_body, dt):
        """
        Propagate INS state using a single IMU measurement.
        
        Args:
            accel_body: Specific force [ax, ay, az] in m/s^2.
            gyro_body: Angular rate [wx, wy, wz] in rad/s.
            dt: Time step in seconds.
            
        Returns:
            tuple: (position, velocity, quaternion)
        """
        accel_body = np.array(accel_body) - self.bias_accel
        gyro_body = np.array(gyro_body) - self.bias_gyro
        
        # 2. Quaternion update using rotation vector method
        ang_rate_mag = np.linalg.norm(gyro_body)
        if ang_rate_mag > 1e-8:
            theta = ang_rate_mag * dt
            delta_q = np.array([
                np.cos(theta/2),
                *(gyro_body / ang_rate_mag * np.sin(theta/2))
            ])
        else:
            delta_q = np.array([1.0, 0.0, 0.0, 0.0])
            
        self.quat = quat_mult(self.quat, delta_q)
        
        # 3. Normalize quaternion
        self.quat = self.quat / np.linalg.norm(self.quat)
        
        # 4. Rotate specific force to nav frame
        C_b_n = get_rot_matrix(self.quat)
        accel_nav = C_b_n @ accel_body
        
        # 5. Subtract gravity (Note: gravity vector is [0,0,-9.81], so we subtract it 
        # meaning accel_nav - [0,0,-9.81] = accel_nav + [0,0,9.81])
        # Wait, if sensor measures specific force f = a - g
        # Then a = f + g. If g is [0, 0, -9.81], a = f + [0, 0, -9.81].
        # In ENU, gravity vector is [0, 0, -9.81] (downwards).
        # Specific force measures upward when stationary, so [0, 0, 9.81].
        # Nav accel = [0, 0, 9.81] + [0, 0, -9.81] = 0.
        accel_nav_corrected = accel_nav + self.gravity_enu
        
        # 6 & 7. Trapezoidal integration (using current state and new accel)
        # For simplicity in this step, Euler integration for velocity and trap/euler for pos
        vel_new = self.vel + accel_nav_corrected * dt
        pos_new = self.pos + (self.vel + vel_new) * 0.5 * dt
        
        self.vel = vel_new
        self.pos = pos_new
        
        return self.pos, self.vel, self.quat

    def get_rotation_matrix(self) -> np.ndarray:
        return get_rot_matrix(self.quat)

    def get_euler(self) -> tuple:
        """Returns (roll, pitch, yaw) in radians. Scipy uses x,y,z,w format for quats."""
        w, x, y, z = self.quat
        r = R_scipy.from_quat([x, y, z, w])
        return tuple(r.as_euler('xyz'))

    def get_heading(self) -> float:
        """Returns yaw in radians."""
        return self.get_euler()[2]

if __name__ == '__main__':
    # Basic sanity check test
    print("Running Strapdown INS sanity check...")
    ins = StrapdownINS([0,0,0], [0,0,0], [1,0,0,0])
    
    # Simulate 100 steps of stationary IMU
    # specific force = [0, 0, 9.81] (resisting gravity of -9.81)
    accel = [0.0, 0.0, 9.81]
    gyro = [0.0, 0.0, 0.0]
    dt = 0.01
    
    for _ in range(100):
        pos, vel, quat = ins.propagate(accel, gyro, dt)
        
    print(f"Final Position: {pos}")
    print(f"Final Velocity: {vel}")
    print(f"Final Quaternion: {quat}")
    
    assert np.allclose(pos, 0, atol=1e-3), "Position drifted significantly!"
    assert np.allclose(vel, 0, atol=1e-3), "Velocity drifted significantly!"
    print("Sanity check passed!")
