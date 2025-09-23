import requests
import xml.etree.ElementTree as ET
from datetime import datetime

def get_weather_data(api_key, nx, ny, default_rainfall):
    """
    기상청 API를 호출하여 실시간 강수량 데이터를 가져옴.
    실패 시 기본 슬라이더 값을 반환.
    """
    try:
        today = datetime.now().strftime('%Y%m%d')
        now_hour = datetime.now().hour
        candidate_time = ((now_hour // 3) * 3)
        base_time = f"{candidate_time:02d}00" if candidate_time >= 2 else "0200"
        url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst"
        params = {
            'serviceKey': api_key, 'pageNo': '1', 'numOfRows': '10', 'dataType': 'XML',
            'base_date': today, 'base_time': base_time, 'nx': str(nx), 'ny': str(ny)
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            result_code = root.find('.//resultCode')
            if result_code is not None and result_code.text == '00':
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
                return rainfall
        return default_rainfall
    except Exception as e:
        return default_rainfall