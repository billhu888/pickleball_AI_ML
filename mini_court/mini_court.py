<<<<<<< HEAD
import constants
import utils
import cv2
import numpy as np

class MiniCourt():
    def __init__(self, frame):
        self.drawing_rectangle_width = 250
        self.drawing_rectangle_height = 500
        self.buffer = 50
        self.padding_court = 20

        self.set_canvas_background_box_positions(frame)
        self.set_mini_court_position()
        self.set_court_drawing_keypoints()
        self.set_court_lines()

    def set_canvas_background_box_positions(self, frame):
        self.start_x = self.buffer
        self.start_y = self.buffer
        self.end_x = self.start_x + self.drawing_rectangle_width
        self.end_y = self.start_y + self.drawing_rectangle_height

    def set_mini_court_position(self):
        self.court_start_x = self.start_x + self.padding_court
        self.court_start_y = self.start_y + self.padding_court
        self.court_end_x = self.end_x - self.padding_court
        self.count_end_y = self.end_y - self.padding_court
        self.court_drawing_width = self.court_end_x - self.court_start_x
        self.court_drawing_height = self.count_end_y - self.court_start_y

    def set_court_drawing_keypoints(self):
        self.key_points_coordinates = [0] * 24

        # Point 0
        self.key_points_coordinates[0] = int(self.court_start_x)
        self.key_points_coordinates[1] = int(self.court_start_y)
        # Point 1
        self.key_points_coordinates[2] = self.key_points_coordinates[0] + self.court_drawing_width/2
        self.key_points_coordinates[3] = self.key_points_coordinates[1]
        # Point 2
        self.key_points_coordinates[4] = int(self.court_end_x)
        self.key_points_coordinates[5] = self.key_points_coordinates[1]
        # Point 3
        self.key_points_coordinates[6] = self.key_points_coordinates[4]
        self.key_points_coordinates[7] = self.key_points_coordinates[1] + utils.convert_meters_to_pixel_distance(constants.START_TO_FIRST_KITCHEN, constants.COURT_WIDTH, self.court_drawing_width)
        # Point 4
        self.key_points_coordinates[8] = self.key_points_coordinates[2]
        self.key_points_coordinates[9] = self.key_points_coordinates[7]
        # Point 5
        self.key_points_coordinates[10] = self.key_points_coordinates[0] 
        self.key_points_coordinates[11] = self.key_points_coordinates[7]
        # Point 6
        self.key_points_coordinates[12] = self.key_points_coordinates[0]
        self.key_points_coordinates[13] = self.key_points_coordinates[1] + utils.convert_meters_to_pixel_distance(constants.START_TO_SECOND_KITCHEN, constants.COURT_WIDTH, self.court_drawing_width)
        # Point 7
        self.key_points_coordinates[14] = self.key_points_coordinates[2]
        self.key_points_coordinates[15] = self.key_points_coordinates[13]
        # Point 8
        self.key_points_coordinates[16] = self.key_points_coordinates[4]
        self.key_points_coordinates[17] = self.key_points_coordinates[13]
        # Point 9
        self.key_points_coordinates[18] = self.key_points_coordinates[4]
        self.key_points_coordinates[19] = int(self.count_end_y)
        # Point 10
        self.key_points_coordinates[20] = self.key_points_coordinates[2]
        self.key_points_coordinates[21] = self.key_points_coordinates[19]
        # Point 11
        self.key_points_coordinates[22] = self.key_points_coordinates[0]
        self.key_points_coordinates[23] = self.key_points_coordinates[19]

    def set_court_lines(self):
        self.lines = [
            (0,2),
            (0,11),
            (2,9),
            (11,9),
            (5,3),
            (6,8),
            (1,4),
            (7,10)
        ]

    def get_mini_court_length(self):
        return self.court_drawing_height

    def get_mini_court_coordinates(self, foot_position, foot_closest_keypoint_coordinates, foot_closest_keypoint_index, player_height_pixels, player_height_meters, test_loop):
        distance_from_x_actual_court_pixels, distance_from_y_actual_court_pixels = utils.measure_xy_distance(foot_position, foot_closest_keypoint_coordinates)

        distance_from_keypoint_x_actual_court_meters = utils.convert_pixels_distance_to_meters(distance_from_x_actual_court_pixels, player_height_pixels, player_height_meters)
        distance_from_keypoint_y_actual_court_meters = utils.convert_pixels_distance_to_meters(distance_from_y_actual_court_pixels, player_height_pixels, player_height_meters)
        
        distance_from_keypoint_x_mini_court_pixels = utils.convert_meters_to_pixel_distance(distance_from_keypoint_x_actual_court_meters, constants.COURT_LENGTH, self.court_drawing_height)
        distance_from_keypoint_y_mini_court_pixels = utils.convert_meters_to_pixel_distance(distance_from_keypoint_y_actual_court_meters, constants.COURT_LENGTH, self.court_drawing_height)
        
        closest_mini_court_keypoint = (self.key_points_coordinates[foot_closest_keypoint_index*2], self.key_points_coordinates[foot_closest_keypoint_index*2 + 1])
        
        mini_court_player_position = (closest_mini_court_keypoint[0] + distance_from_keypoint_x_mini_court_pixels, closest_mini_court_keypoint[1] + distance_from_keypoint_y_mini_court_pixels)
        
        return mini_court_player_position

    def convert_bounding_boxes_to_mini_court_coordinates(self, player_detections, ball_detections, court_keypoints):
        player_heights = {
            1: constants.PLAYER_1_HEIGHT_METERS,
            2: constants.PLAYER_2_HEIGHT_METERS,
            3: constants.PLAYER_3_HEIGHT_METERS,
            5: constants.PLAYER_5_HEIGHT_METERS,
        }

        output_player_boxes = []
        output_ball_boxes = []

        test_loop = 0

        for frame_num, player_bbox in enumerate(player_detections):
            ball_box = ball_detections[frame_num][1]
            ball_position = utils.get_center_of_bbox(ball_box)
            player_id_closest_to_ball = min(player_bbox.keys(), key=lambda x: utils.measure_distance(ball_position, utils.get_center_of_bbox(player_bbox[x])))
            output_player_bboxes_dict = {}

            for player_id, bbox in player_bbox.items():
                foot_position = utils.get_foot_position(bbox)

                foot_closest_keypoint_index = utils.get_closest_keypoint_index(foot_position, court_keypoints, len(self.key_points_coordinates)/2)
                foot_closest_keypoint_coordinates = (court_keypoints[foot_closest_keypoint_index*2], court_keypoints[foot_closest_keypoint_index*2+1])

                frame_index_min = max(0, frame_num - 20)
                frame_index_max = min(len(player_detections), frame_num+50)

                bboxes_heights_in_pixels = []

                for i in range (frame_index_min, frame_index_max):
                    bbox_height = utils.get_height_of_bbox(player_detections[i][player_id]) 
                    bboxes_heights_in_pixels.append(bbox_height)

                max_player_height_in_pixels = max(bboxes_heights_in_pixels)

                mini_court_player_position = self.get_mini_court_coordinates(foot_position, foot_closest_keypoint_coordinates, foot_closest_keypoint_index, max_player_height_in_pixels, player_heights[player_id], test_loop)
                
                output_player_bboxes_dict[player_id] = mini_court_player_position

                if player_id == player_id_closest_to_ball:
                    ball_closest_keypoint_index = utils.get_closest_keypoint_index(foot_position, court_keypoints, len(self.key_points_coordinates)/2)
                    ball_closest_keypoint_coordinates = (court_keypoints[ball_closest_keypoint_index*2], court_keypoints[ball_closest_keypoint_index*2+1])

                    mini_court_ball_coordinates = self.get_mini_court_coordinates(foot_position, ball_closest_keypoint_coordinates, ball_closest_keypoint_index, max_player_height_in_pixels, player_heights[player_id], test_loop)
                    output_ball_boxes.append({1:mini_court_ball_coordinates})

            output_player_boxes.append(output_player_bboxes_dict)

        return output_player_boxes, output_ball_boxes

    def draw_background_rectangle(self, frame):
        shapes = np.zeros_like(frame, np.uint8)
        # Draw the rectangle
        cv2.rectangle(shapes, (self.start_x, self.start_y), (self.end_x, self.end_y), (255, 255, 255), cv2.FILLED)
        out = frame.copy()
        alpha = 0.5
        mask = shapes.astype(bool)
        out[mask] = cv2.addWeighted(frame, alpha, shapes, 1 - alpha, 0)[mask]

        return out
    
    def draw_court(self, frame):
        for i in range(0, len(self.key_points_coordinates), 2):
            x = int(self.key_points_coordinates[i])
            y = int(self.key_points_coordinates[i+1])
            cv2.circle(frame, (x,y), 5, (0,0,255), -1)

        for line in self.lines:
            start_point = (int(self.key_points_coordinates[line[0]*2]), int(self.key_points_coordinates[line[0]*2+1]))
            end_point = (int(self.key_points_coordinates[line[1]*2]), int(self.key_points_coordinates[line[1]*2+1]))
            cv2.line(frame, start_point, end_point, (0,0,0), 2)
        
        net_start_point = (int(self.key_points_coordinates[0]), int((self.key_points_coordinates[11] + self.key_points_coordinates[13])/2))
        net_end_point = (int(self.key_points_coordinates[4]), int((self.key_points_coordinates[7] + self.key_points_coordinates[17])/2))
        cv2.line(frame, net_start_point, net_end_point, (255,0,0), 2)

        return frame

    def draw_mini_court(self, frames):
        output_frames = []

        for frame in frames:
            frame = self.draw_background_rectangle(frame)
            frame = self.draw_court(frame)
            output_frames.append(frame)

        return output_frames
    
    def draw_points_on_mini_court(self, frames, positions, color=(0,255,0)):
        for frame_num, frame in enumerate(frames):
            for _, position in positions[frame_num].items():
                x,y = position
                x=int(x)
                y=int(y)
                cv2.circle(frame, (x,y), 5, color, -1)
        
=======
import constants
import utils
import cv2
import numpy as np

class MiniCourt():
    def __init__(self, frame):
        self.drawing_rectangle_width = 250
        self.drawing_rectangle_height = 500
        self.buffer = 50
        self.padding_court = 20

        self.set_canvas_background_box_positions(frame)
        self.set_mini_court_position()
        self.set_court_drawing_keypoints()
        self.set_court_lines()

    def set_canvas_background_box_positions(self, frame):
        self.start_x = self.buffer
        self.start_y = self.buffer
        self.end_x = self.start_x + self.drawing_rectangle_width
        self.end_y = self.start_y + self.drawing_rectangle_height

    def set_mini_court_position(self):
        self.court_start_x = self.start_x + self.padding_court
        self.court_start_y = self.start_y + self.padding_court
        self.court_end_x = self.end_x - self.padding_court
        self.count_end_y = self.end_y - self.padding_court
        self.court_drawing_width = self.court_end_x - self.court_start_x
        self.court_drawing_height = self.count_end_y - self.court_start_y

    def set_court_drawing_keypoints(self):
        self.key_points_coordinates = [0] * 24

        # Point 0
        self.key_points_coordinates[0] = int(self.court_start_x)
        self.key_points_coordinates[1] = int(self.court_start_y)
        # Point 1
        self.key_points_coordinates[2] = self.key_points_coordinates[0] + self.court_drawing_width/2
        self.key_points_coordinates[3] = self.key_points_coordinates[1]
        # Point 2
        self.key_points_coordinates[4] = int(self.court_end_x)
        self.key_points_coordinates[5] = self.key_points_coordinates[1]
        # Point 3
        self.key_points_coordinates[6] = self.key_points_coordinates[4]
        self.key_points_coordinates[7] = self.key_points_coordinates[1] + utils.convert_meters_to_pixel_distance(constants.START_TO_FIRST_KITCHEN, constants.COURT_WIDTH, self.court_drawing_width)
        # Point 4
        self.key_points_coordinates[8] = self.key_points_coordinates[2]
        self.key_points_coordinates[9] = self.key_points_coordinates[7]
        # Point 5
        self.key_points_coordinates[10] = self.key_points_coordinates[0] 
        self.key_points_coordinates[11] = self.key_points_coordinates[7]
        # Point 6
        self.key_points_coordinates[12] = self.key_points_coordinates[0]
        self.key_points_coordinates[13] = self.key_points_coordinates[1] + utils.convert_meters_to_pixel_distance(constants.START_TO_SECOND_KITCHEN, constants.COURT_WIDTH, self.court_drawing_width)
        # Point 7
        self.key_points_coordinates[14] = self.key_points_coordinates[2]
        self.key_points_coordinates[15] = self.key_points_coordinates[13]
        # Point 8
        self.key_points_coordinates[16] = self.key_points_coordinates[4]
        self.key_points_coordinates[17] = self.key_points_coordinates[13]
        # Point 9
        self.key_points_coordinates[18] = self.key_points_coordinates[4]
        self.key_points_coordinates[19] = int(self.count_end_y)
        # Point 10
        self.key_points_coordinates[20] = self.key_points_coordinates[2]
        self.key_points_coordinates[21] = self.key_points_coordinates[19]
        # Point 11
        self.key_points_coordinates[22] = self.key_points_coordinates[0]
        self.key_points_coordinates[23] = self.key_points_coordinates[19]

    def set_court_lines(self):
        self.lines = [
            (0,2),
            (0,11),
            (2,9),
            (11,9),
            (5,3),
            (6,8),
            (1,4),
            (7,10)
        ]

    def get_mini_court_length(self):
        return self.court_drawing_height

    def get_mini_court_coordinates(self, foot_position, foot_closest_keypoint_coordinates, foot_closest_keypoint_index, player_height_pixels, player_height_meters, test_loop):
        distance_from_x_actual_court_pixels, distance_from_y_actual_court_pixels = utils.measure_xy_distance(foot_position, foot_closest_keypoint_coordinates)

        distance_from_keypoint_x_actual_court_meters = utils.convert_pixels_distance_to_meters(distance_from_x_actual_court_pixels, player_height_pixels, player_height_meters)
        distance_from_keypoint_y_actual_court_meters = utils.convert_pixels_distance_to_meters(distance_from_y_actual_court_pixels, player_height_pixels, player_height_meters)
        
        distance_from_keypoint_x_mini_court_pixels = utils.convert_meters_to_pixel_distance(distance_from_keypoint_x_actual_court_meters, constants.COURT_LENGTH, self.court_drawing_height)
        distance_from_keypoint_y_mini_court_pixels = utils.convert_meters_to_pixel_distance(distance_from_keypoint_y_actual_court_meters, constants.COURT_LENGTH, self.court_drawing_height)
        
        closest_mini_court_keypoint = (self.key_points_coordinates[foot_closest_keypoint_index*2], self.key_points_coordinates[foot_closest_keypoint_index*2 + 1])
        
        mini_court_player_position = (closest_mini_court_keypoint[0] + distance_from_keypoint_x_mini_court_pixels, closest_mini_court_keypoint[1] + distance_from_keypoint_y_mini_court_pixels)
        
        return mini_court_player_position

    def convert_bounding_boxes_to_mini_court_coordinates(self, player_detections, ball_detections, court_keypoints):
        player_heights = {
            1: constants.PLAYER_1_HEIGHT_METERS,
            2: constants.PLAYER_2_HEIGHT_METERS,
            3: constants.PLAYER_3_HEIGHT_METERS,
            5: constants.PLAYER_5_HEIGHT_METERS,
        }

        output_player_boxes = []
        output_ball_boxes = []

        test_loop = 0

        for frame_num, player_bbox in enumerate(player_detections):
            ball_box = ball_detections[frame_num][1]
            ball_position = utils.get_center_of_bbox(ball_box)
            player_id_closest_to_ball = min(player_bbox.keys(), key=lambda x: utils.measure_distance(ball_position, utils.get_center_of_bbox(player_bbox[x])))
            output_player_bboxes_dict = {}

            for player_id, bbox in player_bbox.items():
                foot_position = utils.get_foot_position(bbox)

                foot_closest_keypoint_index = utils.get_closest_keypoint_index(foot_position, court_keypoints, len(self.key_points_coordinates)/2)
                foot_closest_keypoint_coordinates = (court_keypoints[foot_closest_keypoint_index*2], court_keypoints[foot_closest_keypoint_index*2+1])

                frame_index_min = max(0, frame_num - 20)
                frame_index_max = min(len(player_detections), frame_num+50)

                bboxes_heights_in_pixels = []

                for i in range (frame_index_min, frame_index_max):
                    bbox_height = utils.get_height_of_bbox(player_detections[i][player_id]) 
                    bboxes_heights_in_pixels.append(bbox_height)

                max_player_height_in_pixels = max(bboxes_heights_in_pixels)

                mini_court_player_position = self.get_mini_court_coordinates(foot_position, foot_closest_keypoint_coordinates, foot_closest_keypoint_index, max_player_height_in_pixels, player_heights[player_id], test_loop)
                
                output_player_bboxes_dict[player_id] = mini_court_player_position

                if player_id == player_id_closest_to_ball:
                    ball_closest_keypoint_index = utils.get_closest_keypoint_index(foot_position, court_keypoints, len(self.key_points_coordinates)/2)
                    ball_closest_keypoint_coordinates = (court_keypoints[ball_closest_keypoint_index*2], court_keypoints[ball_closest_keypoint_index*2+1])

                    mini_court_ball_coordinates = self.get_mini_court_coordinates(foot_position, ball_closest_keypoint_coordinates, ball_closest_keypoint_index, max_player_height_in_pixels, player_heights[player_id], test_loop)
                    output_ball_boxes.append({1:mini_court_ball_coordinates})

            output_player_boxes.append(output_player_bboxes_dict)

        return output_player_boxes, output_ball_boxes

    def draw_background_rectangle(self, frame):
        shapes = np.zeros_like(frame, np.uint8)
        # Draw the rectangle
        cv2.rectangle(shapes, (self.start_x, self.start_y), (self.end_x, self.end_y), (255, 255, 255), cv2.FILLED)
        out = frame.copy()
        alpha = 0.5
        mask = shapes.astype(bool)
        out[mask] = cv2.addWeighted(frame, alpha, shapes, 1 - alpha, 0)[mask]

        return out
    
    def draw_court(self, frame):
        for i in range(0, len(self.key_points_coordinates), 2):
            x = int(self.key_points_coordinates[i])
            y = int(self.key_points_coordinates[i+1])
            cv2.circle(frame, (x,y), 5, (0,0,255), -1)

        for line in self.lines:
            start_point = (int(self.key_points_coordinates[line[0]*2]), int(self.key_points_coordinates[line[0]*2+1]))
            end_point = (int(self.key_points_coordinates[line[1]*2]), int(self.key_points_coordinates[line[1]*2+1]))
            cv2.line(frame, start_point, end_point, (0,0,0), 2)
        
        net_start_point = (int(self.key_points_coordinates[0]), int((self.key_points_coordinates[11] + self.key_points_coordinates[13])/2))
        net_end_point = (int(self.key_points_coordinates[4]), int((self.key_points_coordinates[7] + self.key_points_coordinates[17])/2))
        cv2.line(frame, net_start_point, net_end_point, (255,0,0), 2)

        return frame

    def draw_mini_court(self, frames):
        output_frames = []

        for frame in frames:
            frame = self.draw_background_rectangle(frame)
            frame = self.draw_court(frame)
            output_frames.append(frame)

        return output_frames
    
    def draw_points_on_mini_court(self, frames, positions, color=(0,255,0)):
        for frame_num, frame in enumerate(frames):
            for _, position in positions[frame_num].items():
                x,y = position
                x=int(x)
                y=int(y)
                cv2.circle(frame, (x,y), 5, color, -1)
        
>>>>>>> 0b64c56eceabb797502eeec5287bdfc65d808203
        return frames