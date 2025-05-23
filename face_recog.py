import face_recognition  # Yüz tanıma işlemleri için kullanılan kütüphane
import os, sys           # Dosya ve sistem işlemleri için
import cv2               # OpenCV, görüntü işleme için
import numpy as np       # Sayısal işlemler için
import math              # Matematiksel işlemler için

def face_confidence(face_distance, face_match_threshold=0.6):
    """Yüz mesafesini güven skoruna çeviriyorum."""
    range = (1.0 - face_match_threshold)
    linear_val = (1.0 - face_distance) / (range * 2.0)

    if face_distance > face_match_threshold:
        # Eşik değerinden büyükse doğrusal olarak güven skoru döndür
        return str(round(linear_val * 100, 2)) + '%'
    else:
        # Eşik değerinden küçükse daha karmaşık bir formülle güven skoru döndür
        value = (linear_val + ((1.0 - linear_val) * math.pow((linear_val - 0.5) * 2, 0.2))) * 100
        return str(round(value, 2)) + '%'

def preprocess_image(image):
    """Görüntüyü ön işlemden geçiriyorum."""
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    image = cv2.convertScaleAbs(image, alpha=1.3, beta=30)

    """equalized = cv2.equalizeHist(gray)
    denoised = cv2.fastNlMeansDenoising(equalized)"""
    return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

class FaceRecognition:
    """Yüz tanıma işlemlerini yöneten ana sınıf."""
    face_locations = []
    face_encodings = []
    face_names = []
    known_face_encodings = []
    known_face_names = []

    def __init__(self):
        """Sınıfı başlatıp yüz kodlamalarını oluşturuyorum."""
        self.encode_faces()

    def encode_faces(self):
        """Faces klasöründeki yüzleri kodluyorum."""
        for person_folder in os.listdir('faces'):
            person_path = os.path.join('faces', person_folder)
            
            if not os.path.isdir(person_path):
                continue  # Sadece klasörler işlenir
                
            person_encodings = []
            
            for image_file in os.listdir(person_path):
                # Sadece resim dosyalarını işle
                if not image_file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    continue
                    
                image_path = os.path.join(person_path, image_file)
                face_image = face_recognition.load_image_file(image_path)  # Resmi yükle
                face_image = preprocess_image(face_image)  # Ön işlem uygula
                
                face_encodings = face_recognition.face_encodings(face_image)  # Yüz kodlamasını al
                
                if face_encodings:
                    person_encodings.append(face_encodings[0])  # İlk yüz kodlamasını ekle
            
            if person_encodings:
                # Kişinin tüm resimlerinden ortalama bir yüz kodlaması oluştur
                avg_encoding = np.mean(person_encodings, axis=0)
                self.known_face_encodings.append(avg_encoding)
                self.known_face_names.append(person_folder)  # Kişinin adını ekle

        """print('Yüz kodlamaları tamamlandı!')  # Kodlama tamamlandı mesajı
        print(f'Bilinen yüzler: {self.known_face_names}')  # Bilinen yüzler"""

    def recognize_faces(self, frame):
        """
        Verilen bir frame (BGR formatında) üzerinde yüz tanıma yapar.
        Tanınan yüzlerin isim, güven skoru ve koordinatlarını döndürür.
        Dönüş: [(isim, güven, (top, right, bottom, left)), ...]
        """
        results = []
        frame = preprocess_image(frame)  # Ön işlem uygula
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)  # Küçült
        rgb_small_frame = small_frame[:, :, ::-1]  # BGR'den RGB'ye çevir

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        for face_encoding, face_location in zip(face_encodings, face_locations):
            matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
            name = "Unknown"
            confidence = 'unknown'

            face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = self.known_face_names[best_match_index]
                    confidence = face_confidence(face_distances[best_match_index])
            # Koordinatları orijinal boyuta çevir (çarpan 4)
            top, right, bottom, left = face_location
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4
            results.append((name, confidence, (top, right, bottom, left)))
        return results
