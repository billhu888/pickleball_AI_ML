def get_center_of_bbox(bbox):
    x1, y1, x2, y2 = bbox
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2

    return (center_x, center_y)

def measure_distance(point1, point2):
    return ((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2) ** 0.5

def get_foot_position(bbox):
    x1, y1, x2, y2 = bbox

    return (int((x1+x2)/2), y2)

def get_closest_keypoint_index(foot_position, court_keypoints, keypoint_indices_length):
    closest_distance = float('inf')
    current_keypoint_index = 0

    for keypoint_index in range(int(keypoint_indices_length)):
        keypoint = court_keypoints[keypoint_index*2], court_keypoints[keypoint_index*2+1]
        distance = measure_distance(foot_position, keypoint)

        if distance < closest_distance:
            closest_distance = distance
            current_keypoint_index = keypoint_index

    return current_keypoint_index

def get_height_of_bbox(bbox):
    return bbox[3] - bbox[1]

def measure_xy_distance(p1, p2):
    return p1[0]-p2[0], p1[1]-p2[1]