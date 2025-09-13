import json
import logging
import os
import random
import socket
import sys
import time
import warnings
from datetime import datetime

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc # undetected_chromedriver 임포트 # type: ignore
import pandas as pd

# SSL 경고 메시지 숨기기
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def ensure_chrome_debug(port: int, user_data_dir: str) -> None:
    if not is_port_in_use(port):
        # logging.info(f"포트 {port}에서 실행 중인 크롬 브라우저가 없습니다. 새로 실행합니다.")
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        if not os.path.exists(chrome_path):
            raise FileNotFoundError(f"Chrome 실행 파일을 찾을 수 없습니다: {chrome_path}")
        cmd = f'"{chrome_path}" --remote-debugging-port={port} --user-data-dir="{user_data_dir}"'
        import subprocess
        subprocess.Popen(cmd)
        time.sleep(4)  # 브라우저 시작 대기
    else:
        logging.info(f"포트 {port}에서 이미 실행 중인 크롬 브라우저를 사용합니다.")


def connect_driver(port: int, chrome_main_path: str, user_data_dir: str) -> uc.Chrome:
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{port}")
    
    driver = uc.Chrome(
        options=chrome_options,
        use_subprocess=True
    )
    driver.implicitly_wait(1)
    return driver


def wait_for_page_load_and_handle_cloudflare(driver: uc.Chrome, product_id: str, timeout: int = 60, log_callback=None, stop_check_callback=None) -> bool:
    """상품 페이지로 이동하고, Cloudflare 인증에 걸리면 사용자에게 해결을 요청합니다."""
    product_url = f"https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo={product_id}"
    driver.get(product_url)
    if log_callback:
        log_callback(f"상품 페이지 로드 시도: {product_url}")

    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#gdasContents, .prd_detail_box"))
        )
        if log_callback:
            log_callback("페이지 콘텐츠 로드 완료. 인간적인 행동 시뮬레이션 중...")
        # 페이지가 로드된 후 인간적인 행동 시뮬레이션
        for _ in range(random.randint(1, 3)): # 1~3회 무작위 스크롤
            driver.execute_script(f"window.scrollBy(0, {random.randint(200, 800)});")
            time.sleep(random.uniform(0.5, 1.5)) # 0.5~1.5초 무작위 대기
        driver.execute_script("window.scrollTo(0, 0);") # 다시 맨 위로 스크롤
        time.sleep(random.uniform(1, 2)) # 마지막 대기

        return True
    except Exception as e:
        if log_callback:
            log_callback(f"페이지 콘텐츠 로드 실패. Cloudflare 또는 다른 인증 문제가 발생했을 수 있습니다. 오류: {e}")
            log_callback("브라우저 창을 확인하여 캡차를 수동으로 해결하거나, 로그인을 시도해주세요.")
            log_callback(f"현재 URL: {driver.current_url}")
        
        # GUI 메시지 박스를 통해 사용자에게 해결 요청
        if log_callback:
            log_callback("Cloudflare 인증 또는 로그인 후 다시 시도해주세요.")
        
        if stop_check_callback:
            stop_check_callback() # 수집 중지 요청
        return False


def extract_session_from_driver(driver: uc.Chrome) -> tuple[requests.Session, str]:
    session = requests.Session()
    for c in driver.get_cookies():
        session.cookies.set(c.get('name'), c.get('value'))
    user_agent = driver.execute_script("return navigator.userAgent;")
    return session, user_agent


def fetch_reviews(session: requests.Session, user_agent: str, product_id: str, total_pages: int, log_callback=None, stop_check_callback=None) -> list:
    all_reviews: list = []
    progress_interval = max(1, total_pages // 20)
    start_time = time.time()

    for page in range(1, total_pages + 1):
        if stop_check_callback and stop_check_callback():
            if log_callback:
                log_callback("수집 중지 요청 감지. 리뷰 수집을 중단합니다.")
            break
        headers = {
            'User-Agent': user_agent,
            'Referer': f'https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo={product_id}',
            'Accept': '*/*',
            'Accept-Language': 'ko,en;q=0.9,en-US;q=0.8',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua': '"Chromium";v="135", "Not.A/Brand";v="8"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
        }

        url = "https://www.oliveyoung.co.kr/store/goods/getGdasNewListJson.do"
        params = {
            'goodsNo': product_id,
            'gdasSort': '05',
            'itemNo': 'all_search',
            'pageIdx': page,
            'colData': '',
            'keywordGdasSeqs': '',
            'type': '',
            'point': '',
            'hashTag': '',
            'optionValue': '',
            'cTypeLength': '0',
        }

        max_retries = 3
        retry = 0
        response = None
        while retry < max_retries:
            if stop_check_callback and stop_check_callback():
                if log_callback:
                    log_callback("수집 중지 요청 감지. 리뷰 수집을 중단합니다.")
                return [] # 즉시 중단
            try:
                response = session.get(url, params=params, headers=headers, timeout=20, verify=False)
                if response.status_code == 200:
                    break
                retry += 1
                time.sleep(random.uniform(3, 6))
            except Exception as e:
                if log_callback:
                    log_callback(f"페이지 {page} 요청 오류, 재시도 {retry+1}/{max_retries}: {e}")
                retry += 1
                time.sleep(random.uniform(8, 12))
                continue

        time.sleep(random.uniform(1.2, 2.0))

        if not response or response.status_code != 200:
            if log_callback:
                log_callback(f"페이지 {page} 요청 실패: 상태 코드 {getattr(response, 'status_code', 'N/A')}")
            if response is not None and response.status_code == 429:
                wait_time = random.uniform(25, 35)
                if log_callback:
                    log_callback(f"429: {wait_time:.1f}초 대기 후 재시도 예정")
                time.sleep(wait_time)
            elif response is not None and response.status_code == 403:
                wait_time = random.uniform(40, 60)
                if log_callback:
                    log_callback(f"403: {wait_time:.1f}초 대기")
                time.sleep(wait_time)
            continue

        content_type = response.headers.get('Content-Type', '')
        if 'json' not in content_type.lower():
            if '<html' in response.text.lower():
                if log_callback:
                    log_callback(f"페이지 {page} 응답이 HTML입니다. 로그인/캡차 필요 가능성")
                if page == 1:
                    return []
                time.sleep(random.uniform(8, 12))
                continue

        try:
            data = response.json()
            if 'gdasList' in data:
                reviews_on_page = data['gdasList']
                all_reviews.extend(reviews_on_page)
                if log_callback:
                    log_callback(f"페이지 {page}: {len(reviews_on_page)}개 (총 {len(all_reviews)})")
                if len(reviews_on_page) == 0:
                    if log_callback:
                        log_callback(f"빈 페이지 감지: {page}. 종료")
                    break
            else:
                if log_callback:
                    log_callback(f"페이지 {page}에 gdasList 없음. 종료")
                break
        except json.JSONDecodeError:
            if log_callback:
                log_callback(f"페이지 {page} JSON 파싱 실패")
            if page <= 3:
                return []
            time.sleep(random.uniform(8, 12))
            continue

        if page % progress_interval == 0 or page == total_pages:
            elapsed = time.time() - start_time
            if log_callback:
                log_callback(f"진행률: {page/total_pages*100:.1f}% ({page}/{total_pages}), 경과 {elapsed:.1f}s")

    return all_reviews


def process_reviews(reviews: list):
    processed = []
    for r in reviews:
        try:
            nickname = r.get('mbrNickNm', '') or (r.get('mbrId') or '알 수 없음')
            user_id = r.get('mbrId', '') or '알 수 없음'
            rating10 = r.get('gdasScrVal', 0)
            rating5 = rating10 / 2
            date = r.get('dispRegDate', '')
            content = (r.get('gdasCont', '') or '').replace('<br/>', '\n').strip()
            option = r.get('itemNm', '')
            photo_list = r.get('photoList', []) or []
            has_photo = len(photo_list) > 0
            photo_urls = []
            for p in photo_list:
                path = p.get('appxFilePathNm')
                if path:
                    photo_urls.append(f"https://image.oliveyoung.co.kr/uploads/images/gdasEditor/{path}")
            help_cnt = r.get('recommCnt', 0)
            rank_info = '일반'
            rank = r.get('topRvrRnk', 0)
            if rank and rank > 0:
                rank_info = f"TOP {rank}위"
            skin_info = []
            for inf in r.get('addInfoNm', []) or []:
                skin_info.append(inf.get('mrkNm', ''))
            repurchase = r.get('firstGdasYn') == 'N'
            long_use = r.get('renewUsed1mmGdasYn') == 'Y'
            offline = False
            ord_no = r.get('ordNo', '')
            if ord_no and not ord_no.startswith('Y'):
                offline = True

            processed.append({
                '작성자': nickname,
                '아이디': user_id,
                '회원랭킹': rank_info,
                '평점': rating5,
                '작성일': date,
                '구매옵션': option,
                '리뷰내용': content,
                '리뷰형태': '포토리뷰' if has_photo else '일반리뷰',
                '사진여부': '있음' if has_photo else '없음',
                '사진URL': ';'.join(photo_urls),
                '도움이 돼요 수': help_cnt,
                '재구매': '예' if repurchase else '아니오',
                '한달이상사용': '예' if long_use else '아니오',
                '오프라인구매': '예' if offline else '아니오',
                '피부정보': ', '.join(skin_info) if skin_info else '',
            })
        except Exception as e:
            logging.warning(f"리뷰 처리 오류: {e}")
            continue

    return pd.DataFrame(processed)


def save_results(product_id: str, reviews: list, df, out_dir: str, log_callback=None) -> None:
    os.makedirs(out_dir, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_json = os.path.join(out_dir, f"올리브영_리뷰_원본_{product_id}_{date_str}.json")
    with open(raw_json, 'w', encoding='utf-8') as f:
        json.dump(reviews, f, ensure_ascii=False, indent=2)
    if log_callback:
        log_callback(f"원본 JSON 저장: {raw_json}")

    if df is not None and not df.empty:
        excel_path = os.path.join(out_dir, f"올리브영_리뷰_{product_id}_{date_str}.xlsx")
        json_processed = os.path.join(out_dir, f"올리브영_리뷰_가공_{product_id}_{date_str}.json")
        df.to_excel(excel_path, index=False, engine='openpyxl')
        df.to_json(json_processed, force_ascii=False, orient='records', indent=2)
        if log_callback:
            log_callback(f"엑셀 저장: {excel_path}")
            log_callback(f"가공 JSON 저장: {json_processed}")
    else:
        if log_callback:
            log_callback("가공 데이터프레임이 비어 있어 엑셀/가공JSON 저장 생략")

def scrape_reviews(product_id: str, max_pages: int, out_dir: str, port: int, user_data_dir: str, chrome_main_path: str, log_callback=None, stop_check_callback=None):
    # if log_callback:
    #     log_callback(f"스크래핑 시작: 상품 ID={product_id}, 최대 페이지={max_pages}, 출력 디렉토리={out_dir}, 포트={port}, 사용자 데이터 디렉토리={user_data_dir}")
    
    ensure_chrome_debug(port, user_data_dir)
    driver = None
    try:
        driver = connect_driver(port, chrome_main_path=chrome_main_path, user_data_dir=user_data_dir)
        # wait_for_page_load_and_handle_cloudflare에 log_callback과 stop_check_callback 전달
        if not wait_for_page_load_and_handle_cloudflare(driver, product_id, timeout=60, log_callback=log_callback, stop_check_callback=stop_check_callback):
            if log_callback:
                log_callback("Cloudflare 또는 페이지 로드 문제로 인증 정보 획득 실패. 스크립트를 종료합니다.")
            return

        session, user_agent = extract_session_from_driver(driver)
        reviews = fetch_reviews(session, user_agent, product_id, max_pages, log_callback, stop_check_callback)
        if stop_check_callback and stop_check_callback():
            if log_callback:
                log_callback("사용자에 의해 수집이 중지되었습니다. 결과 저장을 건너뜁니다.")
            return # 중지 요청이 있었으므로 결과 저장을 건너옴
        
        if not reviews:
            if log_callback:
                log_callback("수집된 리뷰가 없습니다.")
            return
        df = process_reviews(reviews)
        save_results(product_id, reviews, df, out_dir, log_callback)
    except Exception as e:
        if log_callback:
            log_callback(f"스크래핑 중 오류 발생: {e}")
        logging.error(f"스크래핑 중 예상치 못한 오류 발생: {e}", exc_info=True)
    finally:
        if driver:
            try:
                driver.quit() # 드라이버 명시적 종료
                if log_callback:
                    log_callback("Chrome 드라이버를 종료했습니다.")
            except Exception as e:
                if log_callback:
                    log_callback(f"Chrome 드라이버 종료 중 오류 발생: {e}")
                logging.error(f"Chrome 드라이버 종료 중 오류 발생: {e}", exc_info=True)
