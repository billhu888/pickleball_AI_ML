from ultralytics import YOLO
import cv2
import pickle
import sys
sys.path.append('../')
from utils import measure_distance, get_center_of_bbox

class PlayerTracker:
    def __init__(self, model_path='yolov8x'):
        self.model = YOLO(model_path)

    def detect_frames(self, frames, read_from_stub=False, stub_path=None):
        detected_players_per_frame = []

        if read_from_stub is True and stub_path is not None:
            with open(stub_path, 'rb') as f:
                detected_players_per_frame = pickle.load(f)

            return detected_players_per_frame
        
        for frame in frames:
            player_dict = self.detect_frame(frame)
            detected_players_per_frame.append(player_dict)

        if stub_path is not None:
            with open(stub_path, 'wb') as f:
                pickle.dump(detected_players_per_frame, f)

    def detect_frame(self, frame):
        results = self.model.track(frame, persist=True)[0]
        id_name_dict = results.names
        player_dict= {}

        for box in results.boxes:
            track_id = int(box.id.tolist()[0])
            result = box.xyxy.tolist()[0]
            object_cls_id = box.cls.tolist()[0]
            object_cls_name = id_name_dict[object_cls_id]

            if object_cls_name == 'person':
                player_dict[track_id] = result

        return player_dict
    
    def choose_and_filter_players(self, court_keypoints, player_detections):
        player_detections_first_frame = player_detections[0]
        chosen_players = self.choose_players(court_keypoints, player_detections_first_frame)
        filtered_player_detections = []

        for player_dict in player_detections:
            filtered_dict = {track_id: bbox for track_id, bbox in player_dict.items() if track_id in chosen_players}
            filtered_player_detections.append(filtered_dict)

        return filtered_player_detections

    def choose_players(self, court_keypoints, player_detections_first_frame):
        distances = []

        for track_id, bbox in player_detections_first_frame.items():
            player_center = get_center_of_bbox(bbox)
            min_distance = float('inf')

            for i in range(0, len(court_keypoints), 2):
                court_keypoint = (court_keypoints[i], court_keypoints[i+1])
                distance = measure_distance(player_center, court_keypoint)

                if distance < min_distance:
                    min_distance = distance

            distances.append((track_id, min_distance))
        
        distances.sort(key=lambda x: x[1])
        chosen_players = [distances[0][0], distances[1][0], distances[2][0], distances[3][0]]

        return chosen_players
    
    def draw_bboxes(self, frames, player_detections):
        output_video_frames = []

        for frame, player_dict in zip(frames, player_detections):
            for track_id, bbox in player_dict.items():
                x1, y1, x2, y2 = map(int, bbox)
                # cv2.putText(frame, f"Player ID: {track_id}", (int(bbox[0]), int(bbox[1] - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                # cv2.circle(frame, (int((x1+x2)/2), int(y2)), (int((x2-x1)/2)), (0, 0, 255), 2)
                cv2.ellipse(frame, (int((x1+x2)/2), int(y2)), (int((x2-x1)/2), int((x2-x1)/8)), angle=0, startAngle=0, endAngle=360, color=(0, 255, 0), thickness=2)

                if (track_id == 1) or (track_id == 2):
                    cv2.putText(frame, f"Player {track_id}", (int(bbox[0]), int(bbox[3] + 40)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                if (track_id == 3) or (track_id == 5):
                    cv2.putText(frame, f"Player {track_id}", (int(bbox[0]), int(bbox[1] - 15)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            output_video_frames.append(frame)

            # for track_id, bbox in player_dict.items():
            #     x1, y1, x2, y2 = bbox
            #     cv2.putText(frame, f"Player ID: {track_id}", (int(bbox[0]), int(bbox[1] - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            #     cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 2)

            # output_video_frames.append(frame)

        return output_video_frames