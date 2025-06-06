# Gerekli kütüphanelerin import edilmesi
import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
from PIL import ImageFilter
import cv2
import threading
from face_recog import FaceRecognition
from tkinter import messagebox
from object_detect import detect_objects
import time
import numpy as np
from shapely.geometry import Polygon, box

# Alan listesi için özel widget sınıfı
class AreaListBox(ctk.CTkFrame):
    def __init__(self, master, area_name, remove_callback, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.remove_callback = remove_callback
        # Alan başlığı için frame (renkli ve köşeleri yuvarlatılmış)
        self.label_frame = ctk.CTkFrame(self, fg_color="#3a3f4b", corner_radius=10)
        self.label_frame.pack(fill="x", padx=0, pady=0)
        # Alan ismi etiketi (büyük ve modern font)
        self.label = ctk.CTkLabel(self.label_frame, text=area_name, font=("Segoe UI", 15, "bold"), text_color="#f5f5f5")
        self.label.pack(side="left", anchor="w", padx=10, pady=(8, 0))
        # Alan silme butonu (ikon ve renkli)
        self.remove_btn = ctk.CTkButton(self.label_frame, text="✖", width=32, fg_color="#e74c3c", hover_color="#c0392b", text_color="#fff", font=("Segoe UI", 14, "bold"), corner_radius=8, command=self.remove_area)
        self.remove_btn.pack(side="right", padx=8, pady=4)
        # Kişi listesi (daha modern kutu)
        self.listbox = tk.Listbox(self, height=4, width=25, bg="#23272f", fg="#f5f5f5", selectbackground="#3a3f4b", font=("Segoe UI", 12), relief="flat", highlightthickness=0, borderwidth=0)
        self.listbox.pack(fill="x", padx=10, pady=(0, 12))
        self.listbox.bind("<Button-3>", self.on_right_click)

    # Kişi ekleme metodu
    def add_person(self, name):
        if name not in self.listbox.get(0, tk.END):
            self.listbox.insert(tk.END, name)

    # Listeyi temizleme metodu
    def clear_people(self):
        self.listbox.delete(0, tk.END)

    # Alan silme metodu
    def remove_area(self):
        if messagebox.askyesno("Alan Sil", "Bu alanı silmek istediğinize emin misiniz?"):
            self.remove_callback(self)

    # Sağ tık menüsü metodu
    def on_right_click(self, event):
        selection = self.listbox.curselection()
        if selection:
            idx = selection[0]
            name = self.listbox.get(idx)
            if messagebox.askyesno("Kişi Sil", f"{name} kişisini bu alandan silmek istiyor musunuz?"):
                self.listbox.delete(idx)

# Ana uygulama sınıfı
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        # Pencere ayarları (daha koyu ve modern)
        self.title("Akıllı Alan ve Yüz Takip Arayüzü (customtkinter)")
        self.geometry("1200x700")
        self.resizable(True, True)
        self.configure(bg="#23272f")
        self.frame_width = 800
        self.frame_height = 600
        
        # UI bileşenlerinin başlatılması
        self.init_ui()
        
        # Kamera ve değişkenlerin başlatılması
        self.cap = cv2.VideoCapture(0)
        self.running = True
        self.polygon_mode = False
        self.current_points = []  # Normalized noktalar (0-1 arası oran)
        self.polygons = []        # Her polygon: [ (x_norm, y_norm), ... ]
        self.polygon_names = []
        # Polygon renkleri (RGBA formatında)
        self.polygon_colors = [(0,255,255,100), (255,0,0,100), (0,255,0,100), (255,0,255,100), (255,255,0,100)]
        self.polygon_border_colors = [(0,200,200), (200,0,0), (0,200,0), (200,0,200), (200,200,0)]
        self.area_listboxes = []
        self.detect_mode = False
        self.last_area_for_person = {}
        self.fr = FaceRecognition()
        self.last_seen_people = []  # Her alan için [{isim: zaman}]
        self.id_to_name = {}  # person_id -> isim eşleştirmesi
        
        # Event ve UI güncellemelerinin başlatılması
        self.bind_events()
        self.name_input.configure(state="disabled")
        self.confirm_area_btn.configure(state="disabled")
        self.update_frame()

    # UI bileşenlerinin oluşturulması
    def init_ui(self):
        # Ana frame
        self.main_frame = ctk.CTkFrame(self, fg_color="#23272f")
        self.main_frame.pack(fill="both", expand=True)
        # Sol frame (kamera görüntüsü için)
        self.left_frame = ctk.CTkFrame(self.main_frame, width=self.frame_width, height=self.frame_height, fg_color="#181a20", corner_radius=16)
        self.left_frame.pack(side="left", padx=18, pady=18)
        self.left_frame.pack_propagate(False)
        self.image_label = tk.Label(self.left_frame, bg="#181a20", width=self.frame_width, height=self.frame_height)
        self.image_label.pack(fill="both", expand=True)
        # Sağ frame (kontrol paneli)
        self.right_frame = ctk.CTkFrame(self.main_frame, width=400, fg_color="#23272f")
        self.right_frame.pack(side="right", fill="y", padx=18, pady=18)
        self.right_frame.pack_propagate(False)
        # Kontrol butonları (modern renkler ve fontlar)
        self.add_area_btn = ctk.CTkButton(self.right_frame, text="Alan Ekle", font=("Segoe UI", 14, "bold"), fg_color="#3498db", hover_color="#2980b9", text_color="#fff", corner_radius=10, height=40, command=self.start_polygon_mode)
        self.add_area_btn.pack(pady=(8, 12), fill="x")
        self.name_input = ctk.CTkEntry(self.right_frame, placeholder_text="Alan ismi girin", font=("Segoe UI", 13), fg_color="#23272f", text_color="#fff", border_color="#3a3f4b", border_width=2, corner_radius=8)
        self.name_input.pack(pady=12, fill="x")
        self.confirm_area_btn = ctk.CTkButton(self.right_frame, text="Ekle", font=("Segoe UI", 14, "bold"), fg_color="#27ae60", hover_color="#219150", text_color="#fff", corner_radius=10, height=40, command=self.add_area)
        self.confirm_area_btn.pack(pady=12, fill="x")
        self.finish_btn = ctk.CTkButton(self.right_frame, text="Onayla", font=("Segoe UI", 14, "bold"), fg_color="#8e44ad", hover_color="#6c3483", text_color="#fff", corner_radius=10, height=40, command=self.finish_areas)
        self.finish_btn.pack(pady=12, fill="x")
        # Alan listeleri bölümü (büyük başlık)
        self.area_lists_label = ctk.CTkLabel(self.right_frame, text="Alanlardaki Kişiler", font=("Segoe UI", 18, "bold"), text_color="#f5f5f5")
        self.area_lists_label.pack(pady=(24, 8))
        self.area_lists_frame = ctk.CTkFrame(self.right_frame, fg_color="#181a20", corner_radius=14)
        self.area_lists_frame.pack(fill="both", expand=True, padx=8, pady=8)
        self.area_listboxes = []
        # --- ARAMA KUTUSU ve SONUÇLARI (EN ALTA ALINDI) ---
        self.search_frame = ctk.CTkFrame(self.right_frame, fg_color="#23272f", corner_radius=12)
        self.search_frame.pack(side="bottom", pady=(8, 8), padx=0, fill="x")
        self.search_entry = ctk.CTkEntry(self.search_frame, placeholder_text="Kişi ara...", font=("Segoe UI", 13), fg_color="#23272f", text_color="#fff", border_color="#3a3f4b", border_width=2, corner_radius=8)
        self.search_entry.pack(pady=(12, 6), padx=10, fill="x")
        self.search_entry.bind("<KeyRelease>", self.on_search)
        # Sabit arama sonucu kutusu (her zaman görünür, başta boş)
        self.search_results_box = tk.Listbox(self.search_frame, height=4, width=30, bg="#23272f", fg="#f5f5f5", selectbackground="#3a3f4b", font=("Segoe UI", 12), relief="flat", highlightthickness=1, borderwidth=1, highlightbackground="#3a3f4b")
        self.search_results_box.pack(pady=(0, 10), padx=10, fill="x")

    # Event bağlantılarının yapılması
    def bind_events(self):
        self.image_label.bind("<Button-1>", self.on_image_click)

    # Kamera görüntüsünün güncellenmesi
    def update_frame(self):
        if not self.running:
            return
        frame, (label_w, label_h) = self.get_frame_and_resize()
        if frame is not None:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            draw = ImageDraw.Draw(img, 'RGBA')
            
            # Polygonların çizilmesi
            for i, poly in enumerate(self.polygons):
                color = self.polygon_colors[i % len(self.polygon_colors)]
                border = self.polygon_border_colors[i % len(self.polygon_border_colors)]
                if len(poly) == 4:
                    disp_poly = [ (int(x*label_w), int(y*label_h)) for (x, y) in poly ]
                    draw.polygon(disp_poly, fill=color)
                    draw.line(disp_poly + [disp_poly[0]], fill=border, width=3)
                    if i < len(self.polygon_names):
                        cx = int(sum([p[0] for p in disp_poly]) / 4)
                        cy = int(sum([p[1] for p in disp_poly]) / 4)
                        draw.text((cx-30, cy), self.polygon_names[i], fill=(255,255,255,255))

            # Geçici polygon çizimi
            # Geçici polygon (4 nokta seçildiyse ve isim girilmediyse)
            if len(self.current_points) == 4 and self.name_input.cget('state') == 'normal':
                disp_poly = [ (int(x*label_w), int(y*label_h)) for (x, y) in self.current_points ]
                # Yarı şeffaf mavi dolgu ve kesikli çizgi
                draw.polygon(disp_poly, fill=(0,128,255,80))
                for i in range(4):
                    p1 = disp_poly[i]
                    p2 = disp_poly[(i+1)%4]
                    # Kesikli çizgi için noktalar
                    for t in range(0, 100, 10):
                        x = int(p1[0] + (p2[0]-p1[0])*t/100)
                        y = int(p1[1] + (p2[1]-p1[1])*t/100)
                        draw.ellipse((x-2, y-2, x+2, y+2), fill=(0,128,255,255))
            # Geçici çizim (henüz tamamlanmamış polygon)
            elif self.polygon_mode and len(self.current_points) > 0:
                for idx, (x_norm, y_norm) in enumerate(self.current_points):
                    px = int(x_norm * label_w)
                    py = int(y_norm * label_h)
                    draw.ellipse((px-7, py-7, px+7, py+7), fill=(0,0,255,255))
                    draw.text((px+10, py-10), f"{idx+1}:({px},{py})", fill=(255,255,255,255))
                if len(self.current_points) > 1:
                    disp_points = [ (int(x*label_w), int(y*label_h)) for (x, y) in self.current_points ]
                    draw.line(disp_points, fill=(255,0,0,255), width=2, joint="round")
            imgtk = None
            if self.detect_mode:
                # Object detection sonuçlarını çiz
                objects = detect_objects(frame)
                person_ids_in_area = [[] for _ in self.polygons]  # Her alan için person id listesi
                for class_id, class_name, score, (x1, y1, x2, y2), track_id in objects:
                    x1_disp = int(x1 * label_w / frame.shape[1])
                    x2_disp = int(x2 * label_w / frame.shape[1])
                    y1_disp = int(y1 * label_h / frame.shape[0])
                    y2_disp = int(y2 * label_h / frame.shape[0])
                    in_any_poly = False
                    for poly_idx, poly in enumerate(self.polygons):
                        disp_poly = [ (int(x*label_w), int(y*label_h)) for (x, y) in poly ]
                        if self.is_bbox_in_polygon((x1_disp, y1_disp, x2_disp, y2_disp), disp_poly):
                            in_any_poly = True
                            # Sadece person için, ID'yi ilgili alana ekle
                            if class_name == 'person' and track_id is not None:
                                person_ids_in_area[poly_idx].append(track_id)
                            break
                    if not in_any_poly:
                        continue  # Alan dışında, hiçbir şey çizme
                    color = (0,255,0,180) if class_name == 'person' else (255,128,0,180)
                    draw.rectangle([x1_disp, y1_disp, x2_disp, y2_disp], outline=color, width=3)
                    label = f"{class_name} {int(score*100)}%"
                    if track_id is not None:
                        label += f" ID:{track_id}"
                    draw.text((x1_disp+2, y1_disp+2), label, fill=(255,255,255,255))
                # Her person kutusu için yüz tanıma yap (sadece alan içindekiler için)
                FACE_SCORE_THRESHOLD = 0.75 
                for class_id, class_name, score, (x1, y1, x2, y2), track_id in objects:
                    if class_name == 'person' and track_id is not None:
                        x1_disp = int(x1 * label_w / frame.shape[1])
                        x2_disp = int(x2 * label_w / frame.shape[1])
                        y1_disp = int(y1 * label_h / frame.shape[0])
                        y2_disp = int(y2 * label_h / frame.shape[0])
                        in_any_poly = False
                        for poly_idx, poly in enumerate(self.polygons):
                            disp_poly = [ (int(x*label_w), int(y*label_h)) for (x, y) in poly ]
                            if self.is_bbox_in_polygon((x1_disp, y1_disp, x2_disp, y2_disp), disp_poly):
                                in_any_poly = True
                                break
                        if not in_any_poly:
                            continue  # Alan dışında, yüz tanıma yapma
                        face_crop = frame[y1_disp:y2_disp, x1_disp:x2_disp]
                        faces = self.fr.recognize_faces(face_crop)
                        for name, face_score, (top, right, bottom, left) in faces:
                            # Yüzde işareti varsa temizle, float'a çevir, normalize et
                            score_val = float(face_score.replace('%', '').strip())
                            score_val = score_val / 100
                            if name != "Unknown" and score_val >= FACE_SCORE_THRESHOLD:
                                self.id_to_name[track_id] = name
                            abs_top = y1_disp + top
                            abs_right = x1_disp + right
                            abs_bottom = y1_disp + bottom
                            abs_left = x1_disp + left
                            draw.rectangle([abs_left, abs_top, abs_right, abs_bottom], outline=(0,255,255,180), width=2)
                            draw.text((abs_left+2, abs_top-18), f"{name} ({int(score_val*100)})", fill=(255,255,0,255))
                # Alanlardaki kişi listelerini güncelle
                self.update_area_people_v2(person_ids_in_area)
            imgtk = ImageTk.PhotoImage(image=img)
            self.image_label.imgtk = imgtk
            self.image_label.configure(image=imgtk)
        self.after(30, self.update_frame)

    def detect_faces(self, frame):
        results = self.fr.recognize_faces(frame)
        detected = []
        for name, _, (top, right, bottom, left) in results:
            cx = (left + right) // 2
            cy = (top + bottom) // 2
            detected.append((name, (cx, cy), (top, right, bottom, left)))
        return detected

    def update_area_people(self, detected_people):
        now = time.time()
        # Eğer hiç alan yoksa, kişi listelerini temizle ve çık
        if not self.area_listboxes or not self.polygons:
            for area_box in self.area_listboxes:
                area_box.clear_people()
            return
        # Her alan için: son görülenleri güncelle
        for i, area_box in enumerate(self.area_listboxes):
            # Alan için yeni tespit edilen isimler
            current_names = set()
            for name, (x, y) in detected_people:
                if i < len(self.polygons):
                    label_w = self.image_label.winfo_width()
                    label_h = self.image_label.winfo_height()
                    disp_poly = [ (int(px*label_w), int(py*label_h)) for (px, py) in self.polygons[i] ]
                    if self.point_in_polygon((x, y), disp_poly):
                        current_names.add(name)
            # Son görülenleri güncelle
            last_seen = self.last_seen_people[i]
            for name in current_names:
                last_seen[name] = now
            # 1 saniyeden eski olanları sil
            to_remove = [n for n, t in last_seen.items() if now - t > 15.0]
            for n in to_remove:
                del last_seen[n]
            # Alan kutusunu güncelle
            area_box.clear_people()
            for n in last_seen:
                area_box.add_person(n)

    def point_in_polygon(self, point, poly):
        n = len(poly)
        inside = False
        px, py = point
        j = n - 1
        for i in range(n):
            xi, yi = poly[i]
            xj, yj = poly[j]
            if ((yi > py) != (yj > py)) and (px < (xj - xi) * (py - yi) / (yj - yi + 1e-9) + xi):
                inside = not inside
            j = i
        return inside

    def on_image_click(self, event):
        if not self.polygon_mode:
            return
        label_w = self.image_label.winfo_width()
        label_h = self.image_label.winfo_height()
        x_norm = event.x / label_w
        y_norm = event.y / label_h
        self.current_points.append((x_norm, y_norm))
        if len(self.current_points) == 4:
            self.name_input.configure(state="normal")
            self.confirm_area_btn.configure(state="normal")
            self.polygon_mode = False

    def start_polygon_mode(self):
        self.polygon_mode = True
        self.current_points = []
        self.name_input.delete(0, "end")
        self.name_input.configure(state="disabled")
        self.confirm_area_btn.configure(state="disabled")
        print("Polygon çizim modu başlatıldı.")

    def add_area(self):
        name = self.name_input.get().strip()
        if len(self.current_points) == 4:
            if not name:
                name = f"Alan{len(self.polygon_names)+1}"
            self.polygons.append(self.current_points.copy())
            self.polygon_names.append(name)
            self.current_points = []
            self.name_input.delete(0, "end")
            self.name_input.configure(state="disabled")
            self.confirm_area_btn.configure(state="disabled")
            area_box = AreaListBox(self.area_lists_frame, name, self.remove_area)
            area_box.pack(fill="x", pady=6, anchor="n")
            self.area_listboxes.append(area_box)
            self.last_seen_people.append({})  # Yeni alan için sözlük ekle
            self.polygon_mode = False
            print(f"Alan eklendi: {name}")
        else:
            print("4 nokta ve isim gerekli!")

    def remove_area(self, area_box):
        idx = self.area_listboxes.index(area_box)
        area_box.destroy()
        del self.area_listboxes[idx]
        del self.polygons[idx]
        del self.polygon_names[idx]
        del self.last_seen_people[idx]
        print("Alan silindi.")

    def finish_areas(self):
        print("Alan ekleme tamamlandı, tespit moduna geçildi.")
        self.detect_mode = True
        self.add_area_btn.configure(state="disabled")
        self.name_input.configure(state="disabled")
        self.confirm_area_btn.configure(state="disabled")
        self.finish_btn.configure(state="disabled")

    def on_closing(self):
        self.running = False
        if self.cap:
            self.cap.release()
        self.destroy()

    def intersection_area(self, boxA, boxB):
        # boxA ve boxB: (x1, y1, x2, y2)
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])
        interW = max(0, xB - xA)
        interH = max(0, yB - yA)
        return interW * interH

    def bbox_polygon_intersection_area(self, bbox, polygon):
        # bbox: (x1, y1, x2, y2), polygon: [(x, y), ...]
        poly = Polygon(polygon)
        rect = box(bbox[0], bbox[1], bbox[2], bbox[3])
        inter = poly.intersection(rect)
        return inter.area

    def is_bbox_in_polygon(self, bbox, polygon, threshold=0.7):
        """
        bbox: (x1, y1, x2, y2)
        polygon: [(x, y), ...]
        threshold: oran (varsayılan 0.7)
        """
        box_area = max(1, (bbox[2] - bbox[0]) * (bbox[3] - bbox[1]))
        inter_area = self.bbox_polygon_intersection_area(bbox, polygon)
        return (box_area > 0) and (inter_area / box_area >= threshold)

    def get_frame_and_resize(self):
        ret, frame = self.cap.read()
        if not ret:
            return None, None
        frame = cv2.flip(frame, 1)
        label_w = self.image_label.winfo_width()
        label_h = self.image_label.winfo_height()
        frame = cv2.resize(frame, (label_w, label_h))
        return frame, (label_w, label_h)

    def on_search(self, event=None):
        query = self.search_entry.get().strip().lower()
        self.search_results_box.delete(0, tk.END)
        if not query:
            # Sonuç kutusu boş ama görünür kalacak
            return
        results = []
        for i, area_box in enumerate(self.area_listboxes):
            area_name = self.polygon_names[i] if i < len(self.polygon_names) else f"Alan{i+1}"
            for person in area_box.listbox.get(0, tk.END):
                if query in person.lower():
                    results.append(f"{person} - {area_name}")
        if results:
            for res in results:
                self.search_results_box.insert(tk.END, res)
        # Sonuç yoksa kutu boş kalacak, ama kaybolmayacak

    def update_area_people_v2(self, person_ids_in_area):
        # Her alan için, o anda bölgede olan person ID'lerin isimlerini göster
        for i, area_box in enumerate(self.area_listboxes):
            area_box.clear_people()
            for pid in person_ids_in_area[i]:
                name = self.id_to_name.get(pid, f"ID:{pid}")
                area_box.add_person(name)

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop() 