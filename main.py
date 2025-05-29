import sys
import argparse
from gui_ctk import App
import customtkinter as ctk

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
