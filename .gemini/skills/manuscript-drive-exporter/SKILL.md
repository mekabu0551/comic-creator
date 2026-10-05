---
name: manuscript-drive-exporter
description: >-
  指定された話数・バージョンの漫画原稿（manuscripts/配下）をGoogle Driveのマイドライブへ
  アップロード・同期保存するためのスキル。Pythonスクリプトを実行し、Google Driveへの保存・フォルダリンクの確認を行います。
---

# 原稿 Google Drive 保存スキル (Manuscript Drive Exporter)

本スキルは、Nano Banana で作成した漫画原稿・画像データ（`manuscripts/{話数}/{バージョン}/`）を、Google Drive のマイドライブへ安全にアップロード・同期保存するためのスキルです。

---

## 1. 概要・保存先構造

本スキルを実行すると、マイドライブ直下に以下の階層が自動作成・同期されます。

```text
Google Drive (マイドライブ)
└── comic-trainer/
    └── manuscripts/
        └── {話数}/
            └── {バージョン}/  (例: manuscripts/ep01/v1/配下の全ファイル)
```

---

## 2. 前提条件と認証準備

### 仮想環境と依存ライブラリ
プロジェクト直下の仮想環境 `.venv` に必要なパッケージ（`google-api-python-client` など）がインストールされています。
未インストールの場合は以下のコマンドで導入できます：
```bash
.venv/bin/pip install -r requirements.txt
```

### 環境変数 (.env) 設定
プロジェクト直下の `.env` に、Google アカウントおよび接続情報を設定します。
別ファイル（`credentials.json`）を用意しなくても、**`.env` への記述だけで動作可能**です。

```env
# 保存先 Google アカウント
GOOGLE_ACCOUNT=yophfrid04@outlook.jp
GOOGLE_DRIVE_ROOT_FOLDER=comic-trainer

# Google Drive API 接続情報 (.env だけで動かす場合は以下を入力)
GOOGLE_CLIENT_ID=xxxxxxxxxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxx
```

### Google Drive 認証 (初回のみ)
OAuth 2.0 クライアント認証を使用します（以下のいずれか）：
- **方法 A (推奨・.env完結)**: `.env` に Google Cloud Console で取得した `GOOGLE_CLIENT_ID` と `GOOGLE_CLIENT_SECRET` を記載する。
- **方法 B (ファイル配置)**: ダウンロードした JSON を `credentials.json` として配置する。

初回実行時、ブラウザまたはコンソールでの認証画面が表示され、完了すると **`token.json`** が自動生成されます（次回以降は完全自動認証）。

---

## 3. 実行手順 (Procedure)

### ステップ 1: アップロード対象の確認
指定された話数・バージョンに対応する原稿ディレクトリが存在し、アップロード対象の画像・ログファイルがあるか確認します。

- 対象パスの確認例:
  ```bash
  ls -la manuscripts/ep01/v1/
  ```

### ステップ 2: アップロードスクリプトの実行
プロジェクト専用スクリプト [scripts/upload_to_gdrive.py](file:///home/mekabu0551/comic-trainer/scripts/upload_to_gdrive.py) を実行します。

#### 基本実行コマンド:
```bash
.venv/bin/python scripts/upload_to_gdrive.py manuscripts/{話数}/{バージョン}
```

#### オプション指定例:
- 話数・バージョンを個別指定する場合:
  ```bash
  .venv/bin/python scripts/upload_to_gdrive.py --episode ep01 --version v1
  ```
- 既存ファイルを上書きせずスキップする場合:
  ```bash
  .venv/bin/python scripts/upload_to_gdrive.py manuscripts/ep01/v1 --no-overwrite
  ```
- サービスアカウントキーを使用する場合:
  ```bash
  .venv/bin/python scripts/upload_to_gdrive.py manuscripts/ep01/v1 --service-account /path/to/service_account.json
  ```

### ステップ 3: 実行結果の確認と編集者（ユーザー）への報告
1. スクリプトの出力から、各ファイルのアップロード完了状況と **Google Drive フォルダURL（webViewLink）** を確認します。
2. 編集者（ユーザー）にアップロード成功の旨と、確認用リンクを報告します。
