# object_detect.py
import cv2
from ultralytics import YOLO

# COCO sınıf isimleri (80 sınıf)
COCO_CLASSES = [
    'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light',
    'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow',
    'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
    'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard',
    'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
    'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
    'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone',
    'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear',
    'hair drier', 'toothbrush'
]

# YOLOv8 modelini yükle (ör: 'yolov8n.pt' veya 'yolov8n-seg.pt')
model = YOLO('yolov8n.pt')

def detect_objects(frame):
    """
    Verilen bir frame üzerinde YOLO ile nesne tespiti ve takip (tracking) yapar.
    Her nesne için (class_id, class_name, skor, (x1, y1, x2, y2), track_id) döndürür.
    """
    results = model.track(frame, verbose=False, conf=0.5)
    boxes = results[0].boxes.xyxy.cpu().numpy()  # [x1, y1, x2, y2]
    classes = results[0].boxes.cls.cpu().numpy()  # class id'leri
    scores = results[0].boxes.conf.cpu().numpy()  # skorlar
    track_ids = results[0].boxes.id.cpu().numpy() if hasattr(results[0].boxes, 'id') and results[0].boxes.id is not None else [None]*len(boxes)
    detected = []
    for box, cls, score, track_id in zip(boxes, classes, scores, track_ids):
        class_id = int(cls)
        class_name = COCO_CLASSES[class_id] if class_id < len(COCO_CLASSES) else str(class_id)
        x1, y1, x2, y2 = map(int, box)
        detected.append((class_id, class_name, float(score), (x1, y1, x2, y2), int(track_id) if track_id is not None else None))
    return detected