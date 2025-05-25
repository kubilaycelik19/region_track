import sys
import argparse
from gui_ctk import App
import customtkinter as ctk

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Video veya kamera kaynağı seçimi")
    parser.add_argument('--source', type=str, default='0', help='Kamera icin 0, video dosyasi icin yol')
    args = parser.parse_args()
    # Eğer sayı ise int'e çevir
    try:
        video_source = int(args.source)
    except ValueError:
        video_source = args.source
    ctk.set_appearance_mode("dark")
    app = App(video_source)
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
