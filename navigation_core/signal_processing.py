import numpy as np
from scipy.signal import butter, filtfilt

def butterworth_lowpass(data, cutoff_hz, sample_rate_hz, order=2):
    nyq = 0.5 * sample_rate_hz
    normal_cutoff = cutoff_hz / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return filtfilt(b, a, data, axis=0)

def detect_impulses(accel_data, threshold_g=3.0, window_samples=20):
    norms = np.linalg.norm(accel_data, axis=1)
    mask = norms > threshold_g
    
    # Expand mask by window_samples
    expanded_mask = np.copy(mask)
    for i in np.where(mask)[0]:
        start = max(0, i - window_samples)
        end = min(len(accel_data), i + window_samples + 1)
        expanded_mask[start:end] = True
        
    return expanded_mask

def suppress_impulses(data, impulse_mask):
    out = np.copy(data)
    n_samples = len(data)
    if not np.any(impulse_mask):
        return out
        
    # Find continuous regions of True
    changes = np.diff(np.concatenate(([0], impulse_mask.view(np.int8), [0])))
    starts = np.where(changes == 1)[0]
    ends = np.where(changes == -1)[0]
    
    for s, e in zip(starts, ends):
        val_start = data[s-1] if s > 0 else data[e] if e < n_samples else np.zeros_like(data[0])
        val_end = data[e] if e < n_samples else data[s-1] if s > 0 else np.zeros_like(data[0])
        
        # linear interpolation
        length = e - s
        if length > 0:
            for i in range(data.shape[1] if data.ndim > 1 else 1):
                if data.ndim > 1:
                    out[s:e, i] = np.linspace(val_start[i], val_end[i], length)
                else:
                    out[s:e] = np.linspace(val_start, val_end, length)
    return out

def resample_uniform(timestamps, data, target_rate_hz):
    dt = 1.0 / target_rate_hz
    t_start = timestamps[0]
    t_end = timestamps[-1]
    
    uniform_timestamps = np.arange(t_start, t_end, dt)
    
    resampled_data = np.zeros((len(uniform_timestamps), data.shape[1] if data.ndim > 1 else 1))
    
    if data.ndim > 1:
        for i in range(data.shape[1]):
            resampled_data[:, i] = np.interp(uniform_timestamps, timestamps, data[:, i])
    else:
        resampled_data = np.interp(uniform_timestamps, timestamps, data)
        
    return uniform_timestamps, resampled_data

if __name__ == '__main__':
    t = np.linspace(0, 1, 100)
    data = np.random.randn(100, 3)
    filtered = butterworth_lowpass(data, 10, 100)
    assert filtered.shape == data.shape
    
    accel = np.zeros((100, 3))
    accel[50, 0] = 5.0
    mask = detect_impulses(accel, 3.0, 5)
    assert mask[50]
    assert mask[45]
    
    sup = suppress_impulses(accel, mask)
    assert np.all(sup[50] == 0)
    
    ut, ud = resample_uniform(t, data, 50)
    assert len(ut) == 50
    
    print("signal_processing tests passed.")
