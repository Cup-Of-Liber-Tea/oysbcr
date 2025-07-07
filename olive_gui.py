import sys
import subprocess
import os
import time
import json
import random
import requests
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import traceback
from seleniumbase import SB
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class OliveYoungReviewGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("올리브영 리뷰 수집기")
        self.root.geometry("600x700")
        self.root.resizable(True, True)
        
        # 필요한 패키지 설치 확인
        self.check_packages()
        
        # UI 구성
        self.create_widgets()
    
    def check_packages(self):
        try:
            import pandas as pd
            from seleniumbase import SB
            import requests
        except ImportError:
            if messagebox.askyesno("패키지 설치", "필요한 패키지(pandas, openpyxl, seleniumbase, requests)를 설치해야 합니다. 지금 설치하시겠습니까?"):
                self.install_packages()
    
    def install_packages(self):
        def run_install():
            try:
                packages = ['pandas', 'openpyxl', 'seleniumbase', 'requests']
                for package in packages:
                    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                messagebox.showinfo("설치 완료", "필요한 패키지 설치가 완료되었습니다.")
            except Exception as e:
                messagebox.showerror("설치 오류", f"패키지 설치 중 오류가 발생했습니다:\n{str(e)}")
        
        # 별도 스레드에서 설치 실행
        install_thread = threading.Thread(target=run_install)
        install_thread.daemon = True
        install_thread.start()
    
    def create_widgets(self):
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 제목
        title_label = ttk.Label(main_frame, text="올리브영 리뷰 수집기 - by 꼬질강쥐", font=("Malgun Gothic", 16, "bold"))
        title_label.pack(pady=10)
        
        # 입력 영역 프레임
        input_frame = ttk.LabelFrame(main_frame, text="설정", padding="10")
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 상품 ID 입력
        ttk.Label(input_frame, text="상품 ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.product_id_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.product_id_var, width=30).grid(row=0, column=1, sticky=tk.W, pady=5)
        ttk.Label(input_frame, text="예: A000000159233").grid(row=0, column=2, sticky=tk.W, pady=5, padx=5)
        
        # 최대 페이지 수 입력
        ttk.Label(input_frame, text="최대 페이지 수:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.max_pages_var = tk.IntVar(value=100)
        pages_spin = ttk.Spinbox(input_frame, from_=1, to=1000, textvariable=self.max_pages_var, width=10)
        pages_spin.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # 출력 형식 선택
        ttk.Label(input_frame, text="출력 형식:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.output_format_var = tk.StringVar(value="1")
        excel_radio = ttk.Radiobutton(input_frame, text="엑셀(.xlsx)", variable=self.output_format_var, value="1")
        json_radio = ttk.Radiobutton(input_frame, text="JSON", variable=self.output_format_var, value="2")
        excel_radio.grid(row=2, column=1, sticky=tk.W, pady=5)
        json_radio.grid(row=2, column=2, sticky=tk.W, pady=5)
        
        # 저장 경로 선택
        ttk.Label(input_frame, text="저장 경로:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.save_path_var = tk.StringVar(value=os.getcwd())
        path_entry = ttk.Entry(input_frame, textvariable=self.save_path_var, width=30)
        path_entry.grid(row=3, column=1, sticky=tk.W, pady=5)
        ttk.Button(input_frame, text="찾아보기", command=self.browse_save_path).grid(row=3, column=2, sticky=tk.W, pady=5, padx=5)
        
        # 버튼 영역
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=10)
        
        # 실행 버튼
        self.start_button = ttk.Button(button_frame, text="리뷰 수집 시작", command=self.start_collection)
        self.start_button.pack(side=tk.RIGHT, padx=5)
        
        # 진행 상황 표시
        progress_frame = ttk.LabelFrame(main_frame, text="진행 상황", padding="10")
        progress_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, padx=5, pady=5)
        
        self.status_var = tk.StringVar(value="준비 완료")
        status_label = ttk.Label(progress_frame, textvariable=self.status_var)
        status_label.pack(fill=tk.X, padx=5)
        
        # 로그 출력 영역
        log_frame = ttk.LabelFrame(main_frame, text="로그", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, height=15)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # 하단 버튼 영역
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, padx=5, pady=10)
        
        self.stop_button = ttk.Button(bottom_frame, text="중지", command=self.stop_collection, state=tk.DISABLED)
        self.stop_button.pack(side=tk.RIGHT, padx=5)
        
        self.open_folder_button = ttk.Button(bottom_frame, text="저장 폴더 열기", command=self.open_save_folder)
        self.open_folder_button.pack(side=tk.LEFT, padx=5)
        
        # 초기 메시지
        self.log("올리브영 리뷰 수집기가 시작되었습니다.")
        self.log("상품 ID를 입력하고 '리뷰 수집 시작' 버튼을 클릭하세요.")
    
    def browse_save_path(self):
        folder_path = filedialog.askdirectory(initialdir=self.save_path_var.get())
        if folder_path:
            self.save_path_var.set(folder_path)
    
    def open_save_folder(self):
        path = self.save_path_var.get()
        if os.path.exists(path):
            if sys.platform == 'win32':
                os.startfile(path)
            elif sys.platform == 'darwin':  # macOS
                subprocess.Popen(['open', path])
            else:  # Linux
                subprocess.Popen(['xdg-open', path])
        else:
            messagebox.showerror("오류", "지정된 경로가 존재하지 않습니다.")
    
    def log(self, message):
        self.log_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n")
        self.log_text.see(tk.END)
    
    def start_collection(self):
        # 입력 검증
        product_id = self.product_id_var.get().strip()
        if not product_id:
            messagebox.showerror("입력 오류", "상품 ID를 입력해주세요.")
            return
        
        save_path = self.save_path_var.get()
        if not os.path.exists(save_path):
            messagebox.showerror("경로 오류", "지정된 저장 경로가 존재하지 않습니다.")
            return
        
        # 버튼 상태 변경
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # 수집 시작 메시지
        self.log(f"상품 ID '{product_id}'의 리뷰 수집을 시작합니다.")
        self.log(f"최대 {self.max_pages_var.get()}페이지까지 수집합니다.")
        
        # 수집 스레드 시작
        self.is_running = True
        self.collection_thread = threading.Thread(target=self.run_collection)
        self.collection_thread.daemon = True
        self.collection_thread.start()
    
    def stop_collection(self):
        self.is_running = False
        self.log("리뷰 수집이 중지되었습니다.")
        self.status_var.set("중지됨")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
    
    def run_collection(self):
        try:
            # 설정값 가져오기
            product_id = self.product_id_var.get().strip()
            max_pages = self.max_pages_var.get()
            output_format = self.output_format_var.get()
            save_path = self.save_path_var.get()
            
            # 원래 작업 디렉토리 저장
            original_dir = os.getcwd()
            
            # 저장 경로로 이동
            os.chdir(save_path)
            
            # 리뷰 수집 시작
            self.status_var.set("리뷰 데이터 수집 중...")
            reviews = self.get_reviews(product_id, max_pages)
            
            if not self.is_running:
                os.chdir(original_dir)
                return
            
            if not reviews:
                self.log("수집된 리뷰가 없습니다.")
                messagebox.showinfo("알림", "수집된 리뷰가 없습니다.")
                self.status_var.set("완료 (수집된 리뷰 없음)")
                self.start_button.config(state=tk.NORMAL)
                self.stop_button.config(state=tk.DISABLED)
                os.chdir(original_dir)
                return
            
            self.log(f"총 {len(reviews)}개의 리뷰를 수집했습니다. 데이터 처리 중...")
            
            # 현재 날짜와 시간을 파일명에 포함
            date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # JSON 형식으로 원본 데이터 저장
            self.status_var.set("원본 데이터 저장 중...")
            json_filename = f'올리브영_리뷰_원본_{product_id}_{date_str}.json'
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(reviews, f, ensure_ascii=False, indent=2)
            self.log(f"원본 리뷰 데이터를 '{json_filename}' 파일로 저장했습니다.")
            
            if not self.is_running:
                os.chdir(original_dir)
                return
            
            # 리뷰 데이터 처리
            self.status_var.set("리뷰 데이터 처리 중...")
            df = self.process_reviews(reviews)
            
            if df.empty:
                self.log("처리된 리뷰 데이터가 없습니다.")
                messagebox.showinfo("알림", "처리된 리뷰 데이터가 없습니다.")
                self.status_var.set("완료 (처리된 데이터 없음)")
                self.start_button.config(state=tk.NORMAL)
                self.stop_button.config(state=tk.DISABLED)
                os.chdir(original_dir)
                return
            
            if not self.is_running:
                os.chdir(original_dir)
                return
            
            # 결과 저장
            self.status_var.set("결과 저장 중...")
            if output_format == "1":  # 엑셀 형식
                output_filename = f'올리브영_리뷰_{product_id}_{date_str}.xlsx'
                df.to_excel(output_filename, index=False, engine='openpyxl')
                self.log(f"총 {len(df)}개의 리뷰를 '{output_filename}' 파일로 저장했습니다.")
                self.log(f"파일 위치: {os.path.abspath(output_filename)}")
            else:  # JSON 형식
                output_filename = f'올리브영_리뷰_가공_{product_id}_{date_str}.json'
                df.to_json(output_filename, force_ascii=False, orient='records', indent=2)
                self.log(f"총 {len(df)}개의 리뷰를 '{output_filename}' 파일로 저장했습니다.")
                self.log(f"파일 위치: {os.path.abspath(output_filename)}")
            
            # 완료 처리
            self.progress_var.set(100)
            self.status_var.set(f"완료 ({len(df)}개 리뷰 저장)")
            messagebox.showinfo("완료", f"총 {len(df)}개의 리뷰 수집이 완료되었습니다.")
            
            # 원래 디렉토리로 돌아감
            os.chdir(original_dir)
            
        except Exception as e:
            self.log(f"오류 발생: {str(e)}")
            self.status_var.set("오류 발생")
            messagebox.showerror("오류", f"리뷰 수집 중 오류가 발생했습니다:\n{str(e)}")
        finally:
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
    
    # 임의의 User-Agent 생성 함수 (더 이상 사용되지 않음)
    def get_random_user_agent(self):
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0'
        ]
        return random.choice(user_agents)
    
    # 셀레니움을 사용하여 최신 쿠키와 헤더 가져오기
    def get_reviews(self, product_id, total_pages=100):
        all_reviews = []
        
        # 세션 생성 - 쿠키 유지
        session = requests.Session()
        
        # 직접 Selenium을 사용하여 최신 쿠키와 헤더 가져오기
        self.log("Selenium을 사용하여 최신 인증 정보 획득 중...")
        try:
            with SB(uc=True, headless=False) as sb:
                # 상품 페이지로 이동하여 쿠키 획득
                product_url = f'https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo={product_id}'
                sb.open(product_url)
                
                self.log("캡차(CAPTCHA)가 나타나면 5분 안에 해결해주세요...")
                # 페이지가 완전히 로드될 때까지 대기
                try:
                    sb.wait_for_element_visible("body", timeout=300)
                    self.log("페이지 로드 완료.")
                except:
                    self.log("페이지 로드 대기 중...")
                sb.sleep(2)  # 안정성을 위한 대기

                # 쿠키와 헤더 정보 추출
                cookies = sb.get_cookies()
                cookie_dict = {c['name']: c['value'] for c in cookies}
                
                user_agent = sb.get_user_agent()
                
                # 쿠키를 세션에 적용
                for cookie in cookies:
                    session.cookies.set(cookie['name'], cookie['value'])
                
                self.log("인증 정보 획득 완료. 브라우저를 닫고 리뷰 수집을 시작합니다.")
                
        except Exception as e:
            self.log(f"Selenium 인증 정보 획득 실패: {e}")
            traceback.print_exc()
            return []

        # 진행 상황 표시 변수
        progress_interval = max(1, total_pages // 20)  # 5% 간격으로 진행 상황 표시
        start_time = time.time()
        
        for page in range(1, total_pages + 1):
            # 수집 중지 확인
            if not self.is_running:
                self.log("사용자에 의해 수집이 중지되었습니다.")
                break
            
            # 헤더 설정 - 매 요청마다 약간 다르게 설정
            headers = {
                'User-Agent': user_agent,
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
            
            # 재시도 로직 강화
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    # API 호출 (SSL 검증 비활성화)
                    response = session.get(url, params=params, headers=headers, timeout=20, verify=False)
                    
                    # 응답이 성공적이면 반복문 종료
                    if response.status_code == 200:
                        break
                        
                    # 오류 발생 시 대기 시간 증가 및 재시도
                    retry_count += 1
                    time.sleep(random.uniform(3, 5))
                    
                except Exception as e:
                    self.log(f"페이지 {page} 요청 중 오류, 재시도 {retry_count+1}/{max_retries}: {e}")
                    retry_count += 1
                    time.sleep(5)
                    continue
            
            # 서버 부하 방지 대기 시간을 더 일관되게 설정
            time.sleep(2)  # 무작위가 아닌 고정 대기 시간
            
            # 응답 확인
            if response.status_code == 200:
                # 응답 타입 확인
                content_type = response.headers.get('Content-Type', '')
                if 'application/json' not in content_type and 'text/json' not in content_type and 'text/plain' not in content_type:
                    if '<html' in response.text.lower():
                        self.log(f"페이지 {page}의 응답이 HTML 형식입니다. API가 차단되었을 수 있습니다.")
                        if page <= 2:
                            self.log("=== 도움말 ===")
                            self.log("1. 올리브영 웹사이트에 직접 접속해 로그인을 시도해 보세요.")
                            self.log("2. 웹사이트에서 캡차(CAPTCHA) 인증이 필요할 수 있습니다.")
                            self.log("3. VPN이나 프록시를 사용 중이라면 해제해 보세요.")
                            self.log("4. 잠시 후에 다시 시도해 보세요.")
                            self.log("============")
                            
                            if page == 1:
                                self.log("첫 페이지 요청에 실패했습니다.")
                                return []
                        time.sleep(10)  # 10초 대기
                        continue
                
                try:
                    data = response.json()
                    
                    # 올리브영 API 응답 구조에 맞게 리뷰 데이터 추출
                    if 'gdasList' in data:
                        reviews_on_page = data['gdasList']
                        all_reviews.extend(reviews_on_page)
                        
                        # 현재 페이지 리뷰 정보 출력
                        self.log(f"페이지 {page}: {len(reviews_on_page)}개의 리뷰를 수집했습니다. (총 {len(all_reviews)}개)")
                        
                        # 각 리뷰 정보 간략히 출력
                        for idx, review in enumerate(reviews_on_page, 1):
                            if idx <= 3:  # 처음 3개만 표시
                                self.log(f"  - 리뷰 {idx}: {review.get('gdasScrVal')}점, {review.get('mbrNickNm')}, 작성일: {review.get('dispRegDate')}")
                        
                        # 진행률 업데이트
                        progress = (page / total_pages) * 100
                        self.root.after(0, lambda: self.progress_var.set(progress))
                        self.root.after(0, lambda: self.status_var.set(f"페이지 {page}/{total_pages} 수집 중..."))
                        
                        # 만약 현재 페이지에 리뷰가 없거나 예상보다 적으면, 마지막 페이지에 도달한 것
                        if len(reviews_on_page) == 0:
                            self.log(f"마지막 페이지 ({page})에 도달했습니다. 총 {len(all_reviews)}개의 리뷰를 수집했습니다.")
                            break
                    else:
                        self.log(f"페이지 {page}에서 리뷰 데이터를 찾을 수 없습니다.")
                        self.log(f"응답: {json.dumps(data, ensure_ascii=False, indent=2)[:200]}...")
                        # API 응답에 gdasList가 없으면 마지막 페이지로 간주
                        break
                except json.JSONDecodeError:
                    self.log(f"페이지 {page}의 응답을 JSON으로 파싱할 수 없습니다.")
                    self.log(f"응답 내용 일부: {response.text[:100]}")
                    
                    # HTML 응답인지 확인
                    if '<html' in response.text.lower():
                        self.log("응답이 HTML 형식입니다. API가 차단되었거나 로그인이 필요할 수 있습니다.")
                        # 첫 페이지에서 이런 일이 발생하면 종료
                        if page <= 3:
                            self.log("초기 페이지에서 오류가 발생했습니다.")
                            return []
                    
                    if page > 1:  # 첫 페이지가 아니면 API 오류로 간주하고 스킵
                        time.sleep(15)  # 15초 대기
                        continue
                    else:
                        self.log("API 응답 형식이 예상과 다릅니다.")
                        return []
            else:
                self.log(f"페이지 {page} 요청 실패: 상태 코드 {response.status_code}")
                
                try:
                    self.log(f"응답: {response.text[:200]}...")  # 응답의 처음 200자만 출력
                except:
                    self.log("응답 내용을 표시할 수 없습니다.")
                
                # 429 (Too Many Requests) 오류 시 더 오래 대기
                if response.status_code == 429:
                    wait_time = 60  # 60초 대기
                    self.log(f"너무 많은 요청을 보냈습니다. {wait_time}초 대기 후 다시 시도합니다.")
                    time.sleep(wait_time)
                    page -= 1  # 같은 페이지 다시 시도
                    continue
                
                # 403 (Forbidden) 오류 시 더 오래 대기하고 헤더 변경
                if response.status_code == 403:
                    wait_time = 120  # 120초 대기
                    self.log(f"접근이 거부되었습니다. {wait_time}초 대기 후 다시 시도합니다.")
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
                
                self.log(f"진행률: {progress:.1f}% ({page}/{total_pages} 페이지)")
                self.log(f"경과 시간: {elapsed:.1f}초, 남은 예상 시간: {remaining:.1f}초")
                
            # 서버 부하 방지를 위한 대기 시간
            time.sleep(random.uniform(1, 3))  # 1~3초 대기
                
        return all_reviews
    
    # 리뷰 데이터 처리 및 저장
    def process_reviews(self, reviews):
        import pandas as pd
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
                self.log(f"리뷰 처리 중 오류 발생: {e}")
                continue
        
        # DataFrame 생성
        df = pd.DataFrame(processed_data)
        
        # 데이터가 없는 경우 빈 DataFrame 반환
        if df.empty:
            self.log("처리할 리뷰 데이터가 없습니다.")
            return df
        
        return df

def main():
    root = tk.Tk()
    app = OliveYoungReviewGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 