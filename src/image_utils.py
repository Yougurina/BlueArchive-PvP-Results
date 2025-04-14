import os
import cv2
import numpy
import shutil
from PIL import Image

# --- 画像処理関数 ---

def fx_templatematch(img1_pil, img2_pil):
    """
    テンプレートマッチングを使用して2つの画像の類似度を計算します。
    サイズが異なる場合には、大きい画像の中に小さい画像がマッチするかを判定します。

    Args:
        img1_pil (PIL.Image.Image): 第一画像。
        img2_pil (PIL.Image.Image): 第二画像。

    Returns:
        float: 類似度スコア。-1.0 から 1.0 の範囲。エラー時は -1.0 を返す。
    """
    try:
        # PIL画像をOpenCV形式 (BGR) に変換
        img1_cv = cv2.cvtColor(numpy.array(img1_pil), cv2.COLOR_RGB2BGR)
        img2_cv = cv2.cvtColor(numpy.array(img2_pil), cv2.COLOR_RGB2BGR)

        # グレースケールに変換
        img1_gray = cv2.cvtColor(img1_cv, cv2.COLOR_BGR2GRAY)
        img2_gray = cv2.cvtColor(img2_cv, cv2.COLOR_BGR2GRAY)

        # 寸法を取得
        h1, w1 = img1_gray.shape
        h2, w2 = img2_gray.shape

        # 寸法が0の画像がないかチェック
        if h1 == 0 or w1 == 0 or h2 == 0 or w2 == 0:
             print(f"警告: ゼロ次元の画像が検出されました。 Img1: {img1_gray.shape}, Img2: {img2_gray.shape}")
             return -1.0

        # サイズが同じ場合
        if h1 == h2 and w1 == w2:
            # 直接比較
            result = cv2.matchTemplate(img1_gray, img2_gray, cv2.TM_CCOEFF_NORMED)
            return result[0][0]
        else:
            # サイズが異なる場合、大きい画像の中に小さい画像がマッチするか判定
            if h1 * w1 >= h2 * w2:  # img1が大きい場合
                large_img = img1_gray
                small_img = img2_gray
            else:  # img2が大きい場合
                large_img = img2_gray
                small_img = img1_gray
            
            # テンプレートマッチングを実行（小さい画像を大きい画像の中で探す）
            result = cv2.matchTemplate(large_img, small_img, cv2.TM_CCOEFF_NORMED)
            # 最大値を取得
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            return max_val

    except cv2.error as e:
        print(f"テンプレートマッチング中のOpenCVエラー: {e}")
        print(f"画像1の形状: {img1_pil.size}, 画像2の形状: {img2_pil.size}")
        # エラーの場合は低い類似度スコアを返す
        return -1.0
    except Exception as e:
        print(f"テンプレートマッチング中の予期せぬエラー: {e}")
        return -1.0


def fx_trim(name):
    """
    ファイル名から拡張子と末尾の '_<数字>' を削除します。

    Args:
        name (str): 入力ファイル名 (例: "image_1.png", "character.jpg")。

    Returns:
        str: ベース名 (例: "image", "character")。
    """
    base_name = os.path.splitext(name)[0] # 拡張子を削除
    parts = base_name.split('_')
    # 区切り字で分割して、後者が連番になっているかチェック
    if len(parts) > 1 and parts[-1].isdigit():
        return '_'.join(parts[:-1]) # 末尾の連番を削除
    return base_name


def fx_append_txt(result_file_prefix, text, script_dir):
    """
    リザルトに転記
    ファイル名は "リザルト_{result_file_prefix}.txt" として構築されます。

    Args:
        result_file_prefix (str): 結果ファイル名のプレフィックス (例: "攻守")。
        text (str): 追記するテキスト行。
        script_dir (str): スクリプトが実行されているベースディレクトリ。
    """
    file_path = os.path.join(script_dir, f"リザルト_{result_file_prefix}.txt")
    try:
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(text + '\n')
    except Exception as e:
        print(f"ファイル {file_path} への追記エラー: {e}")


def fx_move_and_rename(img_path, output_dir_base):
    """
    リザルトの元画像を「履歴」フォルダに移動。
    連番でリネームします (例: 00001.png, 00002.png, ...)。

    Args:
        img_path (str): 移動する画像ファイルのフルパス。
        output_dir_base (str): '履歴' フォルダが存在するべきベースディレクトリ。

    Returns:
        str | None: 成功した場合は新しいファイル名 (例: "00001.png")、それ以外は None。
    """
    output_dir = os.path.join(output_dir_base, "履歴")
    try:
        # 履歴ディレクトリが存在しない場合は作成
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"ディレクトリを作成しました: {output_dir}")

        # 既存のファイルをチェックして次のシーケンス番号を決定
        existing_files = [f for f in os.listdir(output_dir)
                          if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
        num = len(existing_files) + 1
        # 番号を先行ゼロでフォーマット (例: 00001) し、.png 拡張子を追加
        base_name = str(num).zfill(5)
        output_filename = base_name + ".png"
        output_path = os.path.join(output_dir, output_filename)

        # ターゲットファイル名が何らかの理由で既に存在しないことを確認
        while os.path.exists(output_path):
             num += 1
             base_name = str(num).zfill(5)
             output_filename = base_name + ".png"
             output_path = os.path.join(output_dir, output_filename)
             if num > len(existing_files) + 1000: # 安全停止
                 print(f"エラー: 履歴フォルダ内で {img_path} の一意な名前が見つかりませんでした")
                 return None

        # ファイルを移動
        shutil.move(img_path, output_path)
        print(f"'{os.path.basename(img_path)}' を '{output_path}' に移動しました")
        return output_filename # 新しいファイル名を返す

    except FileNotFoundError:
        print(f"エラー: 移動元のファイルが見つかりません: {img_path}")
        return None
    except Exception as e:
        print(f"ファイル {img_path} を {output_dir} へ移動/リネーム中にエラー: {e}")
        return None


def fx_save_trim_img(img_pil, save_folder_path, name, num=0):
    """
    トリミングされた画像を特定のフォルダに保存します。
    ファイル名の衝突の可能性を '_<数字>' を追記することで処理します。

    Args:
        img_pil (PIL.Image.Image): 保存するPIL画像オブジェクト。
        save_folder_path (str): 画像を保存するディレクトリパス。
        name (str): 画像ファイルの希望するベース名 (拡張子なし)。
        num (int): 必要に応じてファイル名に追記する開始番号 (デフォルト 0)。

    Returns:
        str | None: 成功した場合に実際に保存されたファイル名 (例: "new_name_1.png")、
                    それ以外は None。
    """
    if not name: # 名前が空の場合は保存しない
        print("警告: 画像保存用に空の名前が指定されました。保存をスキップします。")
        return None

    # PNGとして保存する前に画像がRGB形式であることを確認
    if img_pil.mode != 'RGB':
        img_pil = img_pil.convert('RGB')

    img_name_base = name
    # 初期のファイル名構築
    img_name = f"{img_name_base}_{num}.png" if num > 0 else f"{img_name_base}.png"
    save_path = os.path.join(save_folder_path, img_name)

    # ターゲットディレクトリが存在しない場合は作成
    if not os.path.exists(save_folder_path):
        try:
            os.makedirs(save_folder_path)
            print(f"ディレクトリを作成しました: {save_folder_path}")
        except Exception as e:
            print(f"ディレクトリ {save_folder_path} の作成エラー: {e}")
            return None # ディレクトリ作成に失敗した場合は保存できない

    # ファイル名の衝突をチェックし、必要に応じて番号をインクリメント
    current_num = num
    while os.path.exists(save_path):
        current_num += 1
        img_name = f"{img_name_base}_{current_num}.png"
        save_path = os.path.join(save_folder_path, img_name)
        # 潜在的な無限ループを防ぐための安全停止
        if current_num > num + 1000:
             print(f"警告: {save_folder_path} 内で {img_name_base} の一意なファイル名を1000回試行しても見つけられませんでした。保存をスキップします。")
             return None

    try:
        # 画像を保存
        img_pil.save(save_path, "PNG") # 明示的にPNGとして保存
        print(f"画像を保存しました: {save_path}")
        return os.path.basename(save_path) # 実際に保存されたファイル名を返す
    except Exception as e:
        print(f"画像 {save_path} への保存エラー: {e}")
        return None