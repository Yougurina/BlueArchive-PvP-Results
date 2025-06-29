import tkinter as tk
import os
import threading
import sys

from src.updatalist import updata_list
from src.gui import ImageClassifierGUI
from src.processing import main_processing
from src import select_preset
from src.transcription import main as transcription_main

# --- ディレクトリ設定 ---
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    script_dir = os.getcwd()

# --- 設定 ---
updata_list(script_dir) # 生徒リストの更新

try:
    positions = select_preset.run() # 使用するプリセットの座標取得
except:
    print("\nエラー: プリセットが存在しません。処理を終了します。")
    sys.exit(1)

input_imgs_dir = os.path.join(script_dir, "Screenshots") # 入力画像ディレクトリを定義

def cleanup_and_transcribe():
    """GUIを完全に閉じてから転記処理を実行"""
    # GUIが完全に破棄されるまで少し待機
    import time
    time.sleep(0.5)
    
    print("\n=== データ転記処理を開始します ===")
    try:
        transcription_main(script_dir)
        print("=== データ転記処理が完了しました ===")
    except Exception as e:
        print(f"データ転記処理でエラーが発生しました: {e}")
    
    print("プログラムを終了します")

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
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\n処理が中断されました")
    
    # GUIウィンドウを完全に破棄
    try:
        root.quit()
        root.destroy()
    except:
        pass
    
    # GUIが完全に閉じられた後に転記処理を実行
    cleanup_and_transcribe()