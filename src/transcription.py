import os
import json
import re
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# === 定数定義 ===
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
ATTACK_WORKSHEET_NAME = '入力・攻撃'
DEFENSE_WORKSHEET_NAME = '入力・防衛'


# === 設定ファイル関連 ===
def load_api_config(script_dir):
    """API設定ファイルを読み込む"""
    api_dir = os.path.join(script_dir, "SpreadsheetAPI")
    
    # ファイル存在確認
    api_json_path = os.path.join(api_dir, "api.json")
    ss_txt_path = os.path.join(api_dir, "SS.txt")
    
    if not os.path.exists(api_json_path):
        print("エラー: api.jsonが存在しません。処理を終了します。")
        print(f"期待されるパス: {api_json_path}")
        return None, None
    
    if not os.path.exists(ss_txt_path):
        print("エラー: SS.txtが存在しません。処理を終了します。")
        print(f"期待されるパス: {ss_txt_path}")
        return None, None
    
    try:
        # スプレッドシートIDを読み込み
        with open(ss_txt_path, 'r', encoding='utf-8') as f:
            ss_content = f.read().strip()
        
        # URLからIDを抽出またはIDをそのまま使用
        if 'docs.google.com/spreadsheets' in ss_content:
            match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', ss_content)
            if match:
                spreadsheet_id = match.group(1)
            else:
                print("エラー: スプレッドシートURLからIDを抽出できませんでした。")
                return None, None
        else:
            spreadsheet_id = ss_content
        
        print(f"スプレッドシートID: {spreadsheet_id}")
        return api_json_path, spreadsheet_id
        
    except Exception as e:
        print(f"設定ファイル読み込みエラー: {e}")
        return None, None


# === Google Sheets API関連 ===
def authenticate_google_sheets(service_account_file):
    """Google Sheets APIの認証を行う"""
    try:
        credentials = Credentials.from_service_account_file(
            service_account_file, scopes=SCOPES)
        service = build('sheets', 'v4', credentials=credentials)
        return service
    except Exception as e:
        print(f"認証エラー: {e}")
        return None


def get_last_row(service, spreadsheet_id, worksheet_name):
    """指定されたワークシートのB列の最終行を取得"""
    try:
        range_name = f"{worksheet_name}!B:B"
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range=range_name).execute()
        
        values = result.get('values', [])
        # 空でない値がある最後の行を探す
        last_row = 0
        for i, row in enumerate(values):
            if row and len(row) > 0 and row[0].strip():  # 空でない値がある場合
                last_row = i + 1
        return last_row
    except HttpError as e:
        print(f"最終行取得エラー: {e}")
        return 0


def convert_checkbox_value(value):
    """チェックボックス用の値を変換"""
    if isinstance(value, str):
        value_upper = value.upper().strip()
        if value_upper in ['TRUE', '1', 'YES', 'チェック', 'ON']:
            return True
        elif value_upper in ['FALSE', '0', 'NO', 'OFF', '']:
            return False
        else:
            # 数値の場合
            try:
                num_value = float(value)
                return num_value != 0
            except ValueError:
                return False
    elif isinstance(value, bool):
        return value
    elif isinstance(value, (int, float)):
        return value != 0
    else:
        return False


def expand_sheet_if_needed(service, spreadsheet_id, worksheet_name, required_rows, required_cols):
    """必要に応じてシートのサイズを拡張"""
    try:
        # 現在のシート情報を取得
        sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheet_info = None
        sheet_id = None
        
        for sheet in sheet_metadata.get('sheets', []):
            if sheet.get('properties', {}).get('title') == worksheet_name:
                sheet_info = sheet.get('properties', {})
                sheet_id = sheet_info.get('sheetId')
                break
        
        if sheet_info is None:
            print(f"ワークシート '{worksheet_name}' が見つかりませんでした")
            return False
        
        current_rows = sheet_info.get('gridProperties', {}).get('rowCount', 1000)
        current_cols = sheet_info.get('gridProperties', {}).get('columnCount', 26)
        
        # 拡張が必要かチェック
        need_expansion = False
        new_rows = current_rows
        new_cols = current_cols
        
        if required_rows > current_rows:
            new_rows = required_rows + 100  # 余裕を持って100行追加
            need_expansion = True
            
        if required_cols > current_cols:
            new_cols = required_cols + 5  # 余裕を持って5列追加
            need_expansion = True
        
        if need_expansion:
            print(f"シートサイズを拡張します: {current_rows}→{new_rows}行, {current_cols}→{new_cols}列")
            
            # シートサイズを拡張
            requests = [{
                'updateSheetProperties': {
                    'properties': {
                        'sheetId': sheet_id,
                        'gridProperties': {
                            'rowCount': new_rows,
                            'columnCount': new_cols
                        }
                    },
                    'fields': 'gridProperties.rowCount,gridProperties.columnCount'
                }
            }]
            
            body = {'requests': requests}
            service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=body
            ).execute()
            
            print(f"シートサイズの拡張が完了しました")
        
        return True
        
    except HttpError as e:
        print(f"シートサイズ拡張エラー: {e}")
        return False


def write_data_to_sheets(service, spreadsheet_id, worksheet_name, data_rows, start_row):
    """スプレッドシートにデータを一括書き込み（チェックボックス対応版）"""
    try:
        if not data_rows:
            print("書き込むデータがありません")
            return False
        
        # データの型変換処理
        converted_data = []
        for row in data_rows:
            converted_row = []
            for i, cell in enumerate(row):
                if i == 2:  # C列（2列目）のみチェックボックス
                    converted_row.append(convert_checkbox_value(cell))
                else:
                    converted_row.append(cell)
            converted_data.append(converted_row)
        
        # 書き込み範囲を計算
        end_row = start_row + len(converted_data) - 1
        num_cols = len(converted_data[0]) if converted_data else 0
        
        # 列番号をアルファベットに変換
        def num_to_col_letters(num):
            result = ""
            while num > 0:
                num -= 1
                result = chr(num % 26 + ord('A')) + result
                num //= 26
            return result
        
        end_col = num_to_col_letters(num_cols)
        range_name = f"{worksheet_name}!A{start_row}:{end_col}{end_row}"
        
        # データを書き込み（RAW入力で上書き）
        body = {'values': converted_data}
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='RAW',  # RAWに変更してチェックボックスを上書き
            body=body
        ).execute()
        
        updated_cells = result.get('updatedCells', 0)
        print(f"スプレッドシート「{worksheet_name}」に {updated_cells} セルのデータを書き込みました")
        print(f"書き込み範囲: {range_name}")
        
        # チェックボックス列の再設定
        setup_checkbox_validation(service, spreadsheet_id, worksheet_name, start_row, end_row)
        
        return True
        
    except HttpError as e:
        print(f"スプレッドシート書き込みエラー: {e}")
        return False


def setup_checkbox_validation(service, spreadsheet_id, worksheet_name, start_row, end_row):
    """指定範囲にチェックボックスの検証ルールを設定"""
    try:
        # ワークシートIDを取得
        sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheet_id = None
        for sheet in sheet_metadata.get('sheets', []):
            if sheet.get('properties', {}).get('title') == worksheet_name:
                sheet_id = sheet.get('properties', {}).get('sheetId')
                break
        
        if sheet_id is None:
            print(f"ワークシート '{worksheet_name}' が見つかりませんでした")
            return False
        
        # チェックボックスの検証ルールを設定
        requests = []
        
        # C列のチェックボックス設定のみ
        requests.append({
            'setDataValidation': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': start_row - 1,
                    'endRowIndex': end_row,
                    'startColumnIndex': 2,  # C列
                    'endColumnIndex': 3
                },
                'rule': {
                    'condition': {
                        'type': 'BOOLEAN'
                    },
                    'inputMessage': 'チェックボックス',
                    'strict': True
                }
            }
        })
        
        # 一括実行
        body = {'requests': requests}
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=body
        ).execute()
        
        print(f"C列のチェックボックス設定を完了しました (行 {start_row}-{end_row})")
        return True
        
    except HttpError as e:
        print(f"チェックボックス設定エラー: {e}")
        return False


# === ファイル処理関連 ===
def read_file(file_path):
    """ファイルを読み込んでリストに変換"""
    data_rows = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if line:  # 空行でない場合
                    columns = line.split('\t')
                    data_rows.append(columns)
        
        print(f"ファイルから {len(data_rows)} 行のデータを読み込みました: {file_path}")
        print("記入中...")
        return data_rows
    
    except FileNotFoundError:
        print(f"ファイルが見つかりません: {file_path}")
        return []
    except Exception as e:
        print(f"ファイル読み込みエラー: {e}")
        return []


def process_file_data(service, spreadsheet_id, file_path, worksheet_name, file_type):
    """ファイルデータを処理してスプレッドシートに書き込み"""
    if not os.path.exists(file_path):
        return False
    
    print(f"\n--- {file_type}データの処理 ---")
    data = read_file(file_path)
    if not data:
        return False
    
    # シートの最終行を取得
    last_row = get_last_row(service, spreadsheet_id, worksheet_name)
    start_row = last_row + 1
    print(f"{file_type}シート - 最終行: {last_row}, 書き込み開始行: {start_row}")
    
    # シートにデータを書き込み
    if write_data_to_sheets(service, spreadsheet_id, worksheet_name, data, start_row):
        print(f"{file_type}データの転記が完了しました")
        #テキストファイル削除
        os.remove(file_path)
        return True
    else:
        print(f"{file_type}データの転記に失敗しました")
        return False


# === メイン処理 ===
def main(script_dir=None):
    """メイン処理"""
    if script_dir is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # srcフォルダ内から実行された場合は、親ディレクトリを取得
        if os.path.basename(script_dir) == 'src':
            script_dir = os.path.dirname(script_dir)
    
    print("=== Google Sheetsデータ転記プログラム ===")
    
    # API設定を読み込み
    print("API設定を読み込み中...")
    service_account_file, spreadsheet_id = load_api_config(script_dir)
    if not service_account_file or not spreadsheet_id:
        return
    
    # ファイルパス定義
    file_attack = os.path.join(script_dir, "リザルト_攻撃.txt")
    file_defense = os.path.join(script_dir, "リザルト_防衛.txt")
    
    # ファイルの存在確認
    attack_exists = os.path.exists(file_attack)
    defense_exists = os.path.exists(file_defense)
    
    if not attack_exists and not defense_exists:
        print("攻撃ファイルと防衛ファイルの両方が存在しません。処理を終了します。")
        return
    
    # Google Sheets APIの認証
    print("Google Sheets APIに接続中...")
    service = authenticate_google_sheets(service_account_file)
    if not service:
        print("Google Sheets APIの認証に失敗しました")
        return
    print("認証成功！")
    
    # データ処理
    success_count = 0
    total_files = 0
    
    if attack_exists:
        total_files += 1
        if process_file_data(service, spreadsheet_id, file_attack, ATTACK_WORKSHEET_NAME, "攻撃"):
            success_count += 1
    
    if defense_exists:
        total_files += 1
        if process_file_data(service, spreadsheet_id, file_defense, DEFENSE_WORKSHEET_NAME, "防衛"):
            success_count += 1
    
    # 結果の表示
    if success_count == total_files:
        print(f"\nデータ転記が完了しました！ ({success_count}/{total_files})")
    else:
        print(f"\nデータ転記に失敗しました ({success_count}/{total_files})")


if __name__ == "__main__":
    main()
