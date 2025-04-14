import requests
from bs4 import BeautifulSoup
import os
# --- 設定 ---
def updata_list(script_dir):
	google_drive_url = "https://drive.google.com/file/d/1It7AMNGTPge6EDUocaQdzFftSgDNgEX3/view?usp=drive_link"

	# スクリプトの場所を基準に選択肢フォルダを設定
	#script_dir = os.path.dirname(os.path.abspath(__file__))
	choice_dir = os.path.join(script_dir, "選択肢")
	log_path = os.path.join(choice_dir, "log.txt")
	st_path = os.path.join(choice_dir, "ST.txt")
	sp_path = os.path.join(choice_dir, "SP.txt")

	# フォルダなければ作成
	os.makedirs(choice_dir, exist_ok=True)

	# ファイル名を取得
	def get_filename_from_drive(url):
		response = requests.get(url)
		soup = BeautifulSoup(response.text, "html.parser")
		title = soup.title.string
		return title.replace(" - Google ドライブ", "").strip()

	# ファイル内容を取得（gdriveの特殊URL）
	def get_file_content(file_id):
		download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
		response = requests.get(download_url)
		return response.text if response.status_code == 200 else None

	# IDをURLから抜き出す
	def extract_file_id(url):
		parts = url.split("/")
		return parts[5] if "drive.google.com" in url and len(parts) > 5 else None

	# メイン処理
	file_id = extract_file_id(google_drive_url)
	filename = get_filename_from_drive(google_drive_url)

	# ログ読み込み
	if os.path.exists(log_path):
		with open(log_path, "r", encoding="utf-8") as f:
			existing = [line.strip() for line in f.readlines()]
	else:
		existing = []

	# ログに存在しない場合のみ処理
	if filename not in existing:
		# ログ追記
		with open(log_path, "a", encoding="utf-8") as f:
			f.write(filename + "\n")
		print(f"ログに追加しました: {filename}")

		# ファイル内容取得
		content = get_file_content(file_id)
		if content:
			# 分割処理
			parts = content.split("---", 1)
			if len(parts) == 2:
				with open(st_path, "w", encoding="utf-8") as f:
					f.write(parts[0].strip())
				with open(sp_path, "w", encoding="utf-8") as f:
					f.write(parts[1].strip())
				print("ST.txt / SP.txt に分割して保存しました。")
			else:
				print("データの分割に失敗しました（--- が見つかりません）。")
		else:
			print("ファイルの取得に失敗しました。")
	else:
		print("すでにログに存在しています。処理はスキップされました。")
