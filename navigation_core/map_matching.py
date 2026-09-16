import numpy as np
import math
from typing import List, Tuple, Dict, Any

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees) in meters.
    """
    R = 6371000.0  # Earth radius in meters
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0) ** 2
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def point_to_segment_projection(
    px: float, py: float, 
    ax: float, ay: float, 
    bx: float, by: float
) -> Tuple[float, float, float]:
    """
    Project point (px, py) onto line segment from (ax, ay) to (bx, by).
    Since we are working with lat/lon, we assume local flat earth 
    approximation for small segments.
    Returns (proj_x, proj_y, distance_to_segment) in degrees.
    """
    dx = bx - ax
    dy = by - ay
    
    # If segment is a point
    if dx == 0 and dy == 0:
        return ax, ay, math.hypot(px - ax, py - ay)
        
    # Calculate projection parameter t
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    
    # Clamp t to [0, 1] for segment bounding
    t = max(0.0, min(1.0, t))
    
    proj_x = ax + t * dx
    proj_y = ay + t * dy
    
    dist_deg = math.hypot(px - proj_x, py - proj_y)
    return proj_x, proj_y, dist_deg

class HMMMapMatcher:
    """
    Hidden Markov Model (HMM) based Map Matcher using Viterbi decoding.
    Matches noisy GPS trajectories to a known road network.
    """
    
    def __init__(self, road_network_nodes: List[Tuple[float, float]], road_network_edges: List[Tuple[int, int]], sigma_z: float = 10.0, beta: float = 5.0):
        """
        Initialize the HMM Map Matcher.
        
        Args:
            road_network_nodes: List of (lat, lon) coordinates for road intersections/points.
            road_network_edges: List of (node_idx1, node_idx2) representing road segments.
            sigma_z: Standard deviation of GPS measurement error (meters).
            beta: Transition probability parameter (meters).
        """
        self.nodes = road_network_nodes
        self.edges = road_network_edges
        self.sigma_z = sigma_z
        self.beta = beta
        
        # Viterbi state tracking
        # Each entry in prev_candidates is a dictionary for a candidate:
        # { 'pos': (lat, lon), 'prob': float, 'path': List[(lat, lon)], 'edge_idx': int }
        self.prev_candidates: List[Dict[str, Any]] = []
        self.prev_meas: Tuple[float, float] = None
        
    def get_candidates(self, measured_pos: Tuple[float, float], radius: float = 50.0) -> List[Dict[str, Any]]:
        """
        Find all road segments within `radius` meters of the measured position.
        
        Args:
            measured_pos: (lat, lon) of the current measurement.
            radius: Maximum distance to search for candidates (meters).
            
        Returns:
            List of candidate dictionaries: {'pos': (lat, lon), 'edge_idx': int, 'dist': float}
        """
        candidates = []
        lat, lon = measured_pos
        
        for i, edge in enumerate(self.edges):
            n1_idx, n2_idx = edge
            lat1, lon1 = self.nodes[n1_idx]
            lat2, lon2 = self.nodes[n2_idx]
            
            # Project point to segment (flat earth approximation)
            proj_lat, proj_lon, dist_deg = point_to_segment_projection(lat, lon, lat1, lon1, lat2, lon2)
            
            # Convert distance to meters approximately (haversine from measured to projected)
            dist_m = haversine_distance(lat, lon, proj_lat, proj_lon)
            
            if dist_m <= radius:
                candidates.append({
                    'pos': (proj_lat, proj_lon),
                    'edge_idx': i,
                    'dist': dist_m
                })
                
        return candidates

    def emission_probability(self, dist_m: float) -> float:
        """
        Calculate emission probability P(z_t | r_i)
        
        Args:
            dist_m: Distance between measured position and candidate position (meters).
            
        Returns:
            Probability value.
        """
        prob = (1.0 / (math.sqrt(2 * math.pi) * self.sigma_z)) * math.exp(-0.5 * (dist_m / self.sigma_z) ** 2)
        return prob

    def transition_probability(self, candidate_prev: Tuple[float, float], candidate_curr: Tuple[float, float], meas_prev: Tuple[float, float], meas_curr: Tuple[float, float]) -> float:
        """
        Calculate transition probability P(r_i | r_{i-1})
        
        Args:
            candidate_prev: (lat, lon) of previous candidate.
            candidate_curr: (lat, lon) of current candidate.
            meas_prev: (lat, lon) of previous measurement.
            meas_curr: (lat, lon) of current measurement.
            
        Returns:
            Probability value.
        """
        # Dist route is approx euclidean/haversine for simplicity
        dist_route = haversine_distance(candidate_prev[0], candidate_prev[1], candidate_curr[0], candidate_curr[1])
        dist_meas = haversine_distance(meas_prev[0], meas_prev[1], meas_curr[0], meas_curr[1])
        
        diff = abs(dist_route - dist_meas)
        prob = (1.0 / self.beta) * math.exp(-diff / self.beta)
        return prob

    def viterbi_step(self, measured_pos: Tuple[float, float]) -> Tuple[float, float]:
        """
        Online Viterbi step for streaming data.
        
        Args:
            measured_pos: New (lat, lon) measurement.
            
        Returns:
            The most likely matched position (lat, lon).
        """
        candidates = self.get_candidates(measured_pos, radius=100.0) # slightly larger radius to ensure candidates
        
        if not candidates:
            # If no candidates, fall back to measurement and reset tracking
            self.prev_candidates = []
            self.prev_meas = measured_pos
            return measured_pos
            
        new_state: List[Dict[str, Any]] = []
        
        if not self.prev_candidates:
            # Initialization
            for cand in candidates:
                ep = self.emission_probability(cand['dist'])
                new_state.append({
                    'pos': cand['pos'],
                    'prob': ep,
                    'path': [cand['pos']],
                    'edge_idx': cand['edge_idx']
                })
        else:
            # Induction
            for cand in candidates:
                max_prob = -1.0
                best_path = []
                
                ep = self.emission_probability(cand['dist'])
                
                for prev_cand in self.prev_candidates:
                    tp = self.transition_probability(prev_cand['pos'], cand['pos'], self.prev_meas, measured_pos)
                    prob = prev_cand['prob'] * tp * ep
                    
                    if prob > max_prob:
                        max_prob = prob
                        best_path = prev_cand['path'] + [cand['pos']]
                        
                new_state.append({
                    'pos': cand['pos'],
                    'prob': max_prob,
                    'path': best_path,
                    'edge_idx': cand['edge_idx']
                })
                
        # Normalize probabilities to avoid underflow
        sum_prob = sum(state['prob'] for state in new_state)
        if sum_prob > 0:
            for state in new_state:
                state['prob'] /= sum_prob
                
        self.prev_candidates = new_state
        self.prev_meas = measured_pos
        
        # Find best current state
        best_state = max(new_state, key=lambda x: x['prob'])
        return best_state['pos']
