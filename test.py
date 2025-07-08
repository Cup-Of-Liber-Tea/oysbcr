import sys
import subprocess
import os
import time
import json
import random
from datetime import datetime
import traceback

# 필요한 패키지 설치 함수 (curl_cffi, seleniumbase 추가)
def install_packages():
    try:
        packages = ['pandas', 'openpyxl', 'seleniumbase', 'curl_cffi']
        for package in packages:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        print("필요한 패키지 설치 완료")
    except Exception as e:
        print(f"패키지 설치 중 오류 발생: {e}")
        print("아래 명령어로 수동 설치를 시도해보세요:")
        print("pip install pandas openpyxl seleniumbase curl_cffi")
        sys.exit(1)

# 패키지 존재 여부 확인 및 설치
try:
    import pandas as pd
    from curl_cffi.requests import Session
    from seleniumbase import SB
except ImportError:
    print("필요한 패키지를 설치합니다...")
    install_packages()
    import pandas as pd
    from curl_cffi.requests import Session
    from seleniumbase import SB

def acquire_auth_info_with_selenium(product_id: str):
    """
    SeleniumBase를 사용하여 캡차를 통과하고,
    API 요청에 필요한 쿠키와 헤더 정보를 추출하여 반환합니다.
    """
    print("Selenium을 사용하여 인증 정보 획득을 시작합니다...")
    try:
        with SB(uc=True, headless=False) as sb:
            initial_url = f'https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo={product_id}'
            sb.open(initial_url)
            
            print("캡차(CAPTCHA)가 나타나면 5분 안에 해결해주세요...")
            sb.wait_for_element_visible("#gdasContents", timeout=300)
            print("초기 인증 완료. (리뷰 영역 로드 확인)")
            sb.sleep(1) # 안정성을 위한 짧은 대기

            # 쿠키와 헤더 정보 추출
            cookies = sb.get_cookies()
            cookie_dict = {c['name']: c['value'] for c in cookies}
            
            user_agent = sb.get_user_agent()
            headers = {
                'Referer': initial_url,
                'User-Agent': user_agent,
                'X-Requested-With': 'XMLHttpRequest',
            }
            
            # 추출한 정보를 반환
            auth_info = {'cookies': cookie_dict, 'headers': headers}
            print("인증 정보를 성공적으로 획득했습니다.")
            return auth_info

    except Exception as e:
        print(f"Selenium 인증 정보 획득 실패: {e}", file=sys.stderr)
        traceback.print_exc()
        return None

def get_all_reviews(product_id: str, max_pages: int, auth_info: dict):
    """
    인증 정보를 사용하여 API를 통해 모든 리뷰를 수집합니다.
    """
    all_reviews = []
    
    with Session(impersonate="chrome110") as session:
        # 인증 정보 설정
        session.cookies.update(auth_info['cookies'])
        session.headers.update(auth_info['headers'])
        
        for page in range(1, max_pages + 1):
            url = f"https://www.oliveyoung.co.kr/store/goods/getGdasNewListJson.do?goodsNo={product_id}&gdasSort=05&itemNo=all_search&pageIdx={page}"
            
            try:
                print(f"{page}/{max_pages} 페이지 요청 중...")
                response = session.get(url, timeout=20)
                response.raise_for_status()
                data = response.json()
                
                reviews_on_page = data.get('gdasList', [])
                if not reviews_on_page:
                    print(f"마지막 페이지({page})에 도달했거나 더 이상 리뷰가 없습니다. 수집을 종료합니다.")
                    break
                
                all_reviews.extend(reviews_on_page)
                print(f"  -> {len(reviews_on_page)}개 리뷰 발견 (총 {len(all_reviews)}개)")
                
                # 올리브영 서버 부하를 줄이기 위한 랜덤 딜레이
                time.sleep(random.uniform(0.5, 1.5))

            except Exception as e:
                print(f"페이지 {page} 요청 중 오류 발생: {e}")
                if "403 Forbidden" in str(e):
                    print("오류: 403 Forbidden. 인증이 만료되었거나 차단되었을 수 있습니다.")
                break

    return all_reviews


# 리뷰 데이터 처리 및 저장 (기존과 동일)
def process_reviews(reviews):
    """
    수집된 리뷰 데이터를 처리하고 DataFrame으로 변환합니다.
    
    Args:
        reviews (list): 수집된 리뷰 데이터 리스트
    
    Returns:
        pandas.DataFrame: 처리된 리뷰 데이터
    """
    processed_data = []
    
    for review in reviews:
        try:
            # 기본 리뷰 정보 추출
            nickname = review.get('mbrNickNm', '')
            user_id = review.get('mbrId', '')
            if not user_id:
                user_id = '알 수 없음'
                
            # 닉네임이 없는 경우 아이디 값 사용
            if not nickname:
                nickname = user_id
            
            # 평점
            rating = review.get('gdasScrVal', 0)
            # 평점 변환 (10점 만점 → 5점 만점)
            converted_rating = rating / 2
            
            # 작성일
            date = review.get('dispRegDate', '')
            
            # 리뷰 내용
            content = review.get('gdasCont', '').replace('<br/>', '\n').strip()
            
            # 구매 옵션
            option = review.get('itemNm', '')
            
            # 리뷰 형태 판별 (포토리뷰/일반리뷰)
            review_type = "일반리뷰"
            
            # 사진 여부 확인
            has_photo = False
            photo_urls = []
            photo_list = review.get('photoList', [])
            if photo_list and len(photo_list) > 0:
                has_photo = True
                review_type = "포토리뷰"
                # 전체 URL로 이미지 경로 구성
                for photo in photo_list:
                    file_path = photo.get('appxFilePathNm', '')
                    if file_path:
                        full_url = f"https://image.oliveyoung.co.kr/uploads/images/gdasEditor/{file_path}"
                        photo_urls.append(full_url)
            
            # 도움이 돼요 수
            help_count = review.get('recommCnt', 0)
            
            # 회원 랭킹 정보 추출
            rank_info = "일반"
            top_reviewer_rank = review.get('topRvrRnk', 0)
            if top_reviewer_rank and top_reviewer_rank > 0:
                rank_info = f"TOP {top_reviewer_rank}위"
            
            # 피부 정보 추출
            skin_info = []
            add_info_list = review.get('addInfoNm', [])
            if add_info_list:
                for info in add_info_list:
                    skin_info.append(info.get('mrkNm', ''))
            
            # 재구매 여부 추출 (firstGdasYn 값이 'N'이면 재구매)
            repurchase = False
            if review.get('firstGdasYn') == 'N':
                repurchase = True
                
            # 한달이상 사용 여부 추출 (renewUsed1mmGdasYn 값이 'Y'이면 한달 이상 사용)
            long_use = False
            if review.get('renewUsed1mmGdasYn') == 'Y':
                long_use = True
            
            # 오프라인 구매 여부 (ordNo 필드가 'Y'로 시작하지 않으면 오프라인 구매)
            offline_purchase = False
            order_no = review.get('ordNo', '')
            if order_no and not order_no.startswith('Y'):
                offline_purchase = True
            
            processed_data.append({
                '작성자': nickname,
                '아이디': user_id,
                '회원랭킹': rank_info,
                '평점': converted_rating,
                '작성일': date,
                '구매옵션': option,
                '리뷰내용': content,
                '리뷰형태': review_type,
                '사진여부': '있음' if has_photo else '없음',
                '사진URL': ';'.join(photo_urls),
                '도움이 돼요 수': help_count,
                '재구매': '예' if repurchase else '아니오',
                '한달이상사용': '예' if long_use else '아니오',
                '오프라인구매': '예' if offline_purchase else '아니오',
                '피부정보': ', '.join(skin_info) if skin_info else ''
            })
        except Exception as e:
            print(f"리뷰 처리 중 오류 발생: {e}")
            continue
    
    # DataFrame 생성
    df = pd.DataFrame(processed_data)
    
    # 데이터가 없는 경우 빈 DataFrame 반환
    if df.empty:
        print("처리할 리뷰 데이터가 없습니다.")
        return df
    
    return df

def main():
    """
    메인 실행 함수
    """
    print("=" * 50)
    print("올리브영 리뷰 추출 프로그램")
    print("=" * 50)
    
    # 사용자 입력 받기
    product_id = input("올리브영 상품 ID를 입력하세요 (예: A000000159233): ").strip()
    if not product_id:
        print("상품 ID가 입력되지 않았습니다. 프로그램을 종료합니다.")
        sys.exit(1)
    
    try:
        max_pages = int(input("가져올 최대 페이지 수를 입력하세요 (기본값: 100): ") or "100")
    except ValueError:
        print("올바른 숫자를 입력하지 않았습니다. 기본값 100을 사용합니다.")
        max_pages = 100
    
    # 결과 형식 선택
    output_format = input("결과 형식을 선택하세요 (1: 엑셀, 2: JSON, 기본값: 1): ").strip() or "1"
    
    print(f"\n{product_id} 상품의 리뷰를 최대 {max_pages}페이지까지 가져옵니다...\n")
    
    try:
        # 1. Selenium으로 인증 정보 획득
        auth_info = acquire_auth_info_with_selenium(product_id)
        if not auth_info:
            print("인증 정보 획득에 실패하여 프로그램을 종료합니다.")
            sys.exit(1)
        
        # 2. 획득한 정보로 모든 리뷰 수집
        reviews = get_all_reviews(product_id, max_pages, auth_info)
        
        if not reviews:
            print("수집된 리뷰가 없습니다. 프로그램을 종료합니다.")
            sys.exit(1)
        
        # 원본 데이터는 이제 임시 파일로 관리되므로 별도 저장 로직은 제거 가능 (또는 유지)
        print(f"총 {len(reviews)}개의 리뷰를 수집했습니다. 데이터 처리 중...")
        
        # 현재 날짜와 시간을 파일명에 포함
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 리뷰 데이터 처리
        df = process_reviews(reviews)
        
        if df.empty:
            print("처리된 리뷰 데이터가 없습니다. 프로그램을 종료합니다.")
            sys.exit(1)
        
        if output_format == "1":  # 엑셀 형식
            output_filename = f'올리브영_리뷰_{product_id}_{date_str}.xlsx'
            df.to_excel(output_filename, index=False, engine='openpyxl')
            print(f"\n리뷰 추출 완료!")
            print(f"총 {len(df)}개의 리뷰를 '{output_filename}' 파일로 저장했습니다.")
            print(f"파일 위치: {os.path.abspath(output_filename)}")
        else:  # JSON 형식
            output_filename = f'올리브영_리뷰_가공_{product_id}_{date_str}.json'
            df.to_json(output_filename, force_ascii=False, orient='records', indent=2)
            print(f"\n리뷰 추출 완료!")
            print(f"총 {len(df)}개의 리뷰를 '{output_filename}' 파일로 저장했습니다.")
            print(f"파일 위치: {os.path.abspath(output_filename)}")
    
    except KeyboardInterrupt:
        print("\n사용자에 의해 프로그램이 중단되었습니다.")
        sys.exit(0)
    except Exception as e:
        print(f"\n프로그램 실행 중 오류가 발생했습니다: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
