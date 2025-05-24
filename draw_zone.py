import cv2

drawing = False
ix, iy = -1, -1
rectangles = []
current_frame = None  # Güncel frame'i global olarak tut

# Fare olaylarını işleyecek fonksiyon
def draw_rectangle(event, x, y, flags, param):
    global ix, iy, drawing, rectangles, frame_with_rectangles, current_frame
    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y
    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            img_copy = frame_with_rectangles.copy()
            cv2.rectangle(img_copy, (ix, iy), (x, y), (0, 255, 0), 2)
            cv2.imshow('Canli Akis', img_copy)
    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        rectangles.append(((ix, iy), (x, y)))
        frame_with_rectangles = current_frame.copy()  # frame yerine current_frame
        for rect in rectangles:
            cv2.rectangle(frame_with_rectangles, rect[0], rect[1], (0, 255, 0), 2)
        cv2.imshow('Canli Akis', frame_with_rectangles)

def draw_zones_on_stream(cap):
    global frame_with_rectangles, rectangles, current_frame
    rectangles = []
    cv2.namedWindow('Canli Akis')
    cv2.setMouseCallback('Canli Akis', draw_rectangle)
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Kare alınamadı.")
            exit()
        frame = cv2.flip(frame, 1)
        current_frame = frame  # Her döngüde güncelleniyor
        if 'frame_with_rectangles' not in globals():
            frame_with_rectangles = frame.copy()
        else:
            frame_with_rectangles = frame.copy()
            for rect in rectangles:
                cv2.rectangle(frame_with_rectangles, rect[0], rect[1], (0, 255, 0), 2)
        cv2.imshow('Canli Akis', frame_with_rectangles)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == ord('s'):
            break
    cv2.setMouseCallback('Canli Akis', lambda *a: None) # Mouse olaylarını kapat
    return rectangles.copy()

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