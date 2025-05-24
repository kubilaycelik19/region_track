import cv2
from face_recog import FaceRecognition
from object_detect import detect_objects
from draw_zone import draw_zones_on_stream, draw_zones_on_frame

def intersection_area(boxA, boxB):
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    interW = max(0, xB - xA)
    interH = max(0, yB - yA)
    return interW * interH

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Kamera açılamadı.")
    exit()

fr = FaceRecognition()

# Zone çizimi için fonksiyonu çağır
zones = draw_zones_on_stream(cap)
print('Çizilen zone:', zones)

# Artık ana akışa geç
while True:
    ret, frame = cap.read()
    if not ret:
        print("Kare alınamadı.")
        break
    frame = cv2.flip(frame, 1)
    detected_objects = detect_objects(frame)

    # Zone'ları şeffaf dolgu ve kenarlıkla çiz
    frame = draw_zones_on_frame(frame, zones)

    for class_id, class_name, score, (x1, y1, x2, y2), track_id in detected_objects:
        track_text = f'ID:{track_id}' if track_id is not None else ''
        if class_id == 0:  # person
            for rect in zones:
                (zx1, zy1), (zx2, zy2) = rect
                zone_xmin, zone_xmax = min(zx1, zx2), max(zx1, zx2)
                zone_ymin, zone_ymax = min(zy1, zy2), max(zy1, zy2)
                obj_area = (x2 - x1) * (y2 - y1)
                inter_area = intersection_area((x1, y1, x2, y2), (zone_xmin, zone_ymin, zone_xmax, zone_ymax))
                if obj_area > 0 and (inter_area / obj_area) >= 0.7:
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
                    cv2.putText(frame, f'{class_name} {score:.2f} {track_text}', (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1)
                    person_crop = frame[y1:y2, x1:x2]
                    faces = fr.recognize_faces(person_crop)
                    label = class_name
                    if faces:
                        isim, guven, (top, right, bottom, left) = faces[0]
                        label = f'{isim} {guven}'
                        abs_top = y1 + top
                        abs_right = x1 + right
                        abs_bottom = y1 + bottom
                        abs_left = x1 + left
                        cv2.rectangle(frame, (abs_left, abs_top), (abs_right, abs_bottom), (255,0,0), 2)
                        cv2.putText(frame, label, (abs_left, abs_top-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,0), 1)
        else:
            for rect in zones:
                (zx1, zy1), (zx2, zy2) = rect
                zone_xmin, zone_xmax = min(zx1, zx2), max(zx1, zx2)
                zone_ymin, zone_ymax = min(zy1, zy2), max(zy1, zy2)
                obj_area = (x2 - x1) * (y2 - y1)
                inter_area = intersection_area((x1, y1, x2, y2), (zone_xmin, zone_ymin, zone_xmax, zone_ymax))
                if obj_area > 0 and (inter_area / obj_area) >= 0.7:
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0,0,255), 2)
                    cv2.putText(frame, f'{class_name} {score:.2f} {track_text}', (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 1)

    cv2.imshow('Canli Akis', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
cap.release()
cv2.destroyAllWindows()
