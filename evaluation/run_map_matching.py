import numpy as np
import matplotlib.pyplot as plt
import os
import sys

# Add parent directory to path to import navigation_core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from navigation_core.map_matching import HMMMapMatcher, haversine_distance

def create_synthetic_network():
    """
    Create a synthetic road network.
    Returns:
        nodes: List of (lat, lon)
        edges: List of (node_idx1, node_idx2)
    """
    # A simple square-ish grid
    nodes = [
        (0.0, 0.0),      # 0
        (0.0, 0.01),     # 1
        (0.01, 0.01),    # 2
        (0.01, 0.0),     # 3
        (0.005, 0.0)     # 4
    ]
    edges = [
        (0, 4), (4, 3),  # Bottom edge
        (3, 2),          # Right edge
        (2, 1),          # Top edge
        (1, 0)           # Left edge
    ]
    return nodes, edges

def generate_noisy_trajectory(nodes, edges, noise_std=0.0002):
    """
    Generate a synthetic trajectory that roughly follows the roads, with noise.
    """
    # Let's say the true path is 0 -> 4 -> 3 -> 2
    true_path_nodes = [0, 4, 3, 2]
    trajectory = []
    
    for i in range(len(true_path_nodes) - 1):
        start_node = nodes[true_path_nodes[i]]
        end_node = nodes[true_path_nodes[i+1]]
        
        # Interpolate points along the segment
        num_points = 20
        for j in range(num_points):
            alpha = j / num_points
            lat = start_node[0] * (1 - alpha) + end_node[0] * alpha
            lon = start_node[1] * (1 - alpha) + end_node[1] * alpha
            
            # Add noise
            lat_noisy = lat + np.random.normal(0, noise_std)
            lon_noisy = lon + np.random.normal(0, noise_std)
            
            trajectory.append((lat_noisy, lon_noisy))
            
    # Add the final point
    final_node = nodes[true_path_nodes[-1]]
    trajectory.append((final_node[0] + np.random.normal(0, noise_std), 
                       final_node[1] + np.random.normal(0, noise_std)))
                       
    return trajectory

def main():
    print("Setting up synthetic road network...")
    nodes, edges = create_synthetic_network()
    
    print("Generating noisy trajectory...")
    np.random.seed(42) # for reproducibility
    trajectory = generate_noisy_trajectory(nodes, edges, noise_std=0.0005)
    
    print("Running HMM Map Matching...")
    # Initialize matcher
    # 0.0005 deg is roughly 50m, so set sigma_z accordingly
    matcher = HMMMapMatcher(nodes, edges, sigma_z=50.0, beta=10.0)
    
    matched_trajectory = []
    for pos in trajectory:
        matched_pos = matcher.viterbi_step(pos)
        matched_trajectory.append(matched_pos)
        
    print("Plotting results...")
    plt.figure(figsize=(10, 8))
    
    # Plot road network
    for edge in edges:
        n1, n2 = edge
        lat1, lon1 = nodes[n1]
        lat2, lon2 = nodes[n2]
        plt.plot([lon1, lon2], [lat1, lat2], 'k-', linewidth=3, alpha=0.6, label='Road Network' if edge == edges[0] else "")
        
    # Plot noisy trajectory
    traj_lons = [p[1] for p in trajectory]
    traj_lats = [p[0] for p in trajectory]
    plt.plot(traj_lons, traj_lats, 'rx--', markersize=4, label='Noisy GPS Trajectory', alpha=0.7)
    
    # Plot matched trajectory
    matched_lons = [p[1] for p in matched_trajectory]
    matched_lats = [p[0] for p in matched_trajectory]
    plt.plot(matched_lons, matched_lats, 'b.-', markersize=6, label='Matched Trajectory')
    
    plt.title('HMM Map Matching Evaluation')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.legend()
    plt.grid(True)
    
    # Save plot
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'outputs', 'plots')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'map_matching.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Plot saved to: {output_path}")

if __name__ == "__main__":
    main()
