---
name: nano-banana-artist
description: >-
  承認されたプロットとキャラクター・世界観設定をもとに、Nano Banana を使用して漫画画像・原稿を生成・管理するスキル。
  キャラクターの一貫性を担保したプロンプト設計、コマごとの作画生成、原稿出力（manuscripts/配下）と編集者への納品を行います。
---

# Nano Banana 漫画原稿作成スキル (Nano Banana Artist)

本スキルは、編集者（ユーザー）によって承認されたプロット（`plot/`）およびキャラクター・世界観設定（`setting/`）をもとに、**Nano Banana** を活用して漫画のコマ画像・原稿を生成・管理するためのスキルです。

---

## 1. 原則と留意事項

- **キャラクターの一貫性 (Character Consistency)**:
  - 必ず [setting/characters/](file:///home/mekabu0551/comic-trainer/setting/characters/) にあるキャラクター設定シートの「Nano Banana 作画用固定プロンプト」をコマごとのプロンプトに統合します。
  - 同一キャラクターの髪型、目の色、服装、体格のキーワードがブレないように固定します。
- **背景・構図の一貫性**:
  - [setting/world/](file:///home/mekabu0551/comic-trainer/setting/world/) のロケーション設定に基づいた環境キーワードを使用します。
- **漫画表現・演出のプロンプト化**:
  - 白黒マンガ（モノクロ・スクリーントーン風）またはカラーコミックの画風指定、集中線・効果線・カメラアングルの指定を明確に行います。

---

## 2. 実行手順 (Procedure)

### ステップ 1: プロットと設定のインプット
1. **承認済みプロットの確認**:
   - `plot/{話数}/{バージョン}/plot.md` を読み込み、各ページ・コマの構図、登場人物、表情、背景、演出意図を把握します。
2. **固定プロンプトの抽出**:
   - 登場するキャラクターの固定特徴キーワード（例: `1boy, black messy hair, blue eyes, black gakuran`）を抽出します。
   - 舞台背景の固定特徴キーワード（例: `rainy city street, night, puddles, streetlights`）を抽出します。

### ステップ 2: コマ別 Nano Banana プロンプトの設計
各コマに対して、以下の構成でプロンプトを構築します：

```text
[スタイル指定] + [キャラクター固定特徴] + [コマ固有のアクション・表情・ポーズ] + [背景・環境] + [カメラアングル・構図] + [ライティング・品質指定]
```

#### プロンプト構成例:
- **スタイル指定**: `manga page, monochrome comic style, detailed line art, screentone shading`
- **被写体・表情**: `1boy, short black hair, school uniform, looking down at his wristwatch, cold focused expression`
- **背景・構図**: `rainy Tokyo alley at night, dim streetlamp, medium shot, dramatic shadow, cinematic composition`

### ステップ 3: 画像生成と保存管理
- 原稿画像および生成時に使用したプロンプトログを以下のディレクトリに保存します。
- **保存ディレクトリ**: `manuscripts/{話数}/{バージョン}/`
  - 画像ファイル命名規則: `page_{ページ番号}_panel_{コマ番号}.png` （またはページ単位で `page_{ページ番号}.png`）
  - プロンプト記録ファイル: `manuscripts/{話数}/{バージョン}/prompts.md`

#### `prompts.md` の記録例:
```markdown
# 第〇話 作画プロンプト記録 (v1)

## ページ 1 - コマ 1
- **生成ファイル**: `page_01_panel_01.png`
- **プロンプト**: `manga panel, wide shot, overcast sky, abandoned classroom, dust motes, cinematic lighting, ultra-detailed manga lineart`
- **調整メモ**: 背景の廃墟感を強調。

## ページ 1 - コマ 2
- **生成ファイル**: `page_01_panel_02.png`
- **プロンプト**: `manga panel, 1boy, messy black hair, school uniform, looking back with wide surprised eyes, close up, motion blur`
...
```

### ステップ 4: 完成原稿の編集者（ユーザー）最終確認
1. 生成された原稿画像・コマ画像を一覧化し、プロットの意図が表現されているかを確認します。
2. 編集者に成果物を提示し、絵の整合性、表情のニュアンス、作画クオリティについて確認を依頼します。
3. 修正が必要なコマがあれば、プロンプトを微調整して再生成を行います。
