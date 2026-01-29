from ultralytics import YOLO

model = YOLO('yolov10x')

result = model.track('input_videos/input_video2.mp4', conf = 0.3, save=True)