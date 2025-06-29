import os
import json

from InquirerPy import inquirer
from src import positions
from rich.pretty import pprint

# --- グローバル定義 ---
BASE_DIR = os.path.dirname(__file__)
PATH = os.path.join(BASE_DIR, "src", "positions_preset.json")


def main():
    """
    メイン処理。
    座標プリセット保存用JSONファイルを保証 → 読み込み → ユーザー操作のループ処理
    """
    # 座標プリセット保存用JSONファイルが無いならば生成
    ensure_positions_preset()
    positions_preset = load_positions_preset()

    while True:
        mode = inquirer.select(
            message="実行内容を選択:",
            choices=[
                "座標データをプリセットへ追加",
                "任意のプリセットを削除",
                "全てのプリセットを削除",
                "現在のプリセット一覧を表示",
                "終了",
            ],
        ).execute()

        if mode == "座標データをプリセットへ追加":
            key = input("プリセット名を入力：")
            if key in positions_preset:
                print("既に同じ名前のプリセットが存在します\n")
            else:
                positions_preset[key] = positions.positions  # 座標データ取得
                append_positions_preset(positions_preset)
                print(f"プリセット '{key}' の作成に成功しました\n")

        elif mode == "任意のプリセットを削除":
            if not positions_preset:
                print("既にプリセットが存在しません\n")
            else:
                key = inquirer.select(
                    message="削除するプリセットを選択:", choices=list(positions_preset)
                ).execute()
                delete_positions_preset(positions_preset, key)
                print(f"プリセット '{key}' の削除に成功しました\n")

        elif mode == "全てのプリセットを削除":
            if not positions_preset:
                print("既にプリセットが存在しません\n")
            else:
                flag = inquirer.select(
                    message="本当に全てのプリセットを削除しますか？",
                    choices=["Yes", "No"],
                ).execute()
                if flag == "Yes":
                    reset_positions_preset(positions_preset)
                    print("全てのプリセットの削除に成功しました\n")
                else:
                    print("全てのプリセットの削除を中止しました\n")

        elif mode == "現在のプリセット一覧を表示":
            if positions_preset == {}:
                print("プリセットが存在しません\n")
            else:
                pprint(positions_preset)
                print()  # 可動性向上のための改行

        # 終了処理
        else:
            break


def ensure_positions_preset():
    """
    JSONファイルが存在しない場合、辞書型の空ファイルを生成
    """
    if not os.path.isfile(PATH):
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
        print(f"ファイル '{PATH}' を新規作成")


def load_positions_preset():
    """
    JSONファイルからプリセットを読み込み、返す
    """
    with open(PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def append_positions_preset(positions_preset):
    """
    新しいプリセットを現在の辞書へ追加し、JSONファイルを更新する
    """
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(positions_preset, f, ensure_ascii=False, indent=4)


def delete_positions_preset(positions_preset, key):
    """
    指定されたキーのプリセットを辞書から削除し、JSONファイルを更新する
    """
    positions_preset.pop(key, None)
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(positions_preset, f, ensure_ascii=False, indent=4)


def reset_positions_preset(positions_preset):
    """
    辞書内の全てのプリセットを削除して、JSONファイルを更新する
    """
    positions_preset.clear()
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(positions_preset, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    main()
