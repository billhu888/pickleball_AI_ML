from ultralytics import YOLO
import pickle
import pandas as pd
import cv2

class BallTracker:
    def __init__(self, model_path='yolov8x'):
        self.model = YOLO(model_path)
    
    def detect_frames(self, frames, read_from_stub=False, stub_path=None):
        detected_ball_per_frame = []

        if read_from_stub is True and stub_path is not None:
            with open(stub_path, 'rb') as f:
                detected_ball_per_frame = pickle.load(f)

            return detected_ball_per_frame
        
        for frame in frames:
            ball_dict = self.detect_frame(frame)
            detected_ball_per_frame.append(ball_dict)

        if stub_path is not None:
            with open(stub_path, 'wb') as f:
                pickle.dump(detected_ball_per_frame, f)

        return detected_ball_per_frame
    
    def detect_frame(self, frame):
        results = self.model.predict(frame, conf=0.15)[0]
        ball_dict= {}

        for box in results.boxes:
            result = box.xyxy.tolist()[0]
            ball_dict[1] = result

        return ball_dict

    def interpolate_ball_positions(self, ball_detections):
        ball_positions = [x.get(1,[]) for x in ball_detections]
        df_ball_positions = pd.DataFrame(ball_positions, columns=['x1', 'y1', 'x2', 'y2'])

        df_ball_positions = df_ball_positions.interpolate()
        df_ball_positions = df_ball_positions.bfill()

        ball_positions = [{1:x} for x in df_ball_positions.to_numpy().tolist()]

        return ball_positions
    
    def get_ball_shot_frames(self, ball_detections):
        ball_positions = [x.get(1,[]) for x in ball_detections]
        ball_positions = pd.DataFrame(ball_positions, columns=['x1', 'y1', 'x2', 'y2'])
        ball_positions['mid_y'] = (ball_positions['y1'] + ball_positions['y2']) / 2
        ball_positions['delta_y'] = ball_positions['mid_y'].diff()
        minimum_change_frames_for_hit = 12
        ball_positions['ball_hit'] = 0

        for i in range(int(minimum_change_frames_for_hit*1.25), len(ball_positions) - int(minimum_change_frames_for_hit*1.25)):
            negative_position_change = ball_positions['delta_y'].iloc[i] > 0 and ball_positions['delta_y'].iloc[i+1] < 0
            positive_position_change = ball_positions['delta_y'].iloc[i] < 0 and ball_positions['delta_y'].iloc[i+1] > 0

            if negative_position_change or positive_position_change:
                frames_change_direction_count = 0

                for frame in range(i-int(minimum_change_frames_for_hit*1.25), i):
                    negative_position_change_previous_frame = ball_positions['delta_y'].iloc[i] > 0 and ball_positions['delta_y'].iloc[frame] > 0
                    positive_position_change_previous_frame = ball_positions['delta_y'].iloc[i] < 0 and ball_positions['delta_y'].iloc[frame] < 0

                    if negative_position_change and negative_position_change_previous_frame:
                        frames_change_direction_count += 1
                    if positive_position_change and positive_position_change_previous_frame:
                        frames_change_direction_count += 1

                for frame in range(i+1, i + int(minimum_change_frames_for_hit*1.25)):
                    negative_position_change_following_frame = ball_positions['delta_y'].iloc[i] > 0 and ball_positions['delta_y'].iloc[frame] < 0
                    positive_position_change_following_frame = ball_positions['delta_y'].iloc[i] < 0 and ball_positions['delta_y'].iloc[frame] > 0

                    if negative_position_change and negative_position_change_following_frame:
                        frames_change_direction_count += 1
                    if positive_position_change and positive_position_change_following_frame:
                        frames_change_direction_count += 1

                if frames_change_direction_count >= minimum_change_frames_for_hit*2:
                    ball_positions['ball_hit'].at[i] = 1

        frame_nums_with_ball_hits = ball_positions[ball_positions['ball_hit'] == 1].index.tolist()

        return frame_nums_with_ball_hits

    def draw_bboxes(self, frames, ball_detections):
        output_video_frames = []

        for frame, ball_dict in zip(frames, ball_detections):
            for track_id, bbox in ball_dict.items():
                x1, y1, x2, y2 = map(int, bbox)
                cv2.putText(frame, f"Ball {track_id}", (int(bbox[0]), int(bbox[1] - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
                # cv2.circle(frame, (int((x1+x2)/2), int(y2)), (int((x2-x1)/2)), (0, 0, 255), 2)
                cv2.ellipse(frame, (int((x1+x2)/2), int(y2)), (int((x2-x1)/2), int((x2-x1)/8)), angle=0, startAngle=0, endAngle=360, color=(255, 0, 0), thickness=2)

            output_video_frames.append(frame)

        return output_video_frames