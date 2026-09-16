import numpy as np

# WGS-84 constants
WGS84_A = 6378137.0
WGS84_F = 1.0 / 298.257223563
WGS84_E2 = WGS84_F * (2.0 - WGS84_F)

def geodetic_to_ecef(lat, lon, alt):
    lat_rad = np.radians(lat)
    lon_rad = np.radians(lon)
    sin_lat = np.sin(lat_rad)
    cos_lat = np.cos(lat_rad)
    sin_lon = np.sin(lon_rad)
    cos_lon = np.cos(lon_rad)
    
    N = WGS84_A / np.sqrt(1.0 - WGS84_E2 * sin_lat**2)
    
    x = (N + alt) * cos_lat * cos_lon
    y = (N + alt) * cos_lat * sin_lon
    z = (N * (1.0 - WGS84_E2) + alt) * sin_lat
    
    return x, y, z

def ecef_to_enu(x, y, z, lat0, lon0, alt0):
    x0, y0, z0 = geodetic_to_ecef(lat0, lon0, alt0)
    
    dx = x - x0
    dy = y - y0
    dz = z - z0
    
    lat0_rad = np.radians(lat0)
    lon0_rad = np.radians(lon0)
    
    slat = np.sin(lat0_rad)
    clat = np.cos(lat0_rad)
    slon = np.sin(lon0_rad)
    clon = np.cos(lon0_rad)
    
    e = -slon * dx + clon * dy
    n = -slat * clon * dx - slat * slon * dy + clat * dz
    u = clat * clon * dx + clat * slon * dy + slat * dz
    
    return e, n, u

def latlon_to_enu(lat, lon, lat0, lon0, alt=0, alt0=0):
    """Converts Geodetic coordinates to ENU."""
    x, y, z = geodetic_to_ecef(lat, lon, alt)
    return ecef_to_enu(x, y, z, lat0, lon0, alt0)

def enu_to_ecef(e, n, u, lat0, lon0, alt0):
    x0, y0, z0 = geodetic_to_ecef(lat0, lon0, alt0)
    
    lat0_rad = np.radians(lat0)
    lon0_rad = np.radians(lon0)
    
    slat = np.sin(lat0_rad)
    clat = np.cos(lat0_rad)
    slon = np.sin(lon0_rad)
    clon = np.cos(lon0_rad)
    
    dx = -slon * e - slat * clon * n + clat * clon * u
    dy = clon * e - slat * slon * n + clat * slon * u
    dz = clat * n + slat * u
    
    return x0 + dx, y0 + dy, z0 + dz

def ecef_to_geodetic(x, y, z):
    p = np.sqrt(x**2 + y**2)
    if p < 1e-10:
        lat = np.pi / 2 if z > 0 else -np.pi / 2
        lon = 0.0
        alt = np.abs(z) - WGS84_A * (1 - WGS84_E2)
        return np.degrees(lat), np.degrees(lon), alt
    
    lon = np.arctan2(y, x)
    
    # Bowring's method
    a = WGS84_A
    e2 = WGS84_E2
    b = a * np.sqrt(1 - e2)
    ep2 = (a**2 - b**2) / b**2
    
    th = np.arctan2(a * z, b * p)
    lat = np.arctan2(z + ep2 * b * np.sin(th)**3, p - e2 * a * np.cos(th)**3)
    
    N = a / np.sqrt(1 - e2 * np.sin(lat)**2)
    alt = p / np.cos(lat) - N
    
    return np.degrees(lat), np.degrees(lon), alt

def enu_to_latlon(east, north, up, lat0, lon0, alt0=0):
    """Converts ENU to Geodetic coordinates."""
    x, y, z = enu_to_ecef(east, north, up, lat0, lon0, alt0)
    return ecef_to_geodetic(x, y, z)

def quaternion_multiply(q1, q2):
    """Hamilton convention [w,x,y,z]"""
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    return np.array([
        w1*w2 - x1*x2 - y1*y2 - z1*z2,
        w1*x2 + x1*w2 + y1*z2 - z1*y2,
        w1*y2 - x1*z2 + y1*w2 + z1*x2,
        w1*z2 + x1*y2 - y1*x2 + z1*w2
    ])

def quaternion_to_rotation_matrix(q):
    w, x, y, z = q
    return np.array([
        [1 - 2*y**2 - 2*z**2, 2*x*y - 2*z*w, 2*x*z + 2*y*w],
        [2*x*y + 2*z*w, 1 - 2*x**2 - 2*z**2, 2*y*z - 2*x*w],
        [2*x*z - 2*y*w, 2*y*z + 2*x*w, 1 - 2*x**2 - 2*y**2]
    ])

def rotation_matrix_to_quaternion(R):
    tr = R[0,0] + R[1,1] + R[2,2]
    if tr > 0:
        S = np.sqrt(tr + 1.0) * 2
        w = 0.25 * S
        x = (R[2,1] - R[1,2]) / S
        y = (R[0,2] - R[2,0]) / S
        z = (R[1,0] - R[0,1]) / S
    elif (R[0,0] > R[1,1]) and (R[0,0] > R[2,2]):
        S = np.sqrt(1.0 + R[0,0] - R[1,1] - R[2,2]) * 2
        w = (R[2,1] - R[1,2]) / S
        x = 0.25 * S
        y = (R[0,1] + R[1,0]) / S
        z = (R[0,2] + R[2,0]) / S
    elif R[1,1] > R[2,2]:
        S = np.sqrt(1.0 + R[1,1] - R[0,0] - R[2,2]) * 2
        w = (R[0,2] - R[2,0]) / S
        x = (R[0,1] + R[1,0]) / S
        y = 0.25 * S
        z = (R[1,2] + R[2,1]) / S
    else:
        S = np.sqrt(1.0 + R[2,2] - R[0,0] - R[1,1]) * 2
        w = (R[1,0] - R[0,1]) / S
        x = (R[0,2] + R[2,0]) / S
        y = (R[1,2] + R[2,1]) / S
        z = 0.25 * S
    return np.array([w, x, y, z])

def euler_to_quaternion(roll, pitch, yaw):
    cr = np.cos(roll * 0.5)
    sr = np.sin(roll * 0.5)
    cp = np.cos(pitch * 0.5)
    sp = np.sin(pitch * 0.5)
    cy = np.cos(yaw * 0.5)
    sy = np.sin(yaw * 0.5)

    w = cr * cp * cy + sr * sp * sy
    x = sr * cp * cy - cr * sp * sy
    y = cr * sp * cy + sr * cp * sy
    z = cr * cp * sy - sr * sp * cy

    return np.array([w, x, y, z])

def quaternion_to_euler(q):
    w, x, y, z = q
    sinr_cosp = 2 * (w * x + y * z)
    cosr_cosp = 1 - 2 * (x**2 + y**2)
    roll = np.arctan2(sinr_cosp, cosr_cosp)

    sinp = 2 * (w * y - z * x)
    if np.abs(sinp) >= 1:
        pitch = np.sign(sinp) * np.pi / 2
    else:
        pitch = np.arcsin(sinp)

    siny_cosp = 2 * (w * z + x * y)
    cosy_cosp = 1 - 2 * (y**2 + z**2)
    yaw = np.arctan2(siny_cosp, cosy_cosp)

    return roll, pitch, yaw

def skew_symmetric(v):
    return np.array([
        [0, -v[2], v[1]],
        [v[2], 0, -v[0]],
        [-v[1], v[0], 0]
    ])

if __name__ == '__main__':
    lat, lon, lat0, lon0 = 34.0, -118.0, 34.001, -118.001
    e, n, u = latlon_to_enu(lat, lon, lat0, lon0)
    lat2, lon2, alt2 = enu_to_latlon(e, n, u, lat0, lon0)
    assert np.isclose(lat, lat2) and np.isclose(lon, lon2) and np.isclose(0, alt2)
    
    q1 = np.array([1, 0, 0, 0])
    q2 = np.array([0, 1, 0, 0])
    assert np.allclose(quaternion_multiply(q1, q2), q2)
    print("coordinate_transforms tests passed.")
