import tkinter as tk
from tkinter import simpledialog, messagebox
from PIL import Image, ImageTk
import cv2
import os
import numpy
import datetime
import shutil
import sys
import threading
import queue

# --- 画像処理関数 ---
def fx_templatematch(img1, img2):
    """2つの画像の類似度を計算する"""
    # img1: 検索用画像、img2: マッチング用画像（テンプレート）
    # PIL画像をOpenCV形式に変換
    img1_cv = cv2.cvtColor(numpy.array(img1), cv2.COLOR_RGB2BGR)
    img2_cv = cv2.cvtColor(numpy.array(img2), cv2.COLOR_RGB2BGR)

    # グレースケール変換
    img1_gray = cv2.cvtColor(img1_cv, cv2.COLOR_BGR2GRAY)
    img2_gray = cv2.cvtColor(img2_cv, cv2.COLOR_BGR2GRAY)

    # サイズ比較と処理選択
    h1, w1 = img1_gray.shape
    h2, w2 = img2_gray.shape
    
    try:
        if h1 == h2 and w1 == w2:
            # 同じサイズの場合は直接比較
            result = cv2.matchTemplate(img1_gray, img2_gray, cv2.TM_CCOEFF_NORMED)
            return result[0][0]
        else:
            # 画像サイズが異なる場合
            # 1. テンプレート（img2）をクエリ画像（img1）のサイズにリサイズ
            resized_img2 = cv2.resize(img2_gray, (w1, h1), interpolation=cv2.INTER_AREA)
            result1 = cv2.matchTemplate(img1_gray, resized_img2, cv2.TM_CCOEFF_NORMED)
            score1 = result1[0][0]
            
            # 2. クエリ画像（img1）をテンプレート（img2）のサイズにリサイズ
            resized_img1 = cv2.resize(img1_gray, (w2, h2), interpolation=cv2.INTER_AREA)
            result2 = cv2.matchTemplate(resized_img1, img2_gray, cv2.TM_CCOEFF_NORMED)
            score2 = result2[0][0]
            
            # 3. 両方の結果のうち良い方を採用
            return max(score1, score2)
    except cv2.error as e:
        print(f"Error during template matching: {e}")
        print(f"Image 1 shape: {img1_gray.shape}, Image 2 shape: {img2_gray.shape}")
        # エラー時は低い類似度を返す
        return -1.0

def fx_trim(name):
    """ファイル名から拡張子や末尾の '_数字' を取り除く"""
    base_name = os.path.splitext(name)[0] # 拡張子を除去
    parts = base_name.split('_')
    # 末尾が数字かどうかをチェック
    if len(parts) > 1 and parts[-1].isdigit():
        return '_'.join(parts[:-1]) # 末尾の '_数字' を除去
    return base_name # それ以外は拡張子除去後の名前を返す

def fx_append_txt(path, text):
    """指定されたパスのテキストファイルに追記する"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, f"リザルト_{path}.txt")
    try:
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(text + '\n')
    except Exception as e:
        print(f"Error appending to file {file_path}: {e}")

def fx_move_and_rename(img_path, output_dir_base):
    """画像を履歴フォルダに移動し、連番でリネームする"""
    output_dir = os.path.join(output_dir_base, "履歴")
    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 既存のファイルを確認して次の番号を決定
        existing_files = [f for f in os.listdir(output_dir) if f.endswith(".png")]
        num = len(existing_files) + 1
        name = str(num).zfill(5) + ".png"
        output_img = os.path.join(output_dir, name)

        shutil.move(img_path, output_img)
        return name
    except Exception as e:
        print(f"Error moving/renaming file {img_path}: {e}")
        return None

def fx_save_trim_img(img, save_folder_path, name, num=0):
    """トリミング画像を保存する（重複回避のため連番付与）"""
    if not name: # 名前が空の場合は保存しない
        print("Warning: Empty name provided for saving image. Skipping save.")
        return None # 保存しなかったことを示すためにNoneを返す

    img_name_base = name
    img_name = f"{img_name_base}_{num}.png" if num > 0 else f"{img_name_base}.png"
    save_path = os.path.join(save_folder_path, img_name)

    # ディレクトリが存在しない場合は作成
    if not os.path.exists(save_folder_path):
        try:
            os.makedirs(save_folder_path)
            print(f"Created directory: {save_folder_path}")
        except Exception as e:
            print(f"Error creating directory {save_folder_path}: {e}")
            return None # ディレクトリ作成失敗

    # ファイル名の重複チェック
    current_num = num
    while os.path.exists(save_path):
        current_num += 1
        img_name = f"{img_name_base}_{current_num}.png"
        save_path = os.path.join(save_folder_path, img_name)
        if current_num > 100: # 無限ループ防止
             print(f"Warning: Too many duplicates for {img_name_base} in {save_folder_path}. Skipping save.")
             return None

    try:
        img.save(save_path)
        print(f"Saved image: {save_path}")
        return os.path.basename(save_path) # 保存したファイル名を返す
    except Exception as e:
        print(f"Error saving image to {save_path}: {e}")
        return None

# --- GUIクラス ---
class ImageClassifierGUI:
    def __init__(self, root, script_dir):
        self.root = root
        self.script_dir = script_dir
        self.root.title("画像分類ツール")
        self.root.geometry("800x700") # 少し縦長に

        self.user_input = None
        self.input_received = tk.BooleanVar(value=False)

        # --- 上部フレーム（画像表示用） ---
        self.image_frame = tk.Frame(root, bg="#ECECEC", bd=2, relief=tk.SUNKEN)
        self.image_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        self.image_label = tk.Label(self.image_frame, text="画像待機中...", bg="#ECECEC")
        self.image_label.pack(expand=True, fill=tk.BOTH)
        self.img_tk = None # ImageTk参照保持用

        # --- 下部フレーム（コントロール用） ---
        self.control_frame = tk.Frame(root)
        self.control_frame.pack(pady=10, padx=10, fill=tk.X)

        # 入力欄と決定ボタンのフレーム
        self.input_frame = tk.Frame(self.control_frame)
        self.input_frame.pack(pady=5)

        self.entry_label = tk.Label(self.input_frame, text="新規登録名:")
        self.entry_label.pack(side=tk.LEFT, padx=5)

        self.entry = tk.Entry(self.input_frame, width=40, font=("Arial", 12))
        self.entry.pack(side=tk.LEFT, padx=5)
        self.entry.bind("<Return>", lambda event: self.submit_input()) # Enterキー対応

        self.submit_button = tk.Button(self.input_frame, text="決定", command=self.submit_input, width=10, font=("Arial", 10))
        self.submit_button.pack(side=tk.LEFT, padx=5)

        # ボタンを格納するスクロール可能なフレーム
        self.button_canvas = tk.Canvas(self.control_frame, borderwidth=0, height=500) # 高さを指定
        self.button_frame = tk.Frame(self.button_canvas)
        self.scrollbar = tk.Scrollbar(self.control_frame, orient="vertical", command=self.button_canvas.yview)
        self.button_canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side=tk.RIGHT, fill="y")
        self.button_canvas.pack(side=tk.LEFT, fill="both", expand=True)
        self.button_canvas.create_window((0, 0), window=self.button_frame, anchor="nw")

        self.button_frame.bind("<Configure>", self.on_frame_configure)
        self.button_canvas.bind_all("<MouseWheel>", self.on_mousewheel) # Windows/Mac
        self.button_canvas.bind_all("<Button-4>", self.on_mousewheel) # Linux (up)
        self.button_canvas.bind_all("<Button-5>", self.on_mousewheel) # Linux (down)

        self.empty_img_tk = tk.PhotoImage(width=100, height=100) # 空のPhotoImageを一度だけ生成

    def on_frame_configure(self, event=None):
        '''Reset the scroll region to encompass the inner frame'''
        self.button_canvas.configure(scrollregion=self.button_canvas.bbox("all"))

    def on_mousewheel(self, event):
        # event.delta は Windows/Mac, event.num は Linux
        if event.num == 4 or event.delta > 0:
            self.button_canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self.button_canvas.yview_scroll(1, "units")

    def update_progress(self, progress_percentage):
        self.root.title(f"画像分類ツール - 進捗: {progress_percentage:.2f}%")

    def display_image(self, img_pil):
        """PIL ImageをTkinterラベルに表示する"""
        try:
            # 画像を指定したフレームに合うようにリサイズ（アスペクト比維持）
            max_width = self.image_frame.winfo_width() - 10 # パディング考慮
            max_height = self.image_frame.winfo_height() - 10
            if max_width <= 0 or max_height <= 0: # 初期状態でサイズ0の場合のデフォルト
                max_width = 400
                max_height = 300

            img_pil.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

            self.img_tk = ImageTk.PhotoImage(img_pil)
            self.image_label.configure(image=self.img_tk, text="") # 画像を設定し、テキストを消去
            self.image_label.image = self.img_tk # 参照を保持
        except Exception as e:
            self.image_label.configure(text=f"画像表示エラー:\n{e}", image=None)
            self.img_tk = None # エラー時は参照をクリア

    def update_buttons(self, name_list, icon_dir_base):
        """候補名のボタンリストを更新する"""
        # 既存のボタンをクリア
        for widget in self.button_frame.winfo_children():
            widget.destroy()

        if not name_list:
            no_options_label = tk.Label(self.button_frame, text="候補なし（新規登録してください）")
            no_options_label.pack(pady=20)
            return

        icon_dir = os.path.join(self.script_dir, icon_dir_base) # アイコンディレクトリのパスを修正

        cols = 5 # 1行あたりのボタン数
        for i, name in enumerate(name_list):
            def on_click_callback(n=name):
                self.select_name(n)

            image_path = os.path.join(icon_dir, f"{name}.png")
            btn_args = {"width": 100, "height": 100, "command": on_click_callback}

            try:
                if os.path.exists(image_path):
                    img = Image.open(image_path)
                    img = img.resize((80, 80), Image.Resampling.LANCZOS) # 少し小さく
                    img_tk = ImageTk.PhotoImage(img)
                    btn_args["image"] = img_tk
                else:
                    # アイコンがない場合はテキストボタン
                    btn_args["text"] = name
                    btn_args["image"] = self.empty_img_tk # 空の画像でサイズを確保
                    btn_args["compound"] = tk.CENTER # テキストを中央に
            except Exception as e:
                print(f"Error loading icon {image_path}: {e}")
                # エラー時はテキストボタン
                btn_args["text"] = name
                btn_args["image"] = self.empty_img_tk
                btn_args["compound"] = tk.CENTER

            btn = tk.Button(self.button_frame, **btn_args)
            if "image" in btn_args and btn_args["image"] != self.empty_img_tk:
                 btn.image = img_tk # ImageTk参照を保持

            row = i // cols
            col = i % cols
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

        # フレーム内の列の重みを設定して均等配置
        for c in range(cols):
            self.button_frame.grid_columnconfigure(c, weight=1)

        # Canvasのスクロール領域を再設定するために少し遅延させる
        self.root.after(100, self.on_frame_configure)

    def select_name(self, name):
        """ボタンクリックで名前を選択"""
        self.user_input = name
        self.input_received.set(True)

    def submit_input(self):
        """決定ボタンで自由入力された名前を取得"""
        value = self.entry.get().strip()
        if value:
            self.user_input = value
            self.input_received.set(True)
        else:
            # 何か入力するように促す（任意）
            messagebox.showwarning("入力エラー", "名前を入力してください。")

    def get_input_for_image(self, img_to_show, name_list, icon_dir_base):
        """画像を表示し、ユーザーからの名前入力を待つ"""
        self.user_input = None # 前回の入力をクリア
        self.entry.delete(0, tk.END) # 入力欄をクリア
        self.input_received.set(False) # フラグをリセット

        # 画像を表示 (GUIスレッドで実行)
        self.root.after(0, self.display_image, img_to_show)
        # ボタンを更新 (GUIスレッドで実行)
        self.root.after(0, self.update_buttons, name_list, icon_dir_base)

        # ユーザーの入力待ち
        print("Waiting for user input in GUI...")
        self.root.wait_variable(self.input_received)
        print(f"Input received: {self.user_input}")

        return self.user_input

# --- メイン処理 ---
def main_processing(gui, script_dir, positions, input_imgs_dir):
    """画像処理のメインループ"""
    try:
        files_input = sorted([f for f in os.listdir(input_imgs_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))])
    except FileNotFoundError:
        messagebox.showerror("エラー", f"入力ディレクトリが見つかりません:\n{input_imgs_dir}")
        gui.root.quit() # GUIを終了
        return
    except Exception as e:
        messagebox.showerror("エラー", f"入力ディレクトリの読み込み中にエラーが発生しました:\n{e}")
        gui.root.quit()
        return

    if not files_input:
        messagebox.showinfo("情報", "処理対象の画像が Screenshots フォルダにありません。")
        gui.root.quit()
        return

    total_files = len(files_input)
    processed_files = 0
    max_tasks = total_files * len(positions)
    completed_tasks = 0

    dt_now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") # 時刻を文字列に

    for input_img_name in files_input:
        input_path = os.path.join(input_imgs_dir, input_img_name)
        try:
            input_img = Image.open(input_path).convert("RGB") # RGBに変換
        except Exception as e:
            print(f"Error opening image {input_img_name}: {e}. Skipping.")
            processed_files += 1
            completed_tasks += len(positions) # このファイルのタスクはスキップ
            continue # 次のファイルへ

        w, h = input_img.size
        data = [None] * len(positions) # 結果格納用リストを初期化
        all_positions_processed = True # この画像の全ポジションが処理できたか

        for idx, position in enumerate(positions):
            try:
                l = int(w * position[0])
                t = int(h * position[1])
                r = int(w * position[2])
                b = int(h * position[3])
                cropped_img = input_img.crop((l, t, r, b))
            except Exception as e:
                 print(f"Error cropping image {input_img_name} for position {idx}: {e}. Skipping position.")
                 all_positions_processed = False
                 completed_tasks += 1
                 gui.update_progress((completed_tasks / max_tasks) * 100)
                 continue # このポジションはスキップ

            match_folder_name = position[-1] # "攻守", "キャラクター" など
            match_img_dir = os.path.join(script_dir, "判定画像", match_folder_name)

            best_match_name = ""
            best_match_score = -1.0

            try:
                if not os.path.exists(match_img_dir):
                     print(f"Warning: Match image directory not found: {match_img_dir}. Creating it.")
                     os.makedirs(match_img_dir)

                files_match = sorted([f for f in os.listdir(match_img_dir) if f.lower().endswith('.png')])

                for img_match_name in files_match:
                    match_img_path = os.path.join(match_img_dir, img_match_name)
                    try:
                        match_img_pil = Image.open(match_img_path).convert("RGB")
                        # サイズ合わせは fx_templatematch 内で行うので削除
                        
                        res = fx_templatematch(cropped_img, match_img_pil)
                        if res > best_match_score:
                            best_match_score = res
                            best_match_name = fx_trim(img_match_name) # 拡張子などを除去した名前
                    except Exception as e:
                        print(f"Error processing match image {img_match_name}: {e}")

            except Exception as e:
                print(f"Error accessing match directory {match_img_dir}: {e}")

            # 閾値判定
            if best_match_score >= 0.9:
                data[idx] = best_match_name
                print(f"Match found for {input_img_name} pos {idx}: {best_match_name} (Score: {best_match_score:.2f})")
            else:
                print(f"Low match score ({best_match_score:.2f}) for {input_img_name} pos {idx}. Requesting user input.")
                # GUIでユーザー入力を求める
                name_list = []
                name_list_file = position[-2] # "攻守.txt", "名前.txt" など
                icon_dir_base = os.path.join("選択肢", "icon") # アイコンのベースディレクトリ

                if name_list_file and isinstance(name_list_file, str): # ファイル名が文字列の場合のみ
                    name_list_path = os.path.join(script_dir, "選択肢", name_list_file)
                    try:
                        with open(name_list_path, 'r', encoding='utf-8') as f:
                            name_list = [line.strip() for line in f if line.strip()]
                    except FileNotFoundError:
                        print(f"Name list file not found: {name_list_path}. Allowing free input only.")
                        name_list = [] # ファイルがなければ空リスト
                    except Exception as e:
                        print(f"Error reading name list file {name_list_path}: {e}")
                        name_list = []

                # GUIに入力を要求
                chosen_name = gui.get_input_for_image(cropped_img, name_list, icon_dir_base)

                if chosen_name:
                    data[idx] = chosen_name
                    # 新しい名前の画像を保存
                    fx_save_trim_img(cropped_img, match_img_dir, chosen_name, 0)
                else:
                    print(f"User did not provide input for {input_img_name} pos {idx}. Skipping position.")
                    data[idx] = "" # 入力がない場合は空文字など
                    all_positions_processed = False # この画像は完全には処理できなかった

            # 進捗更新
            completed_tasks += 1
            gui.update_progress((completed_tasks / max_tasks) * 100)
            gui.root.update_idletasks() # GUIを強制的に更新

        # --- 1画像分の処理完了後 ---
        processed_files += 1

        # data[0]（攻守）とdata[1]（名前）が必須と仮定
        if all_positions_processed and data[0] and data[1]:
            # 攻守判定をパスとして使用
            result_file_prefix = data[0]
            # データを整形
            output_data = [dt_now_str] + data # 先頭にタイムスタンプを追加
            # 元画像を履歴に移動
            moved_filename = fx_move_and_rename(input_path, script_dir)
            if moved_filename:
                output_data.append(moved_filename) # 移動後のファイル名を追加
                # 結果をファイルに追記
                fx_append_txt(result_file_prefix, '\t'.join(map(str, output_data)))
                print(f"Processed and recorded data for {input_img_name}")
            else:
                print(f"Failed to move {input_img_name}. Data not recorded.")
        else:
            print(f"Skipping data recording for {input_img_name} due to missing information or skipped steps.")
            # 必要であれば、未処理ファイルとしてどこかに記録するなどの処理を追加

    messagebox.showinfo("完了", "全てのファイルの処理が終了しました！")
    gui.root.quit() # 処理完了後にGUIを閉じる


# --- 設定 ---
# トリミング用の座標配列 [左, 上, 右, 下, 選択肢ファイル名 or None, 保存フォルダ名]
positions = [
	[0.045, 0.260, 0.085, 0.33, "攻守.txt", "攻守"],
	[0.818, 0.238, 0.970, 0.27, None, "対戦相手"], # フリー入力
	[0.090, 0.260, 0.185, 0.33, "勝敗.txt", "勝敗"],
	[0.085, 0.74, 0.119, 0.80, "ST.txt", "キャラクター"],
	[0.144, 0.74, 0.178, 0.80, "ST.txt", "キャラクター"],
	[0.203, 0.74, 0.237, 0.80, "ST.txt", "キャラクター"],
	[0.262, 0.74, 0.296, 0.80, "ST.txt", "キャラクター"],
	[0.321, 0.74, 0.355, 0.80, "SP.txt", "キャラクター"], 
	[0.380, 0.74, 0.414, 0.80, "SP.txt", "キャラクター"], 
	[0.584, 0.74, 0.618, 0.80, "ST.txt", "キャラクター"],
	[0.642, 0.74, 0.676, 0.80, "ST.txt", "キャラクター"],
	[0.700, 0.74, 0.734, 0.80, "ST.txt", "キャラクター"],
	[0.760, 0.74, 0.794, 0.80, "ST.txt", "キャラクター"],
	[0.819, 0.74, 0.853, 0.80, "SP.txt", "キャラクター"],
	[0.878, 0.74, 0.912, 0.80, "SP.txt", "キャラクター"]
]

# スクリプトのディレクトリを取得
try:
	script_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
		# __file__ が未定義の場合（例: 対話モードや一部のIDE）
		script_dir = os.getcwd()

input_imgs_dir = os.path.join(script_dir, "Screenshots")

# --- GUIの初期化とメイン処理の開始 ---
root = tk.Tk()
gui = ImageClassifierGUI(root, script_dir)

# メイン処理を別スレッドで実行（GUIがフリーズしないように）
processing_thread = threading.Thread(target=main_processing, args=(gui, script_dir, positions, input_imgs_dir), daemon=True)
processing_thread.start()

# Tkinterのメインループを開始
root.mainloop()

print("Application finished.")