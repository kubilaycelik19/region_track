import cv2
from face_recog import FaceRecognition
from object_detect import detect_objects

# Zone çizim fonksiyonu artık burada

def intersection_area(boxA, boxB):
    # boxA ve boxB: (x1, y1, x2, y2)
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    interW = max(0, xB - xA)
    interH = max(0, yB - yA)
    return interW * interH

def draw_zones_on_window(window_name, frame):
    drawing = False
    ix, iy = -1, -1
    zone_rects = []
    zone = None

    def draw_rectangle(event, x, y, flags, param):
        nonlocal ix, iy, drawing, zone_rects, zone
        if event == cv2.EVENT_LBUTTONDOWN:
            drawing = True
            ix, iy = x, y
        elif event == cv2.EVENT_LBUTTONUP:
            drawing = False
            zone = (ix, iy, x, y)
            zone_rects.append((ix, iy, x, y))

    cv2.imshow(window_name, frame)
    cv2.setMouseCallback(window_name, draw_rectangle)

    while True:
        temp = frame.copy()
        for zx1, zy1, zx2, zy2 in zone_rects:
            zone_xmin, zone_xmax = min(zx1, zx2), max(zx1, zx2)
            zone_ymin, zone_ymax = min(zy1, zy2), max(zy1, zy2)
            cv2.rectangle(temp, (zone_xmin, zone_ymin), (zone_xmax, zone_ymax), (0,255,255), 2)
        cv2.imshow(window_name, temp)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == ord('s'):
            break
    cv2.setMouseCallback(window_name, lambda *a : None)
    return zone_rects

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Kamera açılamadı.")
    exit()

fr = FaceRecognition()

# İlk frame ile zone çizdir
while True:
    ret, frame = cap.read()
    if not ret:
        print("Kare alınamadı.")
        exit()
    frame = cv2.flip(frame, 1)
    break
zones = draw_zones_on_window('Object + Face Recognition', frame)
print('Çizilen zone:', zones)
cap.release()

while True:
    ret, frame = cap.read()
    if not ret:
        print("Kare alınamadı.")
        break
    frame = cv2.flip(frame, 1)
    detected_objects = detect_objects(frame)

    # Zone'ları çiz
    for zx1, zy1, zx2, zy2 in zones:
        zone_xmin, zone_xmax = min(zx1, zx2), max(zx1, zx2)
        zone_ymin, zone_ymax = min(zy1, zy2), max(zy1, zy2)
        cv2.rectangle(frame, (zone_xmin, zone_ymin), (zone_xmax, zone_ymax), (0,255,255), 2)

    for class_id, class_name, score, (x1, y1, x2, y2) in detected_objects:
        if class_id == 0:  # person
            for zx1, zy1, zx2, zy2 in zones:
                zone_xmin, zone_xmax = min(zx1, zx2), max(zx1, zx2)
                zone_ymin, zone_ymax = min(zy1, zy2), max(zy1, zy2)
                obj_area = (x2 - x1) * (y2 - y1)
                #zone_area = (zone_xmax - zone_xmin) * (zone_ymax - zone_ymin)
                inter_area = intersection_area((x1, y1, x2, y2), (zone_xmin, zone_ymin, zone_xmax, zone_ymax))
                if obj_area > 0 and (inter_area / obj_area) >= 0.7:
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
                    cv2.putText(frame, f'{class_name} {score:.2f}', (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1)
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
            for zx1, zy1, zx2, zy2 in zones:
                zone_xmin, zone_xmax = min(zx1, zx2), max(zx1, zx2)
                zone_ymin, zone_ymax = min(zy1, zy2), max(zy1, zy2)
                obj_area = (x2 - x1) * (y2 - y1)
                #zone_area = (zone_xmax - zone_xmin) * (zone_ymax - zone_ymin)
                inter_area = intersection_area((x1, y1, x2, y2), (zone_xmin, zone_ymin, zone_xmax, zone_ymax))
                if obj_area > 0 and (inter_area / obj_area) >= 0.7:
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0,0,255), 2)
                    cv2.putText(frame, f'{class_name} {score:.2f}', (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 1)

    cv2.imshow('Object + Face Recognition', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
cap.release()
cv2.destroyAllWindows()
