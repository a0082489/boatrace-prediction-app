import sqlite3
import json
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# データベース接続
def get_db_connection():
    conn = sqlite3.connect('boatrace_analysis.db')
    conn.row_factory = sqlite3.Row
    return conn

# 全場一覧を取得
@app.route('/api/venues', methods=['GET'])
def get_venues():
    try:
        conn = get_db_connection()
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

        return jsonify({'venues': venues_list})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# レース情報を取得
@app.route('/api/race/<date>/<venue_code>/<race_num>', methods=['GET'])
def get_race_info(date, venue_code, race_num):
    try:
        # 公式サイトからのデータ取得
        url = f'https://www.boatrace.jp/race/?jcd={venue_code}&hd={date}#{race_num}R'

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

        session = requests.Session()
        response = session.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # レーサー情報を抽出
        racers = []

        # 出走表のテーブルを探す
        table = soup.find('table', class_='table1')
        if not table:
            # 別のクラス名を試す
            table = soup.find('table', {'class': 'oddsTableWrap'}) or soup.find('div', class_='racersList')

        if table:
            rows = table.find_all('tr')[1:]  # ヘッダー行をスキップ

            for i, row in enumerate(rows[:6]):  # 最大6艇
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 4:
                    try:
                        # 基本情報の抽出
                        boat_num = i + 1

                        # 登録番号の抽出
                        reg_num_elem = row.find('span', class_='regNum') or row.find('td', class_='regNum')
                        reg_num = reg_num_elem.text.strip() if reg_num_elem else '----'

                        # 選手名の抽出
                        name_elem = row.find('a', class_='racerName') or row.find('span', class_='racerName') or row.find('td', class_='racerName')
                        if not name_elem:
                            name_elem = cells[1].find('a') or cells[1]
                        name = name_elem.text.strip() if name_elem else '未取得'

                        # 級別の抽出
                        class_elem = row.find('span', class_='racerClass') or row.find('td', class_='class')
                        racer_class = class_elem.text.strip() if class_elem else 'B2'

                        # 支部の抽出
                        branch_elem = row.find('span', class_='racerArea') or row.find('td', class_='area')
                        branch = branch_elem.text.strip() if branch_elem else '未取得'

                        # 年齢の抽出
                        age_elem = row.find('span', class_='racerAge') or row.find('td', class_='age')
                        age = age_elem.text.strip() if age_elem else '0'

                        # 勝率の抽出
                        winrate_elem = row.find('span', class_='winRate') or row.find('td', class_='winRate')
                        win_rate = float(winrate_elem.text.strip()) if winrate_elem and winrate_elem.text.strip().replace('.', '').isdigit() else 5.0

                        # スタートタイミングの抽出
                        start_elem = row.find('span', class_='startTime') or row.find('td', class_='startTime')
                        start_timing = float(start_elem.text.strip()) if start_elem and start_elem.text.strip().replace('.', '').replace('-', '').isdigit() else 0.15

                        # AI予想計算
                        prediction = calculate_prediction(win_rate, racer_class, start_timing, boat_num)

                        racers.append({
                            'boat_num': boat_num,
                            'reg_num': reg_num,
                            'name': name,
                            'class': racer_class,
                            'branch': branch,
                            'hometown': branch,  # 支部を出身地として使用
                            'age': age,
                            'win_rate': win_rate,
                            'start_timing': start_timing,
                            'prediction': prediction
                        })

                    except Exception as e:
                        # エラー時のデフォルト値
                        racers.append({
                            'boat_num': i + 1,
                            'reg_num': '----',
                            'name': '取得エラー',
                            'class': 'B2',
                            'branch': '未取得',
                            'hometown': '未取得',
                            'age': '0',
                            'win_rate': 5.0,
                            'start_timing': 0.15,
                            'prediction': 16.67
                        })
        else:
            # テーブルが見つからない場合のサンプルデータ
            sample_names = ['田中太郎', '佐藤花子', '山田次郎', '鈴木美咲', '高橋勇気', '渡辺直美']
            sample_classes = ['A1', 'A2', 'B1', 'B1', 'B2', 'B2']
            sample_branches = ['福岡', '大阪', '埼玉', '愛知', '広島', '香川']

            for i in range(6):
                win_rate = np.random.uniform(4.0, 7.5)
                start_timing = np.random.uniform(0.05, 0.25)
                prediction = calculate_prediction(win_rate, sample_classes[i], start_timing, i + 1)

                racers.append({
                    'boat_num': i + 1,
                    'reg_num': f'{4000 + i}',
                    'name': sample_names[i],
                    'class': sample_classes[i],
                    'branch': sample_branches[i],
                    'hometown': sample_branches[i],
                    'age': str(25 + i * 3),
                    'win_rate': round(win_rate, 2),
                    'start_timing': round(start_timing, 2),
                    'prediction': prediction
                })

        # 場名を取得
        conn = get_db_connection()
        venue = conn.execute('SELECT name FROM venues WHERE code = ?', (venue_code,)).fetchone()
        conn.close()
        venue_name = venue['name'] if venue else f'場コード{venue_code}'

        return jsonify({
            'date': date,
            'venue_code': venue_code,
            'venue_name': venue_name,
            'race_num': race_num,
            'racers': racers,
            'data_source': 'real' if table else 'sample'
        })

    except requests.RequestException as e:
        return jsonify({'error': f'データ取得エラー: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'処理エラー: {str(e)}'}), 500

def calculate_prediction(win_rate, racer_class, start_timing, boat_num):
    """AI予想計算"""
    try:
        # 基本スコア（勝率ベース）
        base_score = win_rate * 10

        # 級別ボーナス
        class_bonus = {'A1': 20, 'A2': 15, 'B1': 10, 'B2': 5}.get(racer_class, 5)

        # スタートタイミングボーナス
        if start_timing < 0.10:
            start_bonus = 15
        elif start_timing < 0.15:
            start_bonus = 10
        elif start_timing < 0.20:
            start_bonus = 5
        else:
            start_bonus = -5

        # 艇番による補正
        boat_bonus = [5, 3, 0, -2, -3, -5][boat_num - 1] if 1 <= boat_num <= 6 else 0

        # 総合スコア
        total_score = base_score + class_bonus + start_bonus + boat_bonus

        # パーセンテージに変換（最低5%、最高40%）
        percentage = max(5, min(40, total_score))

        return round(percentage, 1)

    except:
        return 16.67  # エラー時のデフォルト値

@app.route('/')
def home():
    return """
    <h1>ボートレース予想API</h1>
    <p>スマートフォン対応のボートレース予想システムAPIサーバーです。</p>
    <h2>エンドポイント:</h2>
    <ul>
        <li><strong>GET /api/venues</strong> - 全場一覧を取得</li>
        <li><strong>GET /api/race/&lt;date&gt;/&lt;venue_code&gt;/&lt;race_num&gt;</strong> - レース情報を取得</li>
    </ul>
    <h2>使用例:</h2>
    <ul>
        <li><a href="/api/venues">/api/venues</a> - 全場一覧</li>
        <li><a href="/api/race/20241215/01/1">/api/race/20241215/01/1</a> - 桐生の1Rの情報</li>
    </ul>
    """

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
