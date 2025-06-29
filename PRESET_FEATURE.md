# 📌 座標プリセット機能について

`preset_manager.py` は、座標データのプリセットを追加・削除・閲覧できるCLIツールです。  
JSON形式で座標データを保存・管理し、定型的な配置を再利用可能にします。  

`main.py` を実行した際にプリセットの選択が可能になります。  
※プリセット登録をしていない状態で `main.py` が動作しなくなります

---

## 🔧 主な機能

- 座標データを名前付きプリセットとして保存
- 任意のプリセットを削除
- 全プリセットの削除（初期化）
- 登録済みプリセットの一覧表示

---

## 🚀 使い方

### 1. 実行
```bash
python preset_manager.py
```

### 2. 表示される選択肢から操作を選びます：

- `座標データをプリセットへ追加`  
  現在の `positions.positions` の座標データを、プリセットとして保存します

- `任意のプリセットを削除`  
- `全てのプリセットを削除`  
- `現在のプリセット一覧を表示`  
- `終了`  

---

## 🗂 データ保存先

プリセットは以下のJSONファイルへ保存されます：

```
src/positions_preset.json
```

---

## 📦 依存ライブラリ

以下のライブラリが必要です：

- [InquirerPy](https://github.com/kazhala/InquirerPy)：選択UIの提供
- [rich](https://github.com/Textualize/rich)：整形済み出力表示

インストールは以下の通りです：

```bash
pip install InquirerPy rich
```

---

## 🧪 備考

- 登録される座標データは `src/positions.py` の `positions.positions` に依存します。
- GUI ではなく CLI ベースの簡易ツールです。
- プリセットを追加する場合は事前準備が必要になります。
  1. [1. 初期設定](./readme.md)  に沿って `初期設定.index` を用いて `positions.py` を出力します。  
  2. 出力した `positions.py` をフォルダ `src` へ配置します  ※上書きでOK

---

## 📝 ライセンス・クレジット

このツールはfork元リポジトリの構成を基に、Yougurinaによって拡張されたものです。  
fork元（オリジナル）作成者であるManeNeko様に何か不都合がある場合は予告なく削除します