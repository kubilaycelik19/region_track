import cv2
from face_recog import FaceRecognition
from object_detect import detect_objects
from draw_zone import draw_zones_on_stream, draw_polygons_on_frame
import numpy as np

def intersection_area_poly(poly, box):
    # Polygon ve dikdörtgenin kesişim alanı (yaklaşık):
    # Polygonu maske olarak kullanıp, box içindeki alanı sayabilirsin.
    mask = np.zeros((box[3], box[2]), dtype=np.uint8)
    shifted_poly = [ (x-box[0], y-box[1]) for (x,y) in poly ]
    cv2.fillPoly(mask, [np.array(shifted_poly, np.int32)], 1)
    return np.sum(mask)

cap = cv2.VideoCapture("test_video.mp4")
if not cap.isOpened():
    print("Kamera açılamadı.")
    exit()

fr = FaceRecognition()

# Zone çizimi için fonksiyonu çağır
zones, zone_labels = draw_zones_on_stream(cap)
print('Çizilen zone:', zones)
print('Zone etiketleri:', zone_labels)

# Artık ana akışa geç
while True:
    ret, frame = cap.read()
    if not ret:
        print("Kare alınamadı.")
        break
    frame = cv2.flip(frame, 1)
    detected_objects = detect_objects(frame)

    # Zone'ları şeffaf dolgu ve kenarlıkla çiz
    frame = draw_polygons_on_frame(frame, zones, labels=zone_labels)

    for class_id, class_name, score, (x1, y1, x2, y2), track_id in detected_objects:
        track_text = f'ID:{track_id}' if track_id is not None else ''
        if class_id == 0:  # person
            for poly in zones:
                # Kesişim oranı için polygon ve box kullanımı
                box = (x1, y1, x2, y2)
                # Basit alan kontrolü: kutunun merkezi polygon içinde mi?
                center = ((x1+x2)//2, (y1+y2)//2)
                if cv2.pointPolygonTest(np.array(poly, np.int32), center, False) >= 0:
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
            for poly in zones:
                box = (x1, y1, x2, y2)
                center = ((x1+x2)//2, (y1+y2)//2)
                if cv2.pointPolygonTest(np.array(poly, np.int32), center, False) >= 0:
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0,0,255), 2)
                    cv2.putText(frame, f'{class_name} {score:.2f} {track_text}', (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 1)

    cv2.imshow('Canli Akis', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
cap.release()
cv2.destroyAllWindows()
