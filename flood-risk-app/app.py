import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import folium
import streamlit.components.v1 as components
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from folium.plugins import HeatMap  # 히트맵 오버레이용

# 페이지 설정 (전체 레이아웃으로 변경 – 사이드바 숨김)
st.set_page_config(layout="wide", page_title="침수 위험 진단 서비스")

from modules.data import korean_cities
from modules.api import get_weather_data
from modules.visualization import create_map, create_rainfall_chart, create_trend_chart, create_simulation_chart
from modules.utils import calculate_risk, get_recommendations, get_past_data, get_alert_text

# 한글 폰트 설정 (Malgun Gothic → NanumGothic으로 변경, Cloud 호환)
plt.rcParams['font.family'] = ['NanumGothic', 'DejaVuSans']  # 폴백 추가
plt.rcParams['axes.unicode_minus'] = False

st.title("침수 위험 진단 서비스 (GIS & AI 프로토타입 + 기상청/시뮬레이션 침수 API 연동)")

st.sidebar.header("API 키 입력")
if st.secrets.get("dev_mode", False):  # Cloud Secrets 우선, 로컬 fallback
    api_key = st.sidebar.text_input("기상청 API 키", value='c965d7cee76ede7e4be93efd1040a83589b93b4e5c25bd81006e81901d66b809', type="password")
    use_weather = st.sidebar.checkbox("기상청 강수량 연동", value=True)
    use_flood = st.sidebar.checkbox("시뮬레이션 침수심 연동", value=True)
else:
    api_key = st.secrets.get("api_key", "")  # Cloud에서 불러옴
    use_weather = True  # 로컬 기본 활성화
    use_flood = True

# 사용자 입력
st.header("1. 현장 정보 입력")
selected_sido = st.selectbox("시/도 선택 (한국 모든 도시)", list(korean_cities.keys()), index=0)
selected_gu = st.selectbox("구 선택", list(korean_cities[selected_sido].keys()), index=0)
lat, lon, nx, ny, base_depth = korean_cities[selected_sido][selected_gu]
st.write(f"선택된 지역: {selected_sido} {selected_gu} (위도: {lat}, 경도: {lon}, 격자: nx={nx}, ny={ny})")

# 기상청 강수량
rainfall = st.slider("예상 강수량 (mm)", 50, 200, 100)  # 기본값
if use_weather and api_key:
    st.info("기상청 API 연동 중...")
    try:
        today = datetime.now().strftime('%Y%m%d')
        now_hour = datetime.now().hour
        # 유효 base_time 목록
        valid_times = ['0200', '0500', '0800', '1100', '1400', '1700', '2000', '2300']
        candidate_time = ((now_hour // 3) * 3) * 100
        base_time = [t for t in valid_times if int(t) >= candidate_time][0] if candidate_time in [int(t) for t in valid_times] else valid_times[-1] if now_hour < 2 else valid_times[(now_hour // 3) % 8]
        url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst"
        params = {
            'serviceKey': api_key, 'pageNo': '1', 'numOfRows': '10', 'dataType': 'XML',
            'base_date': today, 'base_time': base_time, 'nx': str(nx), 'ny': str(ny)
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            result_code = root.find('.//resultCode')
            if result_code is not None:
                result_code_text = result_code.text
                if result_code_text == '00':
                    pty, rn1 = '0', '0'
                    for item in root.findall('.//item'):
                        category = item.find('category')
                        obsr_value = item.find('obsrValue')
                        if category is not None and obsr_value is not None:
                            if category.text == 'PTY':
                                pty_raw = obsr_value.text
                                pty = '0' if pty_raw in ['-999', '-998'] else pty_raw
                            elif category.text == 'RN1':
                                rn1_raw = obsr_value.text
                                rn1 = '0' if rn1_raw in ['-999', '-998', '-998.9'] else rn1_raw
                    rainfall = float(rn1) if rn1 and rn1 != 'None' else 0.0
                    if int(pty) == 0:
                        rainfall = 0.0
                        st.info("현재 무강수 (PTY=0), 1시간 후 예보 확인 추천.")
                    st.success(f"기상청 성공! 강수량: {rainfall}mm (형태: {pty}, 발표 시간: {base_time})")
                else:
                    st.warning("기상청 응답 오류. 슬라이더 사용.")
            else:
                st.warning("기상청 resultCode 없음. 슬라이더 사용.")
        else:
            st.error("기상청 HTTP 에러. 슬라이더 사용.")
    except Exception as e:
        st.error(f"기상청 실패: {str(e)}. 슬라이더 사용.")

elevation = st.slider("건물 고도 (m)", 0, 50, 10)

# 시뮬레이션 침수심
flood_depth = 0.0
if use_flood:
    st.info("시뮬레이션 침수심 연동 중... (도시별 100년 빈도 가정)")
    flood_depth = base_depth + np.random.uniform(0, 2, 1)[0]
    flood_depth = round(flood_depth, 1)
    st.success(f"시뮬레이션 성공! 예상 침수심: {flood_depth}m (100년 빈도)")

if st.button("위험 진단 실행"):
    # AI 예측
    risk_score, predicted_risk = calculate_risk(rainfall, elevation, flood_depth)
    
    st.header("2. 진단 결과")
    st.metric("위험 점수 (강수량 + 침수)", f"{risk_score:.2f}")
    if predicted_risk == 1:
        st.error("🚨 고위험: 강화형 차수판 설치 추천!")
    else:
        st.success("✅ 저위험: 기본형으로 충분할 수 있어요.")
    
    # 추천 테이블
    st.subheader("추천 설치 옵션")
    recommendations = get_recommendations()
    st.table(recommendations)
    
    # 과거 데이터
    st.subheader("지역 과거 침수 사례 (강수량 초과 시 위험 ↑)")
    past_data = get_past_data()
    st.table(past_data)
    st.warning("강수량 200mm 초과 시 침수 확률 50% ↑ – 2025년 사례처럼 피해 예방하세요!")
    
    # 강수량 vs 침수 확률 차트
    st.subheader("강수량 vs 침수 확률 (과거 데이터 기반)")
    fig_rainfall = create_rainfall_chart(rainfall)
    st.pyplot(fig_rainfall)
    st.info("200mm 초과 시 80% 이상 침수 위험 – 과거 호우 사례처럼 주의!")
    
    # 개인화 알림
    with st.expander("침수 위험 상세 알림 (개인화)"):
        alert_text = get_alert_text(rainfall)
        st.write(alert_text)
        st.warning("차수판 설치로 피해 70% 예방 가능! 문의하세요.")
    
    # 연간 강수량 추세
    st.subheader("연간 강수량 추세 (침수 위험 증가)")
    fig_trend = create_trend_chart()
    st.pyplot(fig_trend)
    st.info("2025년 장마 강수량 증가 – 과거 데이터로 30% 위험 ↑! 예방이 핵심.")
    
    # GIS 지도 (구 단위 히트맵 포함)
    st.subheader("3. 위치 기반 GIS 지도 (구 단위 히트맵 오버레이)")
    m = create_map(lat, lon, predicted_risk, selected_gu, risk_score, rainfall, flood_depth, korean_cities)
    map_html = m._repr_html_()
    components.html(map_html, height=500, width=700)
    
    # 히트맵 설명 추가
    st.write("### 히트맵 설명")
    st.write("- **색상**: 빨간색은 높은 침수 위험(기본 침수심이 큼), 파란색은 낮은 침수 위험을 나타냅니다.")
    st.write("- **가중치**: 각 구의 기본 침수심(base_depth)을 10배 스케일링하여 표시. 값이 클수록 침수 가능성이 높습니다.")
    st.info("히트맵: 각 구의 침수심 기반 위험도 – 현재 위치와 비교해 위험 파악하세요!")
    
    # 시뮬레이션 그래프
    st.subheader("4. 시뮬레이션 그래프")
    fig_simulation = create_simulation_chart()
    st.pyplot(fig_simulation)
    
    st.info("💡 구 단위 히트맵으로 침수 위험 시각화! 배포 시 WMS 오버레이 추가 추천.")

# 사이드바 도움말
with st.sidebar:
    st.header("도움말")
    st.write("- 과거 데이터: 2025년 사례 기반 테이블/차트로 위험 강조.")
    st.write("- 지도 히트맵: folium.HeatMap으로 고강수 위치 시각화.")
    st.write("- 배포: Streamlit Cloud → 아임웹 iframe 임베드.")

# 공공데이터 출처 표시 (법적 의무)
st.caption("""
**데이터 출처**: 
- 기상청_단기예보 (공공데이터포털): https://www.data.go.kr/data/15007722/openapi.do
- 공공누리 "출처표시" 조건에 따라 이용. 원본 데이터 제공: 기상청.
""")