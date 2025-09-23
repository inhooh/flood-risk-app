import pandas as pd

def calculate_risk(rainfall, elevation, flood_depth):
    """위험 점수 계산"""
    base_score = (rainfall / (elevation + 1)) * 10
    flood_bonus = flood_depth * 20
    risk_score = base_score + flood_bonus
    predicted_risk = 1 if risk_score > 20 else 0
    return risk_score, predicted_risk

def get_recommendations():
    """추천 설치 옵션 데이터 반환"""
    return pd.DataFrame({
        '위험 수준': ['저위험', '중위험', '고위험'],
        '차수판 유형': ['기본 알루미늄', '스마트 IoT 내장', '강화 스틸 + 센서'],
        '예상 비용 (㎡당)': ['5만 원', '8만 원', '12만 원'],
        '설치 기간': ['1일', '1-2일', '2일']
    })

def get_past_data():
    """과거 침수 사례 데이터 반환"""
    return pd.DataFrame({
        '년도': ['2025', '2024', '2023'],
        '강수량 (mm)': [411.9, 263.4, 200.5],
        '피해 (억원)': [500, 300, 150],
        '침수 확률 (%)': [80, 70, 50],
        '강조': ['광주 최대 기록', '서울 중부 호우', '전국 평균 초과']
    })

def get_alert_text(rainfall):
    """알림 텍스트 반환"""
    return f"현재 강수량: {rainfall}mm (과거 평균 200mm 초과).\n2025년 중부지방 사례: 500년 빈도 호우로 침수 확률 80% ↑."