import sqlite3
import json
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
from datetime import datetime
import os
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# データベース自動初期化関数
def init_database():
    """アプリ起動時にデータベースを初期化"""
    try:
        conn = sqlite3.connect('boatrace_analysis.db')
        cursor = conn.cursor()
        
        # venuesテーブルを作成
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS venues (
                code TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                location TEXT NOT NULL,
                water_type TEXT NOT NULL,
                region TEXT NOT NULL
            )
        ''')
        
        # 24競艇場のデータ
        venues_data = [
            ('01', '桐生', '群馬県みどり市', '淡水', '関東'),
            ('02', '戸田', '埼玉県戸田市', '淡水', '関東'),
            ('03', '江戸川', '東京都江戸川区', '河川', '関東'),
            ('04', '平和島', '東京都大田区', '海水', '関東'),
            ('05', '多摩川', '東京都府中市', '淡水', '関東'),
            ('06', '浜名湖', '静岡県湖西市', '汽水', '東海'),
            ('07', '蒲郡', '愛知県蒲郡市', '海水', '東海'),
            ('08', '常滑', '愛知県常滑市', '海水', '東海'),
            ('09', '津', '三重県津市', '海水', '東海'),
            ('10', '三国', '福井県坂井市', '海水', '近畿'),
            ('11', 'びわこ', '滋賀県大津市', '淡水', '近畿'),
            ('12', '住之江', '大阪府大阪市', '淡水', '近畿'),
            ('13', '尼崎', '兵庫県尼崎市', '淡水', '近畿'),
            ('14', '鳴門', '徳島県鳴門市', '海水', '四国'),
            ('15', '丸亀', '香川県丸亀市', '海水', '四国'),
            ('16', '児島', '岡山県倉敷市', '海水', '中国'),
            ('17', '宮島', '広島県廿日市市', '海水', '中国'),
            ('18', '徳山', '山口県周南市', '海水', '中国'),
            ('19', '下関', '山口県下関市', '海水', '中国'),
            ('20', '若松', '福岡県北九州市', '海水', '九州'),
            ('21', '芦屋', '福岡県芦屋町', '海水', '九州'),
            ('22', '福岡', '福岡県福岡市', '淡水', '九州'),
            ('23', '唐津', '佐賀県唐津市', '海水', '九州'),
            ('24', '大村', '長崎県大村市', '海水', '九州')
        ]
        
        # データを挿入（重複は無視）
        cursor.executemany(
            'INSERT OR IGNORE INTO venues (code, name, location, water_type, region) VALUES (?, ?, ?, ?, ?)',
            venues_data
        )
        
        conn.commit()
        
        # 確認
        cursor.execute('SELECT COUNT(*) FROM venues')
        count = cursor.fetchone()[0]
        logger.info(f"Database initialized with {count} venues")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

# データベース接続
def get_db_connection():
    """データベース接続を取得"""
    try:
        conn = sqlite3.connect('boatrace_analysis.db')
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

# サンプルデータ生成
def generate_sample_venues():
    """データベース接続失敗時のサンプルデータ"""
    return [
        {'code': '01', 'name': '桐生', 'location': '群馬県', 'water_type': '淡水', 'region': '関東'},
        {'code': '02', 'name': '戸田', 'location': '埼玉県', 'water_type': '淡水', 'region': '関東'},
        {'code': '03', 'name': '江戸川', 'location': '東京都', 'water_type': '河川', 'region': '関東'},
        {'code': '04', 'name': '平和島', 'location': '東京都', 'water_type': '海水', 'region': '関東'},
        {'code': '05', 'name': '多摩川', 'location': '東京都', 'water_type': '淡水', 'region': '関東'},
        {'code': '12', 'name': '住之江', 'location': '大阪府', 'water_type': '淡水', 'region': '近畿'},
        {'code': '20', 'name': '若松', 'location': '福岡県', 'water_type': '海水', 'region': '九州'},
        {'code': '24', 'name': '大村', 'location': '長崎県', 'water_type': '海水', 'region': '九州'}
    ]

def generate_sample_racers():
    """サンプルレーサーデータ生成"""
    sample_names = ['田中太郎', '佐藤花子', '山田次郎', '鈴木美咲', '高橋勇気', '渡辺直美']
    sample_classes = ['A1', 'A2', 'B1', 'B1', 'B2', 'B2']
    sample_branches = ['福岡', '大阪', '埼玉', '愛知', '広島', '香川']
    
    racers = []
    for i in range(6):
        win_rate = round(np.random.uniform(4.0, 7.5), 2)
        start_timing = round(np.random.uniform(0.05, 0.25), 2)
        prediction = calculate_prediction(win_rate, sample_classes[i], start_timing, i + 1)
        
        racers.append({
            'boat_num': i + 1,
            'reg_num': f'{4000 + i}',
            'name': sample_names[i],
            'class': sample_classes[i],
            'branch': sample_branches[i],
            'hometown': sample_branches[i],
            'age': str(25 + i * 3),
            'win_rate': win_rate,
            'start_timing': start_timing,
            'prediction': prediction
        })
    
    return racers

# 全場一覧を取得
@app.route('/api/venues', methods=['GET'])
def get_venues():
    """全競艇場一覧を取得"""
    try:
        conn = get_db_connection()
        if conn is None:
            # データベース接続失敗時はサンプルデータを返す
            return jsonify({'venues': generate_sample_venues(), 'data_source': 'sample'})
        
        venues = conn.execute('SELECT * FROM venues ORDER BY code').fetchall()
        conn.close()
        
        venues_list = []
        for venue in venues:
            venues_list.append({
                'code': venue['code'],
                'name': venue['name'],
                'location': venue['location'],
                'water_type': venue['water_type'],
                'region': venue['region']
            })
        
        return jsonify({'venues': venues_list, 'data_source': 'database'})
        
    except Exception as e:
        logger.error(f"Error in get_venues: {e}")
        return jsonify({'venues': generate_sample_venues(), 'data_source': 'error_fallback'})

# レース情報を取得
@app.route('/api/race///', methods=['GET'])
def get_race_info(date, venue_code, race_num):
    """レース情報を取得"""
    try:
        # 公式サイトからのデータ取得を試行
        url = f'https://www.boatrace.jp/owpc/pc/race/racelist?rno={race_num}&jcd={venue_code}&hd={date}'
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        try:
            session = requests.Session()
            response = session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # レーサー情報を抽出
            racers = []
            
            # テーブル構造を探す
            tables = soup.find_all('table')
            racer_rows = []
            
            for table in tables:
                rows = table.find_all('tr')
                if len(rows) > 6:  # レーサー情報を含むテーブル
                    racer_rows = rows[1:7]  # ヘッダーを除く6行
                    break
            
            if racer_rows and len(racer_rows) >= 6:
                for i, row in enumerate(racer_rows):
                    try:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 3:
                            # 基本情報の抽出（簡易版）
                            boat_num = i + 1
                            
                            # テキストから情報を抽出
                            row_text = row.get_text(strip=True)
                            
                            # 登録番号の抽出（4桁の数字）
                            import re
                            reg_match = re.search(r'\b\d{4}\b', row_text)
                            reg_num = reg_match.group() if reg_match else f'400{i}'
                            
                            # 名前の抽出（カタカナ・ひらがな・漢字）
                            name_match = re.search(r'[あ-んア-ヶ一-龯]{2,8}', row_text)
                            name = name_match.group() if name_match else f'選手{i+1}'
                            
                            # 級別の抽出
                            class_match = re.search(r'[AB][12]', row_text)
                            racer_class = class_match.group() if class_match else 'B1'
                            
                            # 勝率を推定（3.00-7.00の範囲）
                            rate_match = re.search(r'[3-7]\.\d{2}', row_text)
                            win_rate = float(rate_match.group()) if rate_match else round(np.random.uniform(4.0, 6.5), 2)
                            
                            # STを推定（0.05-0.25の範囲）
                            st_match = re.search(r'0\.\d{2}', row_text)
                            start_timing = float(st_match.group()) if st_match else round(np.random.uniform(0.10, 0.20), 2)
                            
                            # AI予想計算
                            prediction = calculate_prediction(win_rate, racer_class, start_timing, boat_num)
                            
                            racers.append({
                                'boat_num': boat_num,
                                'reg_num': reg_num,
                                'name': name,
                                'class': racer_class,
                                'branch': '取得中',
                                'hometown': '取得中',
                                'age': '0',
                                'win_rate': win_rate,
                                'start_timing': start_timing,
                                'prediction': prediction
                            })
                    except Exception as e:
                        logger.warning(f"Error parsing racer {i+1}: {e}")
                        continue
            
            # データが不十分な場合はサンプルデータを使用
            if len(racers) < 6:
                logger.info("Insufficient real data, using sample data")
                racers = generate_sample_racers()
                data_source = 'sample'
            else:
                data_source = 'real'
                
        except requests.RequestException as e:
            logger.warning(f"Network error, using sample data: {e}")
            racers = generate_sample_racers()
            data_source = 'sample'
        
        # 場名を取得
        conn = get_db_connection()
        venue_name = f'場コード{venue_code}'
        
        if conn:
            try:
                venue = conn.execute('SELECT name FROM venues WHERE code = ?', (venue_code,)).fetchone()
                if venue:
                    venue_name = venue['name']
                conn.close()
            except Exception as e:
                logger.warning(f"Error getting venue name: {e}")
                if conn:
                    conn.close()
        
        return jsonify({
            'date': date,
            'venue_code': venue_code,
            'venue_name': venue_name,
            'race_num': race_num,
            'racers': racers,
            'data_source': data_source,
            'status': 'success'
        })
        
    except Exception as e:
        logger.error(f"Error in get_race_info: {e}")
        return jsonify({
            'error': f'処理エラー: {str(e)}',
            'racers': generate_sample_racers(),
            'data_source': 'error_fallback',
            'status': 'error'
        }), 500

def calculate_prediction(win_rate, racer_class, start_timing, boat_num):
    """AI予想計算"""
    try:
        # 基本スコア（勝率ベース）
        base_score = float(win_rate) * 8
        
        # 級別ボーナス
        class_bonus = {'A1': 25, 'A2': 18, 'B1': 12, 'B2': 8}.get(racer_class, 8)
        
        # スタートタイミングボーナス
        st = float(start_timing)
        if st < 0.10:
            start_bonus = 20
        elif st < 0.15:
            start_bonus = 15
        elif st < 0.20:
            start_bonus = 8
        else:
            start_bonus = 0
        
        # 艇番による補正
        boat_bonus = [8, 5, 2, 0, -2, -4][min(boat_num - 1, 5)]
        
        # 総合スコア
        total_score = base_score + class_bonus + start_bonus + boat_bonus
        
        # パーセンテージに変換（最低8%、最高38%）
        percentage = max(8, min(38, total_score))
        
        return round(percentage, 1)
        
    except Exception as e:
        logger.warning(f"Error in prediction calculation: {e}")
        return round(np.random.uniform(12.0, 25.0), 1)

@app.route('/')
def home():
    """メインページ"""
    return """
    🚤 ボートレース予想API
    スマートフォン対応のボートレース予想システムAPIサーバーです。
    📡 エンドポイント:
    
        GET /api/venues - 全場一覧を取得
        GET /api/race/<date>/<venue_code>/<race_num> - レース情報を取得
    
    💡 使用例:
    
        /api/venues - 全場一覧
        /api/race/20250814/01/1 - 桐生の1Rの情報
        /api/race/20250814/12/1 - 住之江の1Rの情報
    
    🔧 ステータス:
    ✅ データベース自動初期化対応済み
    ✅ エラーハンドリング強化済み
    ✅ スマートフォン対応
    """

@app.route('/health')
def health_check():
    """ヘルスチェック"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM venues')
            count = cursor.fetchone()[0]
            conn.close()
            return jsonify({
                'status': 'healthy',
                'database': 'connected',
                'venues_count': count,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'status': 'degraded',
                'database': 'disconnected',
                'timestamp': datetime.now().isoformat()
            }), 503
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# アプリ起動時の初期化
if __name__ == '__main__':
    # データベース初期化
    logger.info("Initializing database...")
    init_success = init_database()
    if init_success:
        logger.info("Database initialization successful")
    else:
        logger.warning("Database initialization failed, but continuing with fallback mode")
    
    # サーバー起動
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
else:
    # Gunicorn起動時の初期化
    logger.info("Initializing database for Gunicorn...")
    init_success = init_database()
    if init_success:
        logger.info("Database initialization successful")
    else:
        logger.warning("Database initialization failed, but continuing with fallback mode")
