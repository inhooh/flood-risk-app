import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import folium
from folium.plugins import HeatMap

def create_map(lat, lon, predicted_risk, selected_gu, risk_score, rainfall, flood_depth, korean_cities):
    """
    GIS 지도 생성 (구 단위 히트맵 오버레이 포함)
    """
    m = folium.Map(location=[lat, lon], zoom_start=12)  # 줌 레벨 조정 (구 단위 표시용)
    color = 'red' if predicted_risk == 1 else 'blue'
    
    # 현재 선택된 지역 마커
    folium.Marker(
        [lat, lon],
        popup=f"지역: {selected_gu}<br>위험도: {'고위험' if predicted_risk == 1 else '저위험'}<br>점수: {risk_score:.2f}<br>강수량: {rainfall}mm<br>침수심: {flood_depth}m",
        icon=folium.Icon(color=color)
    ).add_to(m)

    # 구 단위 히트맵 데이터 생성 (base_depth를 가중치로 사용)
    heat_data = []
    for sido, gus in korean_cities.items():
        for gu, (lat_g, lon_g, _, _, depth) in gus.items():
            # base_depth를 가중치로, 침수심에 비례해 강도 조정
            weight = depth * 10  # base_depth를 10배로 스케일링 (조정 가능)
            heat_data.append([lat_g, lon_g, weight])

    # HeatMap 오버레이 추가
    HeatMap(heat_data, radius=15, blur=10, max_zoom=13).add_to(m)

    return m

def create_rainfall_chart(rainfall):
    fig, ax = plt.subplots(figsize=(8, 6))
    x = np.linspace(0, 500, 100)
    y = 1 - np.exp(-x / 200)  # 지수 모델
    ax.plot(x, y*100, color='red', linewidth=2)
    ax.set_xlabel('강수량 (mm)')
    ax.set_ylabel('침수 확률 (%)')
    ax.set_title('강수량 vs 침수 확률 (2025년 사례 포함)')
    ax.grid(True, alpha=0.3)
    ax.axvline(rainfall, color='orange', linestyle='--', label=f'현재 강수량: {rainfall}mm')
    ax.legend()
    return fig

def create_trend_chart():
    years = [2021, 2022, 2023, 2024, 2025]
    avg_rain = [180, 200, 220, 250, 300]  # 가상 데이터
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(years, avg_rain, marker='o', color='blue', linewidth=2)
    ax.set_xlabel('년도')
    ax.set_ylabel('평균 강수량 (mm)')
    ax.set_title('연간 강수량 추세 (기후변화로 증가 – 침수 빈도 ↑)')
    ax.grid(True, alpha=0.3)
    ax.axhline(200, color='red', linestyle='--', label='침수 임계값 (200mm)')
    ax.legend()
    return fig

def create_simulation_chart():
    fig, ax = plt.subplots(figsize=(8, 6))
    np.random.seed(42)
    sim_data = pd.DataFrame({
        'rainfall': np.random.uniform(50, 200, 50),
        'elevation': np.random.uniform(0, 50, 50),
        'risk': np.random.choice([0, 1], 50, p=[0.7, 0.3])
    })
    sim_data['sim_risk'] = (sim_data['rainfall'] / (sim_data['elevation'] + 1)) * 10 > 20
    scatter = ax.scatter(sim_data['rainfall'], sim_data['elevation'], c=sim_data['risk'], cmap='coolwarm', s=50)
    plt.colorbar(scatter, ax=ax, label='예측 위험도 (0: 저위험, 1: 고위험)')
    ax.set_xlabel('강수량 (mm)')
    ax.set_ylabel('고도 (m)')
    ax.set_title('침수 위험 예측 시각화 (GIS 히트맵 시뮬레이션)')
    ax.grid(True, alpha=0.3)
    return fig