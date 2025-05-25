import cv2
import numpy as np

drawing = False
polygon_points = []
polygons = []
polygon_labels = []
current_frame = None  # Güncel frame'i global olarak tut

# Renk paleti
FILL_COLORS = [(0,255,255), (0,0,255), (255,0,0), (0,255,0), (255,0,255), (255,255,0), (0,128,255), (128,0,255)]
BORDER_COLORS = [(0,200,200), (0,0,200), (200,0,0), (0,200,0), (200,0,200), (200,200,0), (0,100,200), (100,0,200)]

# Fare olaylarını işleyecek fonksiyon (4 köşe polygon)
def mouse_callback(event, x, y, flags, param):
    global polygon_points, polygons, polygon_labels, current_frame
    if event == cv2.EVENT_LBUTTONDOWN:
        polygon_points.append((x, y))
        if len(polygon_points) == 4:
            polygons.append(polygon_points.copy())
            # Önce polygonu ekranda göster
            temp_frame = current_frame.copy()
            temp_frame = draw_polygons_on_frame(temp_frame, polygons, labels=polygon_labels + ["?"], active_points=[])
            cv2.imshow('Canli Akis', temp_frame)
            cv2.waitKey(1)  # Ekranı güncelle
            # Sonra input al
            label = input(f"{len(polygons)}. alan için etiket girin: ")
            polygon_labels.append(label)
            polygon_points = []

def draw_polygons_on_frame(frame, polygons, labels=None, active_points=None, fill_colors=None, border_colors=None, alpha=0.4):
    if fill_colors is None:
        fill_colors = FILL_COLORS
    if border_colors is None:
        border_colors = BORDER_COLORS
    overlay = frame.copy()
    for i, pts in enumerate(polygons):
        pts_np = np.array(pts, np.int32).reshape((-1, 1, 2))
        cv2.fillPoly(overlay, [pts_np], fill_colors[i % len(fill_colors)])
        cv2.polylines(frame, [pts_np], isClosed=True, color=border_colors[i % len(border_colors)], thickness=3)
        # Alanın ortasına label yaz
        if labels is not None and i < len(labels):
            M = cv2.moments(pts_np)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                cv2.putText(frame, str(labels[i]), (pts[0][0], pts[0][1]), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255,255,255), 3)
    # Aktif işaretlenen noktaları göster
    if active_points is not None and len(active_points) > 0:
        for idx, pt in enumerate(active_points):
            cv2.circle(frame, pt, 6, (255,255,255), -1)
            cv2.putText(frame, f"{idx+1}:({pt[0]},{pt[1]})", (pt[0]+8, pt[1]-8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
        if len(active_points) > 1:
            cv2.polylines(frame, [np.array(active_points, np.int32).reshape((-1, 1, 2))], False, (255,255,255), 2)
    return cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

def draw_zones_on_stream(cap):
    global current_frame, polygons, polygon_points, polygon_labels
    polygons = []
    polygon_points = []
    polygon_labels = []
    cv2.namedWindow('Canli Akis')
    cv2.setMouseCallback('Canli Akis', mouse_callback)
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Kare alınamadı.")
            exit()
        frame = cv2.flip(frame, 1)
        current_frame = frame
        temp_frame = frame.copy()
        temp_frame = draw_polygons_on_frame(temp_frame, polygons, labels=polygon_labels, active_points=polygon_points)
        cv2.imshow('Canli Akis', temp_frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == ord('s'):
            break
    cv2.setMouseCallback('Canli Akis', lambda *a: None)
    return polygons.copy(), polygon_labels.copy()

def draw_zones_on_frame(frame, zones, fill_color=(0,255,255), border_color=(0,255,255), alpha=0.2):
    """
    frame: Ana görüntü
    zones: [((x1, y1), (x2, y2)), ...]
    fill_color: BGR dolgu rengi
    border_color: BGR kenarlık rengi
    alpha: şeffaflık oranı
    """
    overlay = frame.copy()
    for rect in zones:
        (zx1, zy1), (zx2, zy2) = rect
        zone_xmin, zone_xmax = min(zx1, zx2), max(zx1, zx2)
        zone_ymin, zone_ymax = min(zy1, zy2), max(zy1, zy2)
        cv2.rectangle(overlay, (zone_xmin, zone_ymin), (zone_xmax, zone_ymax), fill_color, -1)
        cv2.rectangle(frame, (zone_xmin, zone_ymin), (zone_xmax, zone_ymax), border_color, 2)
    return cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0) 