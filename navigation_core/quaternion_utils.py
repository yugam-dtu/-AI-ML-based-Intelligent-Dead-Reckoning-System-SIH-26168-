import numpy as np
from coordinate_transforms import quaternion_multiply

def quaternion_normalize(q):
    return q / np.linalg.norm(q)

def quaternion_conjugate(q):
    return np.array([q[0], -q[1], -q[2], -q[3]])

def quaternion_rotate_vector(q, v):
    v_q = np.array([0.0, v[0], v[1], v[2]])
    q_conj = quaternion_conjugate(q)
    return quaternion_multiply(quaternion_multiply(q, v_q), q_conj)[1:]

def rotation_vector_to_quaternion(theta_vec):
    angle = np.linalg.norm(theta_vec)
    if angle < 1e-8:
        return np.array([1.0, 0.0, 0.0, 0.0])
    axis = theta_vec / angle
    w = np.cos(angle / 2)
    xyz = axis * np.sin(angle / 2)
    return np.array([w, xyz[0], xyz[1], xyz[2]])

if __name__ == '__main__':
    q = np.array([1.0, 2.0, 3.0, 4.0])
    q_norm = quaternion_normalize(q)
    assert np.isclose(np.linalg.norm(q_norm), 1.0)
    
    v = np.array([1.0, 0.0, 0.0])
    q_rot = np.array([np.cos(np.pi/4), 0, 0, np.sin(np.pi/4)]) # 90 deg z
    v_rot = quaternion_rotate_vector(q_rot, v)
    assert np.allclose(v_rot, [0, 1, 0], atol=1e-7)
    
    print("quaternion_utils tests passed.")
