# Persistent Person Tracking + Face Recognition

YOLO v8 tracking ve yüz tanıma ile kalıcı kişi takibi sistemi.

## Özellikler

- **YOLO v8 Tracking**: Gerçek zamanlı person tracking (ID bazlı takip)
- **Persistent Face Recognition**: Bir kez tanınan kişi, yüzü gözükmese bile aynı kimlikle takip edilir
- **Akıllı Kimlik Yönetimi**: Tanınan kimliklerin otomatik kaydedilmesi ve timeout ile temizlenmesi
- **Görsel Feedback**: Tanınan kişiler yeşil, bilinmeyenler mavi renkle gösterilir
- **Performans Optimizasyonu**: Tracking her frame, yüz tanıma her 5 frame'de bir yapılır

## Kurulum

### 1. Gerekli Paketleri Yükleyin

```bash
pip install -r requirements.txt
```

### 2. Yüz Veritabanı Hazırlayın

Projenin ana dizininde `faces` klasörü oluşturun ve içinde her kişi için ayrı klasörler açın:

```
faces/
├── ahmet/
│   ├── ahmet1.jpg
│   ├── ahmet2.jpg
│   └── ahmet3.jpg
├── ayse/
│   ├── ayse1.jpg
│   └── ayse2.jpg
└── mehmet/
    └── mehmet1.jpg
```

**Not**: 
- Her kişi için birden fazla fotoğraf kullanmak tanıma başarısını artırır
- Desteklenen formatlar: `.jpg`, `.jpeg`, `.png`
- Fotoğraflar net ve yüzün önden göründüğü şekilde olmalı

## Kullanım

### Kamera ile başlatmak için:
```bash
python main.py --source 0
```

### Video dosyası ile başlatmak için:
```bash
python main.py --source test_video.mp4
```

### Arayüz Kullanımı

- **Alan Ekle:**  
  Sağ taraftan "Alan Ekle"ye bas,
  Sol ekranda 4 nokta seç, sağdan isim gir (veya boş bırak), "Ekle"ye tıkla.
- **Onayla:**  
  Tüm alanları ekledikten sonra "Onayla"ya bas, tespit moduna geç.
- **Kişi Sil:**  
  Alan listesindeki kişiye sağ tıkla, "Kişi Sil" de.
- **Alan Sil:**  
  Alan başlığındaki kırmızı çarpı butonuna tıkla.
- **Arama:**  
  Sağ alttaki kutudan tüm alanlarda kişi ara.

## Teknik Detaylar

### Dosya Yapısı

- `main.py`: Ana uygulama dosyası (YOLO Tracking + Persistent Face Recognition)
- `face_recog.py`: Yüz tanıma işlemleri (değiştirilmemiştir)
- `faces/`: Yüz veritabanı klasörü
- `requirements.txt`: Gerekli Python paketleri

### Algoritma Akışı

1. **Kamera Girişi**: Webcam'den görüntü alınır
2. **Person Tracking**: YOLO v8 tracking ile kişiler ID'li olarak takip edilir
3. **Kimlik Kontrolü**: Her track ID için mevcut kimlik bilgisi kontrol edilir
4. **Yüz Tanıma**: Kimlik bilgisi olmayan track'ler için yüz tanıma yapılır
5. **Persistent Tracking**: Tanınan kimlikler kaydedilir ve sonraki frame'lerde kullanılır
6. **Görselleştirme**: 
   - Tanınan kişiler: Yeşil kutu + kimlik bilgisi
   - Bilinmeyen kişiler: Mavi kutu + track ID

### Persistent Tracking Sistemi

- **Kimlik Kaydı**: Yüz tanındığında track ID ile eşleştirilir
- **Kalıcı Takip**: Yüz gözükmese bile 5 saniye boyunca kimlik korunur
- **Otomatik Temizlik**: Kaybolmuş track'ler ve timeout olan kimlikler silinir
- **Çoklu Kişi**: Aynı anda birden fazla kişi tanınabilir ve takip edilebilir

### Performans Özellikleri

- **Tracking**: Her frame'de YOLO tracking (hızlı)
- **Face Recognition**: Her 5 frame'de bir yüz tanıma (optimize)
- **ROI Optimizasyonu**: Sadece person bounding box'ının üst yarısında yüz aranır
- **Model Boyutu**: YOLOv8 nano modeli kullanılır (hız için)
- **Memory Management**: Otomatik kimlik temizleme sistemi

## Nasıl Çalışır?

1. **İlk Görülme**: Kişi kameraya girince YOLO tracking sistemi ona bir ID verir (örn: ID:1)
2. **Yüz Tanıma**: Sistem kişinin yüzünü tarar ve bilinen yüzlerle karşılaştırır
3. **Kimlik Eşleştirme**: Yüz tanındığında (örn: "Ahmet"), bu kimlik track ID ile eşleştirilir
4. **Persistent Tracking**: Artık kişi yüzünü çevirse bile "ID:1 - Ahmet %95.2" olarak gösterilir
5. **Timeout**: 5 saniye boyunca görülmezse kimlik bilgisi silinir

## Gereksinimler

- **Python**: 3.8+
- **Kamera**: Webcam veya USB kamera
- **İşlemci**: CPU yeterli (GPU isteğe bağlı)
- **RAM**: En az 4GB önerilir

## Sorun Giderme

### Kamera Açılamıyor
```bash
# Kamera index'ini kontrol edin
python -c "import cv2; print('Kamera durum:', cv2.VideoCapture(0).isOpened())"
```

### YOLO Modeli İndirilmiyor
```bash
# İnternet bağlantısını kontrol edin
# İlk çalıştırmada yolov8n.pt otomatik indirilir
```

### Yüz Tanınmıyor
- `faces/` klasörünün doğru yapıda olduğundan emin olun
- Fotoğrafların net ve yüzün görünür olduğundan emin olun
- Kişi başına en az 2-3 farklı fotoğraf kullanın

### Tracking Sorunları
- Kalabalık ortamlarda tracking performansı düşebilir
- İyi aydınlatma tracking kalitesini artırır
- Hızlı hareketlerde ID'ler değişebilir

### Kütüphane ve requirements sorunları
- dlib yükleme sorunu için çözüm videosu: https://www.youtube.com/watch?v=pO150OCX-ac&t=4s
- face_recognition kütüphanesi sorunu içi python 3.9.21 kullanabilirsiniz.
- "dlib-face-detection-error-unsupported-image-type-must-be-8bit-gray-or-rgb-image" sorunu için pip install numpy==1.26.4 kullanabilirsiniz

## Katkı ve Geliştirme

Pull request ve issue'larınızı beklerim!  
Her türlü öneri ve katkı için iletişime geçebilirsiniz.

**Hazırlayan:**  
Linkedin -> www.linkedin.com/in/kubilay-çelik-033b8b256
github -> https://github.com/kubilaycelik19