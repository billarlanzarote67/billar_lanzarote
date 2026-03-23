"""
Starter stub for future rack detection.

This is a deliberately simple heuristic base:
- enough balls
- close enough together
- later replace with proper top-down detection + cluster logic
"""

def detect_rack_from_ball_centers(ball_centers, min_balls=9, max_spread_px=180):
    if len(ball_centers) < min_balls:
        return False

    xs = [p[0] for p in ball_centers]
    ys = [p[1] for p in ball_centers]
    spread = max(max(xs) - min(xs), max(ys) - min(ys))
    return spread <= max_spread_px

if __name__ == "__main__":
    sample = [(600, 300), (620, 315), (640, 330), (660, 345), (680, 360),
              (640, 360), (620, 345), (660, 315), (650, 338)]
    print("Rack detected?", detect_rack_from_ball_centers(sample))
