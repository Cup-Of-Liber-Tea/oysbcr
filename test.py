import sys
import subprocess
import os
import time
import json
import random
import requests
from datetime import datetime

# 필요한 패키지 설치 함수
def install_packages():
    try:
        packages = ['pandas', 'requests', 'openpyxl']
        for package in packages:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        print("필요한 패키지 설치 완료")
    except Exception as e:
        print(f"패키지 설치 중 오류 발생: {e}")
        print("아래 명령어로 수동 설치를 시도해보세요:")
        print("pip install pandas requests openpyxl")
        sys.exit(1)

# 패키지 존재 여부 확인 및 설치
try:
    import pandas as pd
except ImportError:
    print("필요한 패키지를 설치합니다...")
    install_packages()
    import pandas as pd

# 임의의 User-Agent 생성 함수
def get_random_user_agent():
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0'
    ]
    return random.choice(user_agents)

# API 호출을 통해 리뷰 데이터 수집
def get_reviews(product_id, total_pages=100):
    """
    API를 호출하여 리뷰 데이터를 가져옵니다.
    
    Args:
        product_id (str): 상품 ID
        total_pages (int): 가져올 총 페이지 수
    
    Returns:
        list: 수집된 리뷰 데이터 리스트
    """
    all_reviews = []
    
    # 세션 생성 - 쿠키 유지
    session = requests.Session()
    
    # 먼저 상품 페이지 방문하여 필요한 쿠키 획득
    product_url = f'https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo={product_id}'
    try:
        session.get(product_url, 
                   headers={'User-Agent': get_random_user_agent()},
                   timeout=10)
        # 약간의 지연 시간
        time.sleep(2)
    except Exception as e:
        print(f"상품 페이지 접속 실패: {e}")
    
    # 진행 상황 표시 변수
    progress_interval = max(1, total_pages // 20)  # 5% 간격으로 진행 상황 표시
    start_time = time.time()
    
    for page in range(1, total_pages + 1):
        # 헤더 설정 - 매 요청마다 약간 다르게 설정
        headers = {
            'User-Agent': get_random_user_agent(),
            'Referer': f'https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo={product_id}',
            'Accept': '*/*',
            'Accept-Language': 'ko,en;q=0.9,en-US;q=0.8',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua': '"Microsoft Edge";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin'
        }
        
        # API URL 및 파라미터 설정
        url = "https://www.oliveyoung.co.kr/store/goods/getGdasNewListJson.do"
        
        params = {
            'goodsNo': product_id,
            'gdasSort': '05',  # 최신순
            'itemNo': 'all_search',
            'pageIdx': page,
            'colData': '',
            'keywordGdasSeqs': '',
            'type': '',
            'point': '',
            'hashTag': '',
            'optionValue': '',
            'cTypeLength': '0'
        }
        
        try:
            # API 호출
            response = session.get(url, params=params, headers=headers, timeout=15)
            
            # 응답 확인
            if response.status_code == 200:
                # 응답 타입 확인
                content_type = response.headers.get('Content-Type', '')
                if 'application/json' not in content_type and 'text/json' not in content_type and 'text/plain' not in content_type:
                    if '<html' in response.text.lower():
                        print(f"페이지 {page}의 응답이 HTML 형식입니다. API가 차단되었을 수 있습니다.")
                        if page <= 2:
                            print("\n=== 도움말 ===")
                            print("1. 올리브영 웹사이트에 직접 접속해 로그인을 시도해 보세요.")
                            print("2. 웹사이트에서 캡차(CAPTCHA) 인증이 필요할 수 있습니다.")
                            print("3. VPN이나 프록시를 사용 중이라면 해제해 보세요.")
                            print("4. 잠시 후에 다시 시도해 보세요.")
                            print("============")
                            
                            if page == 1:
                                print("첫 페이지 요청에 실패했습니다. 프로그램을 종료합니다.")
                                sys.exit(1)
                        time.sleep(10)  # 10초 대기
                        continue
                
                try:
                    data = response.json()
                    
                    # 올리브영 API 응답 구조에 맞게 리뷰 데이터 추출
                    if 'gdasList' in data:
                        reviews_on_page = data['gdasList']
                        all_reviews.extend(reviews_on_page)
                        
                        # 현재 페이지 리뷰 정보 출력
                        print(f"페이지 {page}: {len(reviews_on_page)}개의 리뷰를 수집했습니다. (총 {len(all_reviews)}개)")
                        
                        # 각 리뷰 정보 간략히 출력
                        for idx, review in enumerate(reviews_on_page, 1):
                            print(f"  - 리뷰 {idx}: {review.get('gdasScrVal')}점, {review.get('mbrNickNm')}, 작성일: {review.get('dispRegDate')}")
                        
                        # 만약 현재 페이지에 리뷰가 없거나 예상보다 적으면, 마지막 페이지에 도달한 것
                        if len(reviews_on_page) == 0:
                            print(f"마지막 페이지 ({page})에 도달했습니다. 총 {len(all_reviews)}개의 리뷰를 수집했습니다.")
                            break
                    else:
                        print(f"페이지 {page}에서 리뷰 데이터를 찾을 수 없습니다.")
                        print(f"응답: {json.dumps(data, ensure_ascii=False, indent=2)[:200]}...")
                        # API 응답에 gdasList가 없으면 마지막 페이지로 간주
                        break
                except json.JSONDecodeError:
                    print(f"페이지 {page}의 응답을 JSON으로 파싱할 수 없습니다.")
                    print(f"응답: {response.text[:200]}...")  # 응답의 처음 200자만 출력
                    
                    # HTML 응답인지 확인
                    if '<html' in response.text.lower():
                        print("응답이 HTML 형식입니다. API가 차단되었거나 로그인이 필요할 수 있습니다.")
                        # 첫 페이지에서 이런 일이 발생하면 종료
                        if page <= 3:
                            print("초기 페이지에서 오류가 발생했습니다. 프로그램을 종료합니다.")
                            sys.exit(1)
                    
                    if page > 1:  # 첫 페이지가 아니면 API 오류로 간주하고 스킵
                        time.sleep(15)  # 15초 대기
                        continue
                    else:
                        print("API 응답 형식이 예상과 다릅니다. 프로그램을 종료합니다.")
                        sys.exit(1)
            else:
                print(f"페이지 {page} 요청 실패: 상태 코드 {response.status_code}")
                
                try:
                    print(f"응답: {response.text[:200]}...")  # 응답의 처음 200자만 출력
                except:
                    print("응답 내용을 표시할 수 없습니다.")
                
                # 429 (Too Many Requests) 오류 시 더 오래 대기
                if response.status_code == 429:
                    wait_time = 60  # 60초 대기
                    print(f"너무 많은 요청을 보냈습니다. {wait_time}초 대기 후 다시 시도합니다.")
                    time.sleep(wait_time)
                    page -= 1  # 같은 페이지 다시 시도
                    continue
                
                # 403 (Forbidden) 오류 시 더 오래 대기하고 헤더 변경
                if response.status_code == 403:
                    wait_time = 120  # 120초 대기
                    print(f"접근이 거부되었습니다. {wait_time}초 대기 후 다시 시도합니다.")
                    time.sleep(wait_time)
                    continue
                
                # 500번대 서버 오류이면 잠시 대기 후 계속
                if 500 <= response.status_code < 600:
                    time.sleep(20)
                    continue
                
            # 진행 상황 표시
            if page % progress_interval == 0 or page == total_pages:
                progress = (page / total_pages) * 100
                elapsed = time.time() - start_time
                estimated_total = elapsed / (page / total_pages)
                remaining = estimated_total - elapsed
                
                print(f"진행률: {progress:.1f}% ({page}/{total_pages} 페이지)")
                print(f"경과 시간: {elapsed:.1f}초, 남은 예상 시간: {remaining:.1f}초")
                
            # 서버 부하 방지를 위한 대기 시간
            wait_time = random.uniform(1, 3)  # 1~3초 사이 무작위 대기
            time.sleep(wait_time)
                
        except requests.exceptions.RequestException as e:
            print(f"페이지 {page} 요청 중 오류 발생: {e}")
            time.sleep(10)  # 네트워크 오류 시 10초 대기 후 계속 진행
            continue
        except Exception as e:
            print(f"페이지 {page} 처리 중 오류 발생: {e}")
            time.sleep(5)  # 오류 발생 시 5초 대기 후 계속 진행
            continue
    
    return all_reviews

# 리뷰 데이터 처리 및 저장
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
        max_pages = 10
    
    # 결과 형식 선택
    output_format = input("결과 형식을 선택하세요 (1: 엑셀, 2: JSON, 기본값: 1): ").strip() or "1"
    
    print(f"\n{product_id} 상품의 리뷰를 최대 {max_pages}페이지까지 가져옵니다...\n")
    
    try:
        # 리뷰 데이터 수집
        reviews = get_reviews(product_id, max_pages)
        
        if not reviews:
            print("수집된 리뷰가 없습니다. 프로그램을 종료합니다.")
            sys.exit(1)
        
        print(f"총 {len(reviews)}개의 리뷰를 수집했습니다. 데이터 처리 중...")
        
        # 현재 날짜와 시간을 파일명에 포함
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON 형식으로 원본 데이터 저장
        json_filename = f'올리브영_리뷰_원본_{product_id}_{date_str}.json'
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(reviews, f, ensure_ascii=False, indent=2)
        print(f"원본 리뷰 데이터를 '{json_filename}' 파일로 저장했습니다.")
        
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
