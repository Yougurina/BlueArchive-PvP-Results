import os
import datetime
from PIL import Image
import tkinter.messagebox as messagebox

# --- 相対インポートを使用して同じパッケージ内のモジュールをインポート ---
# 同じ 'src' パッケージ内の image_utils.py からユーティリティ関数をインポート
from .image_utils import (fx_templatematch, fx_trim, fx_append_txt,
                          fx_move_and_rename, fx_save_trim_img)

# --- メイン処理ロジック ---

def main_processing(gui, script_dir, positions, input_imgs_dir):
    """
    入力ディレクトリ内の画像を処理するためのメインワークフロー。
    画像を反復処理し、「positions」に基づいてセクションをトリミングし、
    マッチングを試みるか、GUIを介してユーザー入力を取得し、結果を保存し、
    処理済みファイルを移動します。

    Args:
        gui (ImageClassifierGUI): ユーザーと対話するためのGUIクラスのインスタンス。
        script_dir (str): アプリケーションのルートディレクトリ (main.py がある場所)。
                          これは「判定画像」、「選択肢」などのデータフォルダへのアクセスに使用されます。
        positions (list): トリミング領域と関連情報を定義するリスト。
        input_imgs_dir (str): 入力画像を含むディレクトリへのパス
                              (通常は script_dir + "/Screenshots")。
    """
    try:
        # 入力ディレクトリから画像ファイルのソート済みリストを取得
        valid_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
        files_input = sorted([
            f for f in os.listdir(input_imgs_dir)
            if f.lower().endswith(valid_extensions)
        ])
    except FileNotFoundError:
        # 入力ディレクトリが存在しない場合のエラー
        messagebox.showerror("エラー", f"入力ディレクトリが見つかりません:\n{input_imgs_dir}")
        gui.root.quit() # GUIを閉じる
        return # 処理を停止
    except Exception as e:
        # ディレクトリリスト中の他の潜在的なエラーを処理
        messagebox.showerror("エラー", f"入力ディレクトリの読み込み中にエラーが発生しました:\n{e}")
        gui.root.quit()
        return

    # 処理する画像があるか確認
    if not files_input:
        messagebox.showinfo("情報", f"{os.path.basename(input_imgs_dir)} フォルダに処理対象の画像がありません。")
        gui.root.quit()
        return

    # --- 進捗追跡のための初期化 ---
    total_files = len(files_input)
    processed_files_count = 0
    # 合計タスク数 = ファイル数 * ファイルあたりのポジション数
    total_tasks = total_files * len(positions)
    completed_tasks = 0

    # この実行でのすべての結果に対して現在のタイムスタンプを一度取得
    dt_now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"{total_files} 個の画像の処理を開始します...")

    # --- メインループ: 各入力画像を反復処理 ---
    for input_img_name in files_input:
        input_path = os.path.join(input_imgs_dir, input_img_name)
        print(f"\n画像を処理中: {input_img_name}")

        try:
            # PILを使用して画像を開き、RGB形式であることを確認
            input_img = Image.open(input_path).convert("RGB")
        except Exception as e:
            # 画像ファイルを開く際のエラーを処理 (例: 破損ファイル)
            print(f"画像 {input_img_name} を開くエラー: {e}。スキップします。")
            processed_files_count += 1
            # このファイルのすべてのタスクが進捗計算のためにスキップされたと仮定
            completed_tasks += len(positions)
            # 進捗をすぐに更新
            gui.update_progress((completed_tasks / max(total_tasks, 1)) * 100)
            gui.root.update_idletasks() # GUI更新を強制
            continue # 次のファイルへ

        # 画像の寸法を取得
        w, h = input_img.size
        # 各ポジションの分類結果を格納するリストを初期化
        data = [None] * len(positions)
        # 現在の画像のすべてのポジションが正常に処理されたかどうかを追跡するフラグ
        all_positions_processed_successfully = True

        # --- 内部ループ: 現在の画像の各定義済みポジションを反復処理 ---
        for idx, position_info in enumerate(positions):
            # ポジションの詳細を抽出: 座標、選択肢ファイル、保存フォルダ名
            try:
                l_rel, t_rel, r_rel, b_rel, choice_file, save_folder_name = position_info
                # 相対値から絶対ピクセル座標を計算
                l_abs = int(w * l_rel)
                t_abs = int(h * t_rel)
                r_abs = int(w * r_rel)
                b_abs = int(h * b_rel)
                # 画像をトリミング
                cropped_img = input_img.crop((l_abs, t_abs, r_abs, b_abs))
            except Exception as e:
                # トリミング中のエラーを処理 (例: 無効な座標)
                print(f"画像 {input_img_name} のポジション {idx} のトリミングエラー: {e}。ポジションをスキップします。")
                all_positions_processed_successfully = False # 未完了としてマーク
                completed_tasks += 1 # とにかく完了タスクをインクリメント
                gui.update_progress((completed_tasks / max(total_tasks, 1)) * 100)
                gui.root.update_idletasks()
                continue # 次のポジションへ

            # --- テンプレートマッチング ---
            # このポジションタイプの参照画像を含むディレクトリ
            # データフォルダを見つけるために script_dir (main.pyから渡され、ルートを指す) を使用
            match_img_dir = os.path.join(script_dir, "判定画像", save_folder_name)

            best_match_name = ""
            best_match_score = -1.0 # 可能なマッチよりも低いスコアで初期化

            try:
                # マッチングディレクトリが存在しない場合は作成
                if not os.path.exists(match_img_dir):
                    print(f"警告: マッチ画像ディレクトリが見つかりません: {match_img_dir}。作成します。")
                    os.makedirs(match_img_dir)

                # ディレクトリ内の既存の参照画像のリストを取得
                files_match = sorted([
                    f for f in os.listdir(match_img_dir)
                    if f.lower().endswith('.png')
                ])

                # トリミングされた画像を各参照画像と比較
                for img_match_name in files_match:
                    match_img_path = os.path.join(match_img_dir, img_match_name)
                    try:
                        # 参照画像を開く
                        match_img_pil = Image.open(match_img_path).convert("RGB")
                        # インポートされた関数を使用して類似度スコアを計算
                        res = fx_templatematch(cropped_img, match_img_pil)

                        # 現在のスコアが高い場合はベストマッチを更新
                        if res > best_match_score:
                            best_match_score = res
                            # マッチのベース名 (拡張子/_numなし) を取得
                            best_match_name = fx_trim(img_match_name)
                    except Exception as e:
                        # 特定の参照画像を処理する際のエラーを処理
                        print(f"マッチ画像 {img_match_name} の処理エラー: {e}")

            except Exception as e:
                # マッチディレクトリ自体へのアクセスエラーを処理
                print(f"マッチディレクトリ {match_img_dir} へのアクセスエラー: {e}")

            # --- 決定: マッチを使用するかユーザーに尋ねる ---
            match_threshold = 0.9 # 自動マッチングの信頼度しきい値
            if best_match_score >= match_threshold:
                # 高信頼度のマッチが見つかりました
                data[idx] = best_match_name
                print(f"  Pos {idx} ({save_folder_name}): マッチ発見 - '{best_match_name}' (スコア: {best_match_score:.3f})")
            else:
                # 低信頼度またはマッチなし、GUIを介してユーザーに尋ねる
                print(f"  Pos {idx} ({save_folder_name}): 低スコア ({best_match_score:.3f})。ユーザー入力を要求します。")

                # --- ユーザー入力の準備 ---
                name_list = [] # ボタン用の事前定義された選択肢のリスト
                # このポジションに選択肢ファイルが指定されているか確認
                if choice_file and isinstance(choice_file, str):
                    # "選択肢" フォルダを見つけるために script_dir (ルート) を使用
                    name_list_path = os.path.join(script_dir, "選択肢", choice_file)
                    try:
                        # 選択肢ファイルから名前を読み取る
                        with open(name_list_path, 'r', encoding='utf-8') as f:
                            name_list = [line.strip() for line in f if line.strip()]
                        print(f"      {choice_file} から {len(name_list)} 個の選択肢をロードしました")
                    except FileNotFoundError:
                        print(f"      選択肢リストファイルが見つかりません: {name_list_path}。フリー入力のみ許可します。")
                        name_list = [] # ファイルが見つからない場合は空リストを保証
                    except Exception as e:
                        print(f"      選択肢リストファイル {name_list_path} の読み取りエラー: {e}")
                        name_list = []

                # ボタンアイコンのベースディレクトリ (ルート内の相対パス)
                icon_dir_base = os.path.join("選択肢", "icon")

                # --- GUIを呼び出して入力を取得 ---
                chosen_name = gui.get_input_for_image(cropped_img, name_list, icon_dir_base)

                if chosen_name:
                    # ユーザーが名前を入力
                    data[idx] = chosen_name
                    print(f" 入力値: '{chosen_name}'")

                    # --- マッチングディレクトリ (判定画像) に保存 ---
                    # この保存操作は必要に応じてまだ番号を追記します (最初はnum=0)
                    fx_save_trim_img(cropped_img, match_img_dir, chosen_name, 0)

                    # --- アイコンディレクトリ (選択肢/icon) に保存 - 条件付き ---
                    # "対戦相手"カテゴリの場合はアイコン保存をスキップ
                    if save_folder_name != "対戦相手":
                        # script_dir (ルート) を使用してアイコン保存パスを計算
                        icon_save_path = os.path.join(script_dir, icon_dir_base)
                        # 正確なターゲットアイコンファイル名を定義
                        target_icon_filename = f"{chosen_name}.png"
                        target_icon_full_path = os.path.join(icon_save_path, target_icon_filename)

                        # アイコンファイルが既に存在するか確認
                        if not os.path.exists(target_icon_full_path):
                            # アイコンが存在しない場合にのみ保存
                            print(f"      新しいアイコンを保存中: {target_icon_full_path}")
                            # num=0でfx_save_trim_imgを呼び出す。ベースファイルが存在しないことを
                            # 既に知っているので、番号は追記されません。
                            # 必要に応じてディレクトリ作成も処理します。
                            fx_save_trim_img(cropped_img, icon_save_path, chosen_name, 0)
                        else:
                            # アイコンは既に存在します。上書きしたり、番号付きで保存したりしないでください。
                            print(f"      アイコンは既に存在します: {target_icon_full_path}。アイコンの保存をスキップします。")
                    else:
                        # 対戦相手カテゴリの場合はアイコン保存をスキップする
                        print(f"      対戦相手カテゴリなので、アイコンの保存をスキップします: {chosen_name}")

                else:
                    # ユーザーはおそらく入力プロンプトを閉じたかキャンセルしました
                    print(f"      ユーザーはポジション {idx} の入力を提供しませんでした。スキップします。")
                    data[idx] = "" # 不足データを示すために空文字列またはNoneを格納
                    all_positions_processed_successfully = False # 未完了としてマーク

            # --- 進捗更新 ---
            completed_tasks += 1
            current_progress = (completed_tasks / max(total_tasks, 1)) * 100
            # GUIスレッドで進捗更新をスケジュール
            gui.root.after(0, gui.update_progress, current_progress)
            # 保留中のイベント (GUI更新など) をTkinterに処理させる
            gui.root.update_idletasks()

        # --- 現在の画像の後処理 ---
        processed_files_count += 1
        print(f"{input_img_name} のポジション処理完了。結果: {data}")

        # --- 結果の記録とファイルの移動 ---
        # すべての必須データが収集されたか確認 (例: 最初の2つのポジションが必須と仮定)
        if all_positions_processed_successfully and data[0] and data[1]:
            # 結果ファイル名の一部として最初のポジションの結果 (例: "攻守") を使用
            result_file_prefix = data[0]
            # データ行を準備: タイムスタンプ + すべての収集データ
            output_data = [dt_now_str] + data

            # 元の入力画像を「履歴」フォルダに移動
            # 履歴フォルダのベースとして script_dir (ルート) を使用
            moved_filename = fx_move_and_rename(input_path, script_dir)

            if moved_filename:
                # 履歴フォルダ内の新しいファイル名をデータに追加
                output_data.append(moved_filename)
                # テキストファイル用にタブでデータ項目を結合
                output_line = '\t'.join(map(str, output_data[0:1] + output_data[2:]))
                # 結果行を適切な結果ファイルに追記
                fx_append_txt(result_file_prefix, output_line, script_dir)
                print(f"  データを記録し、'{input_img_name}' を履歴に '{moved_filename}' として移動しました。")
            else:
                # ファイルの移動に失敗しました。結果を完全に記録できません。
                print(f"  {input_img_name} の移動に失敗しました。データは記録されませんでした。")
                # 必要に応じて、移動されなかったファイルを処理するためのロジックをここに追加することを検討
        else:
            # データが不完全またはステップがスキップされた場合は記録をスキップ
            print(f"  情報不足またはスキップされたステップのため、{input_img_name} のデータ記録をスキップします。")
            # オプションで、これらのファイルを別の「失敗」または「未完了」フォルダに移動

    # --- ファイナライズ ---
    print("\nすべてのファイル処理が終了しました。")
    # 完了メッセージボックスを表示 (GUIスレッドでスケジュール)
    gui.root.after(0, messagebox.showinfo, "完了", "全てのファイルの処理が終了しました！")
    # GUI終了をメインスレッドでスケジュール
    gui.root.after(100, gui.root.quit) # 終了する前に少し遅延を追加
