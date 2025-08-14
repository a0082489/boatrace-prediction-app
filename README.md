# ボートレース予想システム - スマートフォン対応版

日本の全24ボートレース場に対応した、AIによるボートレース予想システムです。スマートフォンとPCの両方でご利用いただけます。

## 🚀 主な機能

- **全24場対応**: 日本全国のボートレース場に対応
- **リアルタイムデータ**: 公式サイトから最新のレース情報を取得
- **AI予想**: 勝率、級別、スタートタイミングを考慮した予想アルゴリズム
- **スマートフォン対応**: レスポンシブデザインでモバイル端末に最適化
- **CORS対応**: クロスオリジン制限を回避したAPI設計

## 📁 ファイル構成

```
boatrace-prediction/
├── app.py                  # メインAPIサーバー（Flask）
├── requirements.txt        # Python依存関係
├── Procfile               # クラウドデプロイ設定
├── boatrace_analysis.db   # 場データベース（SQLite）
└── README.md              # このファイル
```

## 🔧 技術スタック

- **Backend**: Flask, Flask-CORS
- **Database**: SQLite
- **Web Scraping**: BeautifulSoup, requests
- **Machine Learning**: NumPy
- **Deployment**: Gunicorn (WSGI server)

## 🌐 クラウドデプロイ手順

### 1. Render.com でのデプロイ

#### 準備
1. [Render.com](https://render.com) にアカウント登録
2. GitHubリポジトリを作成し、プロジェクトファイルをアップロード

#### デプロイ手順
1. Render.com ダッシュボードで「New +」→「Web Service」を選択
2. GitHubリポジトリを接続
3. 以下の設定を入力：
   - **Name**: `boatrace-prediction`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`
4. 「Create Web Service」をクリック
5. デプロイ完了後、提供されるURLでアクセス可能

#### 料金
- **Free Tier**: 月750時間まで無料（個人使用に最適）
- **有料プラン**: $7/月〜（商用利用向け）

### 2. Railway.app でのデプロイ

#### 準備
1. [Railway.app](https://railway.app) にアカウント登録
2. GitHubアカウントと連携

#### デプロイ手順
1. Railway ダッシュボードで「New Project」を選択
2. 「Deploy from GitHub repo」を選択
3. リポジトリを選択して「Deploy Now」をクリック
4. 環境変数の設定（必要に応じて）
5. 自動デプロイ完了後、URLが生成される

#### 料金
- **Free Tier**: $5クレジット/月（使用量に応じて消費）
- **有料プラン**: $20/月〜

### 3. Fly.io でのデプロイ

#### 準備
1. [Fly.io](https://fly.io) にアカウント登録
2. Fly CLI をインストール
```bash
# macOS
brew install flyctl

# Windows (PowerShell)
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"

# Linux
curl -L https://fly.io/install.sh | sh
```

#### デプロイ手順
1. プロジェクトディレクトリで初期化
```bash
flyctl auth login
flyctl launch
```

2. `fly.toml` ファイルが生成されるので、以下のように編集：
```toml
app = "your-app-name"
primary_region = "nrt"  # 東京リージョン

[build]

[http_service]
  internal_port = 5000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 1

[[services]]
  protocol = "tcp"
  internal_port = 5000
  processes = ["app"]
```

3. デプロイ実行
```bash
flyctl deploy
```

#### 料金
- **Free Tier**: 月160時間まで無料
- **有料プラン**: 使用量に応じた従量課金

## 📱 API エンドポイント

### 全場一覧取得
```
GET /api/venues
```

**レスポンス例:**
```json
{
  "venues": [
    {
      "code": "01",
      "name": "桐生",
      "location": "群馬県",
      "water_type": "淡水",
      "region": "関東"
    }
  ]
}
```

### レース情報取得
```
GET /api/race/{date}/{venue_code}/{race_num}
```

**パラメータ:**
- `date`: レース日付（YYYYMMDD形式）
- `venue_code`: 場コード（01-24）
- `race_num`: レース番号（1-12）

**使用例:**
```
GET /api/race/20241215/01/1
```

**レスポンス例:**
```json
{
  "date": "20241215",
  "venue_code": "01",
  "venue_name": "桐生",
  "race_num": "1",
  "racers": [
    {
      "boat_num": 1,
      "reg_num": "4001",
      "name": "山田太郎",
      "class": "A1",
      "branch": "群馬",
      "hometown": "群馬",
      "age": "30",
      "win_rate": 6.50,
      "start_timing": 0.12,
      "prediction": 28.5
    }
  ],
  "data_source": "real"
}
```

## 🎯 AI予想アルゴリズム

予想確率は以下の要素を総合的に評価して算出されます：

1. **勝率** (基本スコア): 選手の直近勝率 × 10
2. **級別ボーナス**: A1級(+20), A2級(+15), B1級(+10), B2級(+5)
3. **スタートボーナス**: 0.10秒未満(+15), 0.15秒未満(+10), 0.20秒未満(+5)
4. **艇番補正**: 1号艇(+5), 2号艇(+3), 6号艇(-5)

最終的に5%〜40%の範囲で予想確率を出力します。

## 🔧 ローカル開発

### 環境構築
```bash
# 仮想環境作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係インストール
pip install -r requirements.txt

# サーバー起動
python app.py
```

### アクセス
- Web API: http://localhost:5000
- API文書: http://localhost:5000

## 🏟️ 対応競艇場一覧

| コード | 競艇場名 | 所在地 | 水質 |
|-------|---------|-------|------|
| 01 | 桐生 | 群馬県 | 淡水 |
| 02 | 戸田 | 埼玉県 | 淡水 |
| 03 | 江戸川 | 東京都 | 淡水 |
| 04 | 平和島 | 東京都 | 海水 |
| 05 | 多摩川 | 東京都 | 淡水 |
| 06 | 浜名湖 | 静岡県 | 汽水 |
| 07 | 蒲郡 | 愛知県 | 海水 |
| 08 | 常滑 | 愛知県 | 海水 |
| 09 | 津 | 三重県 | 海水 |
| 10 | 三国 | 福井県 | 海水 |
| 11 | びわこ | 滋賀県 | 淡水 |
| 12 | 住之江 | 大阪府 | 淡水 |
| 13 | 尼崎 | 兵庫県 | 淡水 |
| 14 | 鳴門 | 徳島県 | 海水 |
| 15 | 丸亀 | 香川県 | 海水 |
| 16 | 児島 | 岡山県 | 海水 |
| 17 | 宮島 | 広島県 | 海水 |
| 18 | 徳山 | 山口県 | 海水 |
| 19 | 下関 | 山口県 | 海水 |
| 20 | 若松 | 福岡県 | 海水 |
| 21 | 芦屋 | 福岡県 | 海水 |
| 22 | 福岡 | 福岡県 | 淡水 |
| 23 | 唐津 | 佐賀県 | 海水 |
| 24 | 大村 | 長崎県 | 海水 |

## ⚠️ 注意事項

1. **免責事項**: 本システムの予想結果に基づく投票は自己責任でお願いします
2. **データ制限**: 公式サイトの仕様変更により、データ取得できない場合があります
3. **利用規約**: 公式サイトの利用規約を遵守してご利用ください
4. **アクセス制限**: 過度なリクエストはサーバー負荷軽減のため制限される場合があります

## 📞 サポート

- **GitHub Issues**: バグ報告や機能要望
- **技術的質問**: 実装に関する質問やサポート

## 📄 ライセンス

MIT License - 個人利用・商用利用ともに自由にご利用いただけます。

## 🔄 更新履歴

- **v1.0.0** (2024/12): 初回リリース
  - 全24場対応
  - スマートフォン対応
  - クラウドデプロイ対応
  - AI予想アルゴリズム実装

---

**Happy Betting! 🚤💨**
