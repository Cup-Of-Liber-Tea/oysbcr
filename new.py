import logging
import time
import os
import random
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc # undetected_chromedriver 임포트 # type: ignore

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def connect_driver(chrome_main_path: str, user_data_dir: str) -> uc.Chrome:
    """undetected_chromedriver를 사용하여 크롬 브라우저에 연결합니다."""
    chrome_options = Options()
    # undetected_chromedriver를 사용하여 드라이버 초기화
    driver = uc.Chrome(
        options=chrome_options,
        use_subprocess=True,
        browser_executable_path=chrome_main_path,
        user_data_dir=user_data_dir
    )
    driver.implicitly_wait(1)  # 암시적 대기 시간
    return driver

def wait_for_page_load_and_handle_cloudflare(driver: uc.Chrome, product_id: str, timeout: int = 60) -> bool:
    """상품 페이지로 이동하고, Cloudflare 인증에 걸리면 사용자에게 해결을 요청합니다."""
    product_url = f"https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo={product_id}"
    driver.get(product_url)
    logging.info(f"상품 페이지 로드 시도: {product_url}")

    try:
        # 페이지의 주요 콘텐츠가 로드될 때까지 기다립니다.
        # 여기서는 리뷰 영역 (#gdasContents) 또는 상품 정보 영역 (.prd_detail_box)을 기다립니다.
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#gdasContents, .prd_detail_box"))
        )
        logging.info("페이지 콘텐츠 로드 완료. 인간적인 행동 시뮬레이션 중...")
        # 페이지가 로드된 후 인간적인 행동 시뮬레이션
        for _ in range(random.randint(1, 3)): # 1~3회 무작위 스크롤
            driver.execute_script(f"window.scrollBy(0, {random.randint(200, 800)});")
            time.sleep(random.uniform(0.5, 1.5)) # 0.5~1.5초 무작위 대기
        driver.execute_script("window.scrollTo(0, 0);") # 다시 맨 위로 스크롤
        time.sleep(random.uniform(1, 2)) # 마지막 대기

        return True
    except Exception:
        logging.warning("페이지 콘텐츠 로드 실패. Cloudflare 또는 다른 인증 문제가 발생했을 수 있습니다.")
        logging.warning("브라우저 창을 확인하여 캡차를 수동으로 해결하거나, 로그인을 시도해주세요.")
        logging.warning(f"현재 URL: {driver.current_url}")
        input("Cloudflare 인증 또는 로그인 후 브라우저 창에서 Enter 키를 누르세요...")
        # 사용자 입력 후 다시 한번 콘텐츠 로드 시도
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#gdasContents, .prd_detail_box"))
            )
            logging.info("Cloudflare 해결 후 페이지 콘텐츠 로드 완료.")
            # 인간적인 행동 시뮬레이션 다시
            for _ in range(random.randint(1, 3)):
                driver.execute_script(f"window.scrollBy(0, {random.randint(200, 800)});")
                time.sleep(random.uniform(0.5, 1.5))
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(random.uniform(1, 2))
            return True
        except Exception:
            logging.error("사용자 해결 후에도 Cloudflare/인증 문제 해결 실패.")
            return False

# 메인 실행 블록
if __name__ == '__main__':
    user_data_dir = r"E:\brwProf\User Data"
    chrome_main_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    product_id = "A000000223414" # 예시 상품 ID

    driver = connect_driver(chrome_main_path, user_data_dir)
    try:
        if not wait_for_page_load_and_handle_cloudflare(driver, product_id, timeout=60):
            logging.error("Cloudflare 또는 페이지 로드 문제로 브라우저 연결 실패. 스크립트를 종료합니다.")
        else:
            logging.info("성공적으로 브라우저에 연결하고 Cloudflare를 처리했습니다.")
            logging.info(f"현재 페이지 제목: {driver.title}")
    finally:
        try:
            driver.quit()
        except Exception as e:
            logging.warning(f"드라이버 종료 중 오류 발생 (무시 가능): {e}")
