import tkinter as tk
import os
import threading
import sys

from src.updatalist import updata_list
from src.gui import ImageClassifierGUI
from src.processing import main_processing
from src import positions

# --- ディレクトリ設定 ---
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    script_dir = os.getcwd()

# --- 設定 ---
updata_list(script_dir) # 生徒リストの更新
positions = positions.positions # 座標取得
input_imgs_dir = os.path.join(script_dir, "Screenshots") # 入力画像ディレクトリを定義

if __name__ == "__main__":
    root = tk.Tk()
    gui = ImageClassifierGUI(root, script_dir)

    # メイン処理開始
    processing_thread = threading.Thread(
        target=main_processing,
        args=(gui, script_dir, positions, input_imgs_dir),
        daemon=True #true -> 処理終了時にスレッドも終了
    )
    processing_thread.start()
    root.mainloop()