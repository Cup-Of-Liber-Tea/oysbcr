from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import chromedriver_autoinstaller
import subprocess
import logging
import time
import socket
import os

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 크롬 드라이버 자동 설치
chromedriver_autoinstaller.install()

# 이미 디버깅 모드로 실행 중인 크롬 브라우저가 있는지 확인하는 함수
def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

# 디버깅 포트 설정
debug_port = 9222
user_data_dir = r"E:\brwProf\User Data"

# 이미 실행 중인 브라우저가 없을 때만 새로 실행
if not is_port_in_use(debug_port):
    logging.info(f"포트 {debug_port}에서 실행 중인 크롬 브라우저가 없습니다. 새로 실행합니다.")
    subprocess.Popen(f'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe --remote-debugging-port={debug_port} --user-data-dir="{user_data_dir}"')
    logging.info("크롬 브라우저 디버깅 모드로 실행")
    # 브라우저가 완전히 시작될 때까지 잠시 대기
    time.sleep(4) 
else:
    logging.info(f"포트 {debug_port}에서 이미 실행 중인 크롬 브라우저를 사용합니다.")

# 디버깅 모드로 실행된 크롬에 연결
chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")

# 브라우저 연결
browser = webdriver.Chrome(options=chrome_options)
# 암시적 대기 시간 줄이기 (10초 -> 1초)
browser.implicitly_wait(1)
logging.info("크롬 브라우저에 연결 완료")

# 네이버 블로그 이웃 목록 페이지로 이동
browser.get("https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo=A000000223414&dispCatNo=90000010009&trackingCd=Best_Sellingbest&t_page=%EB%9E%AD%ED%82%B9&t_click=%ED%8C%90%EB%A7%A4%EB%9E%AD%ED%82%B9_%EC%A0%84%EC%B2%B4_%EC%83%81%ED%92%88%EC%83%81%EC%84%B8&t_number=1")
try:
    if browser.window_handles: # 활성 창이 있는지 확인
        logging.info(f"현재 페이지 제목: {browser.title}")
    else:
        logging.error("활성 브라우저 창을 찾을 수 없습니다.")
except Exception as e:
    logging.error(f"페이지 제목을 가져오는 중 오류 발생: {e}")

# 이미 처리한 블로그 이름을 저장할 집합
processed_blogs = set()

# 빠른 요소 탐색을 위한 함수
def fast_find_element(css_selector):
    """JavaScript를 사용하여 빠르게 요소를 찾음"""
    element = browser.execute_script(f"""
        return document.querySelector("{css_selector}");
    """)
    return element

def fast_find_elements(css_selector):
    """JavaScript를 사용하여 빠르게 요소들을 찾음"""
    elements = browser.execute_script(f"""
        return Array.from(document.querySelectorAll("{css_selector}"));
    """)
    return elements

def fast_click(element):
    """JavaScript를 사용하여 빠르게 요소 클릭"""
    if element:
        browser.execute_script("arguments[0].click();", element)
        return True
    return False

