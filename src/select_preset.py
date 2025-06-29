import os
import json
from InquirerPy import inquirer


def run():
    base_dir = os.path.dirname(__file__)
    path = os.path.join(base_dir, "positions_preset.json")

    # プリセットを読み込む
    with open(path, "r", encoding="utf-8") as f:
        positions_preset = json.load(f)

    # 選択したプリセットを返す
    key = inquirer.select(
        message="使用するプリセットを選択:", choices=list(positions_preset)
    ).execute()

    return positions_preset[key]
