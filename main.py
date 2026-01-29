from utils import read_video, save_video, get_center_of_bbox, measure_distance, convert_pixels_distance_to_meters, draw_player_stats
from trackers import PlayerTracker, BallTracker
from court_keypoints_detector import CourtKeypointsDetector
from mini_court import MiniCourt
import constants
from copy import deepcopy
import pandas as pd
import cv2
import bisect

def main():
    input_video_path = 'input_videos/input_video.mp4'
    output_video_frames = read_video(input_video_path)
    
    player_tracker = PlayerTracker(model_path='yolov10x')
    ball_tracker = BallTracker(model_path='models/pickleball2_ball_last.pt')

    player_detections = player_tracker.detect_frames(output_video_frames, read_from_stub=True, stub_path='stubs/player_detections.pkl')

    ball_detections = ball_tracker.detect_frames(output_video_frames, read_from_stub=True, stub_path='stubs/ball_detections_point3conf.pkl')
    ball_detections = ball_tracker.interpolate_ball_positions(ball_detections)
    ball_shot_frames = ball_tracker.get_ball_shot_frames(ball_detections)

    court_keypoints_detections = CourtKeypointsDetector('models/keypoints_model3_53_images.pth')
    court_keypoints = court_keypoints_detections.predict(output_video_frames[0])

    player_detections = player_tracker.choose_and_filter_players(court_keypoints, player_detections)
    
    mini_court = MiniCourt(output_video_frames[0])
    player_mini_court_detections, ball_mini_court_detections = mini_court.convert_bounding_boxes_to_mini_court_coordinates(player_detections,  ball_detections, court_keypoints)
    
    player_stats_data = [{
        'frame_num': 0,

        'player_1_number_of_shots': 0,
        'player_1_total_shot_speed': 0,
        'player_1_last_shot_speed': 0,
        'player_1_total_player_speed': 0,
        'player_1_last_player_speed': 0,

        'player_2_number_of_shots': 0,
        'player_2_total_shot_speed': 0,
        'player_2_last_shot_speed': 0,
        'player_2_total_player_speed': 0,
        'player_2_last_player_speed': 0,  

        'player_3_number_of_shots': 0,
        'player_3_total_shot_speed': 0,
        'player_3_last_shot_speed': 0,
        'player_3_total_player_speed': 0,
        'player_3_last_player_speed': 0,
         
        'player_5_number_of_shots': 0,
        'player_5_total_shot_speed': 0,
        'player_5_last_shot_speed': 0,
        'player_5_total_player_speed': 0,
        'player_5_last_player_speed': 0  
    }]

    for ball_shot_index in range(len(ball_shot_frames) - 1):
        start_frame_shot = ball_shot_frames[ball_shot_index]
        end_frame_shot = ball_shot_frames[ball_shot_index + 1]
        ball_shot_time_in_seconds = (end_frame_shot - start_frame_shot) / 24

        ball_traveled_distance_mini_court_pixels = measure_distance(ball_mini_court_detections[start_frame_shot][1], ball_mini_court_detections[end_frame_shot][1])
        ball_traveled_distance_meters = convert_pixels_distance_to_meters(ball_traveled_distance_mini_court_pixels, mini_court.get_mini_court_length(), constants.COURT_LENGTH)
        speed_of_ball = ball_traveled_distance_meters / ball_shot_time_in_seconds

        player_positions = player_mini_court_detections[start_frame_shot]

        player_shot_ball = min(player_positions.keys(), key=lambda player_id: measure_distance(player_positions[player_id], ball_mini_court_detections[start_frame_shot][1]))

        opponent_player_id1, opponent_player_id2 = (1,2) if player_shot_ball == 3 or player_shot_ball == 5 else (3,5)

        distance_covered_by_opponet1_pixels = measure_distance(player_mini_court_detections[start_frame_shot][opponent_player_id1], player_mini_court_detections[end_frame_shot][opponent_player_id1])
        distance_covered_by_opponet1_meters = convert_pixels_distance_to_meters(distance_covered_by_opponet1_pixels, mini_court.get_mini_court_length(), constants.COURT_LENGTH)
        speed_of_opponent1 = distance_covered_by_opponet1_meters / ball_shot_time_in_seconds

        distance_covered_by_opponet2_pixels = measure_distance(player_mini_court_detections[start_frame_shot][opponent_player_id2], player_mini_court_detections[end_frame_shot][opponent_player_id2])
        distance_covered_by_opponet2_meters = convert_pixels_distance_to_meters(distance_covered_by_opponet2_pixels, mini_court.get_mini_court_length(), constants.COURT_LENGTH)
        speed_of_opponent2 = distance_covered_by_opponet2_meters / ball_shot_time_in_seconds

        current_player_stats = deepcopy(player_stats_data[-1])

        current_player_stats['frame_num'] = start_frame_shot
        current_player_stats[f'player_{player_shot_ball}_number_of_shots'] += 1
        current_player_stats[f'player_{player_shot_ball}_total_shot_speed'] += speed_of_ball
        current_player_stats[f'player_{player_shot_ball}_last_shot_speed'] = speed_of_ball

        current_player_stats[f'player_{opponent_player_id1}_total_player_speed'] +=  speed_of_opponent1
        current_player_stats[f'player_{opponent_player_id1}_last_player_speed'] = speed_of_opponent1
        current_player_stats[f'player_{opponent_player_id2}_total_player_speed'] +=  speed_of_opponent2
        current_player_stats[f'player_{opponent_player_id2}_last_player_speed'] = speed_of_opponent2

        player_stats_data.append(current_player_stats)

    player_stats_data_df = pd.DataFrame(player_stats_data)
    frames_df = pd.DataFrame({'frame_num':list(range(len(output_video_frames)))})

    player_stats_data_df = pd.merge(frames_df, player_stats_data_df, on='frame_num', how='left')
    player_stats_data_df = player_stats_data_df.ffill()

    player_stats_data_df['player_1_average_shot_speed'] = player_stats_data_df['player_1_total_shot_speed'] / (player_stats_data_df['player_3_number_of_shots'] + player_stats_data_df['player_5_number_of_shots'])
    player_stats_data_df['player_2_average_shot_speed'] = player_stats_data_df['player_2_total_shot_speed'] / (player_stats_data_df['player_3_number_of_shots'] + player_stats_data_df['player_5_number_of_shots'])
    player_stats_data_df['player_3_average_shot_speed'] = player_stats_data_df['player_3_total_shot_speed'] / (player_stats_data_df['player_1_number_of_shots'] + player_stats_data_df['player_2_number_of_shots'])
    player_stats_data_df['player_5_average_shot_speed'] = player_stats_data_df['player_5_total_shot_speed'] / (player_stats_data_df['player_1_number_of_shots'] + player_stats_data_df['player_2_number_of_shots'])

    player_stats_data_df['player_1_average_player_speed'] = player_stats_data_df['player_1_total_shot_speed'] / (player_stats_data_df['player_3_number_of_shots'] + player_stats_data_df['player_5_number_of_shots'] + 1)
    player_stats_data_df['player_2_average_player_speed'] = player_stats_data_df['player_2_total_shot_speed'] / (player_stats_data_df['player_3_number_of_shots'] + player_stats_data_df['player_5_number_of_shots'] + 1)
    player_stats_data_df['player_3_average_player_speed'] = player_stats_data_df['player_3_total_shot_speed'] / (player_stats_data_df['player_1_number_of_shots'] + player_stats_data_df['player_2_number_of_shots'] + 1)
    player_stats_data_df['player_5_average_player_speed'] = player_stats_data_df['player_5_total_shot_speed'] / (player_stats_data_df['player_1_number_of_shots'] + player_stats_data_df['player_2_number_of_shots'] + 1)
    
    output_video_frames = player_tracker.draw_bboxes(output_video_frames, player_detections)
    output_video_frames = ball_tracker.draw_bboxes(output_video_frames, ball_detections)

    output_video_frames = court_keypoints_detections.draw_keypoints_on_video(output_video_frames, court_keypoints)

    output_video_frames = mini_court.draw_mini_court(output_video_frames)
    output_video_frames = mini_court.draw_points_on_mini_court(output_video_frames, player_mini_court_detections)
    output_video_frames = mini_court.draw_points_on_mini_court(output_video_frames, ball_mini_court_detections, color=(255,0,0))

    output_video_frames = draw_player_stats(output_video_frames, player_stats_data_df)

    for i, frame in enumerate(output_video_frames):
        cv2.putText(frame, f"Frame: {i}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (128,0,128), 2)

    save_video(output_video_frames, "output_videos/output_video3.avi")

if __name__ == "__main__":
    main()