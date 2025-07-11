## これはなに？
戦術対抗戦のリザルト画像から、テンプレートマッチングを用いて文字起こしをするツールです。  
生成したテキストは下記のスプレッドシートに転記することを想定しています。  
[対抗戦管理シート](https://docs.google.com/spreadsheets/d/12KPs3jY6IbdQOeOLc9a1Pgb9oAaiYB4bbUED37Il09U/) 
## 使い方
導入に関する詳細はこちらを参照してください。  
[導入解説記事](https://note.com/sisisirasu/n/ndb5d1f0260bf) 
1. パッケージインストール  
コマンドプロンプトを開き、以下のコマンドを入力して必要なライブラリをインストールしてください。  
コピペ用：pip install numpy Pillow opencv-python requests beautifulsoup4 google-api-python-client google-auth google-auth-oauthlib

1. 初期設定  
「初期設定.html」を起動してください。  
対抗戦のリザルト画像をアップロードした後、画像に合うように枠を移動させてください。（枠位置は雑でもOK）  
枠を設置した後、「ファイルをダウンロード」ボタンを押してファイルを生成して下さい。  
ダウンロードされた「positions.py」を「src」フォルダ内に配置してください。（上書きしてください）

1. 実行方法  
「Screenshots」フォルダ内に、判定したい対抗戦のリザルト画像を入れて下さい。  
「main.py」を起動すると処理が始まります。  
未登録の画像があると画面に表示されるので、表示された画像の名前を入力してください。  
最初は入力が面倒かもしれませんが、一定入力するとパワースパイクが起きます。私を信じて入力してください。

1. 転記について  
「Google Sheets API」をJSON形式で取得し、ファイル名を「api.json」に変更して「SpreadsheetAPI」内に配置してください。  
「SS.txt」には、転記先のスプレッドシートのIDを記入してください。  
スプレッドシート側「入力・攻撃」「入力・防衛」シートの、A列C列のチェックボックスを削除してから使用してください。

## 注意点  
### 新規生徒の実装時  
 - 自動で更新されるようになっています。（wikiが更新されれば）  
 - ボタンのアイコンを設定したい場合には「選択肢￥icon」の中にアイコン画像を追加してください。  
※追加しなくても、一度入力があればその画像がボタンに配置されます。  
###  臨戦ホシノについて  
 - 「ホシノ（攻撃）」「ホシノ（防御）」から選択してください。  
 - タイプについては、アイコン画像のカバンを見て判断してください。
###  精度について
 - しばらく使用していますが、生徒に関しては精度は100％です。
 - 対戦相手の名前に関しても99％判定できています。（「リリム」「ササム」を同じものとして処理したくらい）
 - 卓にユーザー名をコロコロ変える先生がいる場合は諦めてください。


## 📎 追加機能 (by this fork)

- [座標プリセット機能について](./PRESET_FEATURE.md)  
※プリセット登録をしていない状態で `main.py` が動作しなくなります