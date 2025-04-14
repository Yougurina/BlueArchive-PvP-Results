import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os

class ImageClassifierGUI:
    """
    Tkinterを使用して画像分類ツールのグラフィカルユーザーインターフェース (GUI) を管理します。
    画像を表示し、分類オプションをボタンとして提示し、ユーザー入力を処理します。
    """
    def __init__(self, root, script_dir):
        """
        GUIコンポーネントを初期化します。

        Args:
            root (tk.Tk): メインのTkinterウィンドウ (root)。
            script_dir (str): アプリケーションスクリプトのベースディレクトリ。
        """
        self.root = root
        self.script_dir = script_dir
        self.root.title("画像分類ツール")
        self.root.geometry("800x700") # 初期ウィンドウサイズ

        # --- 状態変数 ---
        self.user_input = None # ユーザーが選択/入力した名前を格納
        self.input_received = tk.BooleanVar(value=False) # 待機できるフラグとして機能します (wait_variable)
        self.img_tk = None # 現在表示されているImageTkオブジェクトへの参照を保持
        self.empty_img_tk = tk.PhotoImage(width=100, height=100) # 画像ボタン用のフレーム

        # --- GUIレイアウト ---
        # 上部フレーム: 分類対象の画像を表示するため
        self.image_frame = tk.Frame(root, bg="#ECECEC", bd=2, relief=tk.SUNKEN, height=250)
        # 子ウィジェットがフレームのサイズを変更しないようにする
        self.image_frame.pack_propagate(False)
        # フレームをパック (垂直方向の伸縮は抑制)
        self.image_frame.pack(pady=10, padx=10, fill=tk.X, expand=False)

        # 画像フレーム内のラベル: 画像またはステータステキストを表示
        self.image_label = tk.Label(self.image_frame, text="画像待機中...", bg="#ECECEC", anchor="center")
        self.image_label.pack(expand=True, fill=tk.BOTH)

        # 下部フレーム: コントロール用 (入力フィールド、ボタン)
        # 利用可能な残りの垂直スペースを埋めるように調整
        self.control_frame = tk.Frame(root)
        self.control_frame.pack(pady=(0, 10), padx=10, fill=tk.BOTH, expand=True)

        # 入力フレーム: テキスト入力と送信ボタンを含む (control_frame内)
        self.input_frame = tk.Frame(self.control_frame)
        self.input_frame.pack(pady=5, fill=tk.X) # 水平方向にフィル

        # 入力ラベル
        self.entry_label = tk.Label(self.input_frame, text="新規登録名:")
        self.entry_label.pack(side=tk.LEFT, padx=5)

        # 入力フィールド
        self.entry = tk.Entry(self.input_frame, width=40, font=("Arial", 12))
        # 入力フィールドが水平方向に伸縮するようにする
        self.entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        # 送信ボタン
        self.submit_button = tk.Button(self.input_frame, text="決定", command=self.submit_input, width=10, font=("Arial", 10))
        self.submit_button.pack(side=tk.LEFT, padx=5)
        # Enterキーを送信アクションにバインド
        self.entry.bind("<Return>", lambda event: self.submit_input())

        # スクロール可能領域フレーム: CanvasとScrollbarを含む (control_frame内)
        self.scrollable_area_frame = tk.Frame(self.control_frame)
        self.scrollable_area_frame.pack(pady=5, fill=tk.BOTH, expand=True)

        # ボタン用スクロール可能フレーム: 多くのボタンをUIを乱雑にせずに表示可能
        # 外側のキャンバス: ボタンフレームを保持し、スクロールを有効にする
        self.button_canvas = tk.Canvas(self.scrollable_area_frame, borderwidth=0, background="#ffffff")
        # 垂直スクロールバー: キャンバスにリンク
        self.scrollbar = tk.Scrollbar(self.scrollable_area_frame, orient="vertical", command=self.button_canvas.yview)
        self.button_canvas.configure(yscrollcommand=self.scrollbar.set)

        # スクロールバーとキャンバスをscrollable_area_frame内にパック
        self.scrollbar.pack(side=tk.RIGHT, fill="y")
        self.button_canvas.pack(side=tk.LEFT, fill="both", expand=True)

        # 内側のフレーム: キャンバス内に配置され、実際のボタンを保持
        self.button_frame = tk.Frame(self.button_canvas, background="#ffffff")
        # ボタンフレームをキャンバスウィンドウに追加し、ウィンドウIDを保存
        self.canvas_window = self.button_canvas.create_window((0, 0), window=self.button_frame, anchor="nw")

        # --- イベントバインディング ---
        # ボタンフレームのサイズが変更されたときにスクロール領域を更新
        self.button_frame.bind("<Configure>", self.on_frame_configure)

        # キャンバスのサイズが変更されたときにキャンバスウィンドウの幅を調整
        self.button_canvas.bind("<Configure>", self.on_canvas_configure)

        # button_canvasウィジェットに直接バインド
        self.button_canvas.bind("<MouseWheel>", self.on_mousewheel)
        # button_frame自体にもバインド
        self.button_frame.bind("<MouseWheel>", self.on_mousewheel)


    def on_canvas_configure(self, event):
        """キャンバス内のフレームの幅をキャンバスの幅に合わせて調整します。"""
        canvas_width = event.width
        # 保存されたウィンドウID (self.canvas_window) を使用してアイテムを設定
        self.button_canvas.itemconfig(self.canvas_window, width=canvas_width)


    def on_frame_configure(self, event=None):
        """キャンバスのスクロール領域をボタンフレームに合わせて更新します。"""
        self.button_canvas.configure(scrollregion=self.button_canvas.bbox("all"))

    def on_mousewheel(self, event):
        """ボタンキャンバスのマウスホイールスクロールを処理します (Windows専用)。"""
        # Windowsはdeltaを120の倍数で送信します
        delta = -1 * int(event.delta / 120)
        if delta:
            self.button_canvas.yview_scroll(delta, "units")


    def update_progress(self, progress_percentage):
        """ウィンドウタイトルを更新して現在の処理進捗を表示します。"""
        self.root.title(f"画像分類ツール - 進捗: {progress_percentage:.2f}%")

    def display_image(self, img_pil):
        """
        PIL Imageオブジェクトをimage_labelに表示します。
        アスペクト比を維持しながら利用可能なスペースに合わせて画像をリサイズします。

        Args:
            img_pil (PIL.Image.Image): 表示する画像。
        """
        try:
            # フレームサイズが計算される前にUIイベントを処理
            self.image_frame.update_idletasks()
            # 画像に利用可能なフレームの現在のサイズを取得
            # より正確なフィッティングのためにパディング/ボーダー幅を減算
            max_width = self.image_frame.winfo_width() - 10
            max_height = self.image_frame.winfo_height() - 10

            # フレームサイズが0以下の場合の処理
            if max_width <= 0: max_width = 200 # 最小フォールバック幅
            if max_height <= 0: max_height = 150 # 最小フォールバック高さ

            # 元の画像を変更しないようにコピーを作成
            img_copy = img_pil.copy()
            # thumbnailを使用して画像をリサイズ (アスペクト比を維持)
            # LANCZOSは高品質なダウンサンプリングフィルターです
            img_copy.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

            # (リサイズされた可能性のある) PIL画像をTkinter PhotoImageに変換
            self.img_tk = ImageTk.PhotoImage(img_copy)

            # ラベルを設定して新しい画像を表示し、以前のテキストをクリア
            self.image_label.configure(image=self.img_tk, text="")
            # ガベージコレクションを防ぐためにPhotoImageオブジェクトへの参照を保持
            self.image_label.image = self.img_tk

        except Exception as e:
            # 画像表示中にエラーが発生した場合はエラーメッセージを表示
            error_text = f"画像表示エラー:\n{e}"
            self.image_label.configure(text=error_text, image=None) # 画像をクリア
            self.img_tk = None # 参照をクリア

    def update_buttons(self, name_list, icon_dir_base):
        """
        既存のボタンをクリアし、提供された名前リストに基づいて新しいボタンを作成します。
        指定されたアイコンディレクトリから各ボタンのアイコンをロードしようとします。

        Args:
            name_list (list[str]): ボタンの名前のリスト。
            icon_dir_base (str): アイコン画像のベースパス (script_dirからの相対パス、例: "選択肢/icon")。
        """
        # button_frame内の現在のボタンをすべてクリア
        for widget in self.button_frame.winfo_children():
            widget.destroy()

        # 名前リストが空の場合、メッセージを表示
        if not name_list:
            no_options_label = tk.Label(self.button_frame, text="候補なし（新規登録してください）", background="#ffffff")
            no_options_label.pack(pady=20)
            no_options_label.bind("<MouseWheel>", self.on_mousewheel)
            # 空の場合でもスクロール領域を更新
            self.root.after(100, self.on_frame_configure)
            return

        # アイコンディレクトリへのフルパスを構築
        icon_dir = os.path.join(self.script_dir, icon_dir_base)

        cols = 5 # 1行あたりのボタン数
        button_widgets = [] # 作成されたボタンを追跡

        for i, name in enumerate(name_list):
            # 各ボタンのコールバックで正しい 'name' をキャプチャするためにラムダでデフォルト引数を使用
            def on_click_callback(n=name):
                self.select_name(n)

            # アイコン画像の期待されるパスを構築
            image_path = os.path.join(icon_dir, f"{name}.png")

            # ボタン設定引数
            btn_args = {
                "width": 100,      # 固定幅
                "height": 100,     # 固定高さ
                "command": on_click_callback,
                "compound": tk.TOP, # デフォルト: 画像とテキスト両方あれば画像が上
                "text": name,       # 常にテキストを初期設定
                "font": ("Arial", 8) # ボタンテキスト用の小さいフォント
            }
            img_tk_ref = None # このボタンのImageTk参照を格納するため

            try:
                if os.path.exists(image_path):
                    # アイコンが存在すればロード
                    img = Image.open(image_path)
                    # ボタンに合わせてアイコンをリサイズ (例: 80x80)
                    img = img.resize((80, 80), Image.Resampling.LANCZOS)
                    img_tk_ref = ImageTk.PhotoImage(img)
                    btn_args["image"] = img_tk_ref
                    btn_args["text"] = name # テキストを画像の下に保持
                else:
                    # アイコンがない場合、サイズ/レイアウト維持のためにプレースホルダー空画像を使用
                    btn_args["image"] = self.empty_img_tk
                    # 実際の画像がない場合はテキストを中央揃え
                    btn_args["compound"] = tk.CENTER

            except Exception as e:
                # アイコンロード中のエラー処理 (例: 破損ファイル)
                print(f"アイコン {image_path} のロードエラー: {e}")
                # サイズ維持のためにプレースホルダーを使用してテキストのみのボタンにフォールバック
                btn_args["image"] = self.empty_img_tk
                btn_args["compound"] = tk.CENTER

            # ボタンを作成
            btn = tk.Button(self.button_frame, **btn_args)
            # ガベージコレクションを防ぐためにImageTk参照をボタンオブジェクト自体に格納
            if img_tk_ref:
                 btn.image = img_tk_ref

            # 各ボタンに個別にマウスホイールをバインド
            btn.bind("<MouseWheel>", self.on_mousewheel)

            # グリッドレイアウトにボタンを配置
            row = i // cols
            col = i % cols
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            button_widgets.append(btn)

        # button_frame内の列が均等に伸縮するように設定
        if button_widgets: # ボタンが追加された場合のみ設定
            # ボタンが配置された最大の列番号+1を計算
            num_cols = max(b.grid_info()['column'] for b in button_widgets) + 1
            for c in range(num_cols):
                # weight=1で伸縮可能に、uniformで均等に
                self.button_frame.grid_columnconfigure(c, weight=1, uniform="button_col")

        # レイアウトが更新された後にスクロール領域を更新する呼び出しをスケジュール
        self.root.after(100, self.on_frame_configure)

    def select_name(self, name):
        """
        候補ボタンがクリックされたときに呼び出されます。選択された名前を格納し、
        入力が受信されたことを示すフラグを設定します。
        """
        print(f"ボタンクリック: {name}")
        self.user_input = name
        self.input_received.set(True) # 入力が準備完了したことを通知

    def submit_input(self):
        """
        '決定' ボタンがクリックされたとき、または入力フィールドでEnterが押されたときに呼び出されます。
        入力されたテキストを格納し、フラグを設定します。
        """
        value = self.entry.get().strip() # 入力からテキストを取得し、空白を削除
        if value:
            print(f"テキスト入力送信: {value}")
            self.user_input = value
            self.input_received.set(True) # 入力が準備完了したことを通知
        else:
            messagebox.showwarning("入力エラー", "名前を入力してください。")

    def get_input_for_image(self, img_to_show, name_list, icon_dir_base):
        """
        画像を表示し、候補ボタンを更新し、ユーザーがボタンをクリックするか、
        テキストを入力して '決定' をクリックするのを待ちます。

        このメソッドは入力が受信されるまで実行をブロックします (wait_variableを使用)。

        Args:
            img_to_show (PIL.Image.Image): 分類のために表示する画像。
            name_list (list[str]): ボタンの候補名のリスト。
            icon_dir_base (str): ボタンアイコンのベースパス。

        Returns:
            str | None: ユーザーが選択または入力した名前。入力ループが予期せず中断された場合はNone。
        """
        # 新しい入力リクエストのために状態をリセット
        self.user_input = None
        self.entry.delete(0, tk.END) # テキスト入力フィールドをクリア
        self.input_received.set(False) # 入力受信フラグをリセット

        # GUI更新をメインTkinterスレッドで実行するようにスケジュール ('after(0, ...)'を使用)
        self.root.after(0, self.display_image, img_to_show)
        self.root.after(0, self.update_buttons, name_list, icon_dir_base)

        # input_receivedフラグ (BooleanVar) がTrueに設定されるまで待機
        print("GUIでユーザー入力を待機中...")
        # 必要に応じてウィンドウを一時的にモーダルにする
        self.root.grab_set()
        self.root.wait_variable(self.input_received)
        # モーダル状態を解除
        self.root.grab_release()
        print(f"入力受信: {self.user_input}")

        # 格納されたユーザー入力を返す
        return self.user_input