#!/usr/bin/env python3
"""
Google Drive Manuscripts Uploader for comic-trainer

指定された manuscripts (例: manuscripts/ep01/v1) の原稿データおよび関連ファイルを
Google Drive のマイドライブへアップロード・同期するスクリプトです。
"""

import os
import sys
import argparse
import mimetypes
from pathlib import Path

# Google API libraries
try:
    from google.oauth2.credentials import Credentials
    from google.oauth2 import service_account
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from googleapiclient.errors import HttpError
    from dotenv import load_dotenv
except ImportError:
    print("エラー: 必要なGoogle APIライブラリがインストールされていません。")
    print("以下のコマンドを実行してください:")
    print("  .venv/bin/pip install -r requirements.txt")
    sys.exit(1)

# スコープ: Google Drive 上で作成・編集したファイルを管理
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def print_setup_guide():
    """認証ファイルが存在しない場合の案内を出力"""
    print("\n" + "=" * 60)
    print("【Google Drive 認証設定（初回のみ）】")
    print("=" * 60)
    print("Google Drive API を使用するには、認証情報ファイル (credentials.json) が必要です。\n")
    print("1. Google Cloud Console (https://console.cloud.google.com/) にアクセス")
    print("2. プロジェクトを作成（または既存プロジェクトを選択）")
    print("3. 「APIとサービス」>「有効なAPIとサービス」から「Google Drive API」を有効化")
    print("4. 「APIとサービス」>「OAuth 同意画面」を設定（ユーザータイプ: 外部または内部）")
    print("5. 「認証情報」>「認証情報を作成」>「OAuth クライアント ID」を選択")
    print("   - アプリケーションの種類: 「デスクトップ アプリ」")
    print("6. 作成したクライアントの JSON ファイルをダウンロードし、プロジェクト直下に")
    print("   'credentials.json' として配置してください。")
    print("=" * 60 + "\n")


def get_drive_service(credentials_path="credentials.json", token_path="token.json", service_account_path=None, google_account=None):
    """Google Drive API サービスインスタンスを取得"""
    creds = None

    # サービスアカウント利用時
    if service_account_path and os.path.exists(service_account_path):
        print(f"サービスアカウントを使用して認証中: {service_account_path}")
        creds = service_account.Credentials.from_service_account_file(
            service_account_path, scopes=['https://www.googleapis.com/auth/drive']
        )
        return build('drive', 'v3', credentials=creds)

    # OAuth 2.0 トークン確認
    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        except Exception as e:
            print(f"既存トークンの読み込みエラー: {e}")
            creds = None

    # トークンが無効または存在しない場合のリフレッシュ / 新規認証
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("既存のOAuthトークンを自動更新中...")
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"トークンの自動更新に失敗しました: {e}")
                creds = None

        if not creds:
            flow = None
            client_id = os.getenv("GOOGLE_CLIENT_ID")
            client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

            if client_id and client_secret:
                print("環境変数 (.env) の GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET を使用して認証します...")
                client_config = {
                    "installed": {
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": ["http://localhost"]
                    }
                }
                flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            elif os.path.exists(credentials_path):
                print(f"OAuth 2.0 認証フローを開始します (使用ファイル: {credentials_path})...")
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            else:
                print(f"エラー: Google Drive 接続情報が見つかりません。")
                print("以下のいずれかを設定してください:")
                print("  A) .env に 'GOOGLE_CLIENT_ID' と 'GOOGLE_CLIENT_SECRET' を記述する")
                print(f"  B) プロジェクト直下に '{credentials_path}' ファイルを配置する")
                print_setup_guide()
                sys.exit(1)

            if google_account:
                print(f"指定ログインアカウント: {google_account}")

            try:
                # ローカルサーバーによる認証試行
                server_kwargs = {"port": 0, "open_browser": True}
                if google_account:
                    server_kwargs["login_hint"] = google_account
                creds = flow.run_local_server(**server_kwargs)
            except Exception:
                # コンソール認証にフォールバック
                print("ブラウザの自動起動が利用できないため、コンソール認証を実行します。")
                creds = flow.run_console()

        # トークンを保存
        with open(token_path, 'w', encoding='utf-8') as token_file:
            token_file.write(creds.to_json())
        print(f"認証トークンを保存しました: {token_path}")

    return build('drive', 'v3', credentials=creds)


def get_or_create_folder(service, folder_name, parent_id=None):
    """指定したフォルダを取得、存在しない場合は作成"""
    query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    else:
        query += " and 'root' in parents"

    results = service.files().list(
        q=query, spaces='drive', fields='files(id, name, webViewLink)'
    ).execute()
    items = results.get('files', [])

    if items:
        return items[0]['id'], items[0].get('webViewLink')

    # 作成
    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    if parent_id:
        folder_metadata['parents'] = [parent_id]

    folder = service.files().create(body=folder_metadata, fields='id, webViewLink').execute()
    print(f"Google Drive にフォルダを作成しました: {folder_name} (ID: {folder.get('id')})")
    return folder.get('id'), folder.get('webViewLink')


def upload_files(service, target_dir: Path, target_folder_id: str, overwrite: bool = True):
    """指定ディレクトリ内のファイルをGoogle Driveフォルダへアップロード"""
    files_to_upload = [p for p in target_dir.iterdir() if p.is_file()]
    if not files_to_upload:
        print(f"警告: ディレクトリ内にアップロード対象のファイルがありません: {target_dir}")
        return []

    # 既存ファイル一覧を取得
    query = f"'{target_folder_id}' in parents and trashed = false"
    existing_items = service.files().list(
        q=query, spaces='drive', fields='files(id, name)'
    ).execute().get('files', [])
    existing_map = {item['name']: item['id'] for item in existing_items}

    uploaded = []
    print(f"\nアップロード対象ファイル数: {len(files_to_upload)} 件")

    for file_path in sorted(files_to_upload):
        file_name = file_path.name
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if not mime_type:
            mime_type = 'application/octet-stream'

        media = MediaFileUpload(str(file_path), mimetype=mime_type, resumable=True)

        if file_name in existing_map and overwrite:
            file_id = existing_map[file_name]
            print(f"  [更新] {file_name} (既存ID: {file_id}) ...", end=" ", flush=True)
            updated_file = service.files().update(
                fileId=file_id,
                media_body=media,
                fields='id, name, webViewLink, size'
            ).execute()
            print("完了")
            uploaded.append(updated_file)
        elif file_name in existing_map and not overwrite:
            print(f"  [スキップ] {file_name} (既に存在します)")
        else:
            print(f"  [新規] {file_name} ...", end=" ", flush=True)
            file_metadata = {
                'name': file_name,
                'parents': [target_folder_id]
            }
            new_file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink, size'
            ).execute()
            print("完了")
            uploaded.append(new_file)

    return uploaded


def resolve_target_dir(args, base_dir: Path) -> Path:
    """引数から対象原稿ディレクトリを解決"""
    if args.path:
        target = Path(args.path)
        if not target.is_absolute():
            target = base_dir / target
        return target

    if args.episode and args.version:
        return base_dir / "manuscripts" / args.episode / args.version

    print("エラー: アップロード対象の原稿ディレクトリを指定してください。")
    print("例: python scripts/upload_to_gdrive.py manuscripts/ep01/v1")
    print("    python scripts/upload_to_gdrive.py --episode ep01 --version v1")
    sys.exit(1)


def main():
    base_dir = Path(__file__).resolve().parent.parent
    load_dotenv(dotenv_path=base_dir / ".env")

    default_account = os.getenv("GOOGLE_ACCOUNT")
    default_root_folder = os.getenv("GOOGLE_DRIVE_ROOT_FOLDER", "comic-trainer")
    default_credentials = os.getenv("CREDENTIALS_FILE", "credentials.json")
    default_token = os.getenv("TOKEN_FILE", "token.json")

    parser = argparse.ArgumentParser(description="Upload comic manuscripts to Google Drive (My Drive).")
    parser.add_argument("path", nargs="?", help="Target manuscript directory (e.g. manuscripts/ep01/v1)")
    parser.add_argument("-e", "--episode", help="Episode name/number (e.g. ep01)")
    parser.add_argument("-v", "--version", help="Version name/number (e.g. v1)")
    parser.add_argument("-a", "--account", default=default_account, help="Target Google account email (login hint)")
    parser.add_argument("-c", "--credentials", default=default_credentials, help="Path to credentials.json")
    parser.add_argument("-t", "--token", default=default_token, help="Path to token.json")
    parser.add_argument("-s", "--service-account", help="Path to service_account.json (optional)")
    parser.add_argument("--root-folder", default=default_root_folder, help="Root folder name on Google Drive")
    parser.add_argument("--no-overwrite", action="store_true", help="Do not overwrite existing files")

    args = parser.parse_args()

    target_dir = resolve_target_dir(args, base_dir)

    if not target_dir.exists():
        print(f"エラー: 指定されたディレクトリが存在しません: {target_dir}")
        sys.exit(1)

    print(f"【Google Drive アップロード処理】")
    print(f"・対象ローカルディレクトリ: {target_dir}")
    if args.account:
        print(f"・対象Googleアカウント: {args.account}")

    # 相対パスから階層（話数/バージョン）を判定
    try:
        rel_path = target_dir.relative_to(base_dir / "manuscripts")
        path_parts = rel_path.parts
    except ValueError:
        path_parts = (target_dir.name,)

    # Google Drive サービス取得
    credentials_path = str(base_dir / args.credentials) if not os.path.isabs(args.credentials) else args.credentials
    token_path = str(base_dir / args.token) if not os.path.isabs(args.token) else args.token
    service = get_drive_service(
        credentials_path=credentials_path,
        token_path=token_path,
        service_account_path=args.service_account,
        google_account=args.account
    )

    try:
        # マイドライブ上のフォルダ階層を構築
        # root -> comic-trainer -> manuscripts -> {話数} -> {バージョン}
        print(f"\nGoogle Drive フォルダ階層を確認・構築中...")
        root_folder_id, _ = get_or_create_folder(service, args.root_folder)
        manuscripts_folder_id, _ = get_or_create_folder(service, "manuscripts", root_folder_id)

        current_parent_id = manuscripts_folder_id
        folder_link = None
        for part in path_parts:
            current_parent_id, folder_link = get_or_create_folder(service, part, current_parent_id)

        print(f"保存先Google Driveフォルダ: {'/'.join([args.root_folder, 'manuscripts', *path_parts])}")
        if folder_link:
            print(f"フォルダURL: {folder_link}")

        # ファイルアップロード実行
        uploaded = upload_files(
            service=service,
            target_dir=target_dir,
            target_folder_id=current_parent_id,
            overwrite=not args.no_overwrite
        )

        print("\n" + "=" * 60)
        print(f"【アップロード完了】 合計 {len(uploaded)} 件のファイルを同期しました。")
        if folder_link:
            print(f"マイドライブ確認リンク: {folder_link}")
        print("=" * 60)

    except HttpError as error:
        print(f"\nGoogle Drive API エラーが発生しました: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
