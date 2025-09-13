import sys
import os
import threading
import logging
import re
from urllib.parse import urlparse, parse_qs
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog, QFrame, QProgressBar, QMessageBox, QScrollArea
from PySide6.QtCore import Signal, QObject, Slot, Qt

from olive_scraper import ensure_chrome_debug, connect_driver, extract_session_from_driver, fetch_reviews, process_reviews, save_results, wait_for_page_load_and_handle_cloudflare

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# GUI 로깅을 위한 커스텀 핸들러
class StreamHandler(logging.Handler, QObject):
    log_signal = Signal(str)

    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        logging.Handler.__init__(self)

    def emit(self, record):
        msg = self.format(record)
        self.log_signal.emit(msg)

class OliveScraperGUI(QWidget):
    status_update_signal = Signal(str)
    progress_update_signal = Signal(int)
    message_box_signal = Signal(str, str, str) # type, title, message

    def __init__(self):
        super().__init__()
        self.input_fields = [] # 동적 입력 필드를 저장할 리스트
        self.init_ui()
        self.init_logging()
        self.is_running = False
        self.current_scraper_thread = None # 현재 실행 중인 스크래퍼 스레드

        self.status_update_signal.connect(self.status_label.setText)
        self.progress_update_signal.connect(self.progress_bar.setValue)
        self.message_box_signal.connect(self._show_message_box)

    def init_ui(self):
        self.setWindowTitle("올리브영 리뷰 수집기")
        self.setGeometry(100, 100, 800, 850) # 창 높이 증가

        main_layout = QVBoxLayout()

        title_label = QLabel("올리브영 리뷰 수집기1.3 - by 꼬질강쥐")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        input_frame = QFrame()
        input_frame.setFrameShape(QFrame.StyledPanel)
        input_layout = QVBoxLayout()
        input_frame.setLayout(input_layout)

        # 동적 입력 필드를 담을 스크롤 가능한 영역
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content_widget = QWidget()
        self.input_fields_layout = QVBoxLayout(scroll_content_widget)
        scroll_area.setWidget(scroll_content_widget)
        input_layout.addWidget(scroll_area)

        # 기본 입력 필드 하나 추가
        self._add_input_field_pair("A000000213959", 100)

        add_link_button = QPushButton("링크 추가")
        add_link_button.clicked.connect(lambda: self._add_input_field_pair())
        input_layout.addWidget(add_link_button)

        output_format_label = QLabel("출력 형식: 엑셀(.xlsx)과 JSON 파일 모두 저장됩니다")
        format_hbox = QHBoxLayout()
        format_hbox.addStretch(1)
        format_hbox.addWidget(output_format_label)
        input_layout.addLayout(format_hbox)

        output_dir_hbox = QHBoxLayout()
        output_dir_label = QLabel("저장할 폴더:")
        self.output_dir_input = QLineEdit(os.getcwd())
        output_dir_select_btn = QPushButton("찾아보기")
        output_dir_select_btn.clicked.connect(self._select_output_directory)
        output_dir_hbox.addWidget(output_dir_label)
        output_dir_hbox.addWidget(self.output_dir_input)
        output_dir_hbox.addWidget(output_dir_select_btn)
        input_layout.addLayout(output_dir_hbox)

        user_data_dir_hbox = QHBoxLayout()
        user_data_dir_label = QLabel("사용자프로필경로:")
        self.user_data_dir_input = QLineEdit(r"E:\brwProf\User Data")
        user_data_dir_select_btn = QPushButton("찾아보기")
        user_data_dir_select_btn.clicked.connect(self._select_user_data_dir)
        user_data_dir_hbox.addWidget(user_data_dir_label)
        user_data_dir_hbox.addWidget(self.user_data_dir_input)
        user_data_dir_hbox.addWidget(user_data_dir_select_btn)
        input_layout.addLayout(user_data_dir_hbox)

        main_layout.addWidget(input_frame)

        button_frame = QHBoxLayout()
        self.start_button = QPushButton("리뷰 수집 시작")
        self.start_button.clicked.connect(self.start_collection)
        button_frame.addStretch(1)
        button_frame.addWidget(self.start_button)
        button_frame.addStretch(1)
        
        main_layout.addLayout(button_frame)

        progress_frame = QFrame()
        progress_frame.setFrameShape(QFrame.StyledPanel)
        progress_layout = QVBoxLayout()
        progress_frame.setLayout(progress_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        progress_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("준비 완료")
        self.status_label.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(self.status_label)

        main_layout.addWidget(progress_frame)

        log_frame = QFrame()
        log_frame.setFrameShape(QFrame.StyledPanel)
        log_layout = QVBoxLayout()
        log_frame.setLayout(log_layout)
        
        log_layout.addWidget(QLabel("로그:"))
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        log_layout.addWidget(self.log_output)

        main_layout.addWidget(log_frame)

        bottom_button_frame = QHBoxLayout()
        self.stop_button = QPushButton("중지")
        self.stop_button.clicked.connect(self.stop_collection)
        self.stop_button.setEnabled(False)
        bottom_button_frame.addWidget(self.stop_button)
        
        self.open_folder_button = QPushButton("저장 폴더 열기")
        self.open_folder_button.clicked.connect(self.open_save_folder)
        bottom_button_frame.addWidget(self.open_folder_button)

        main_layout.addLayout(bottom_button_frame)

        self.setLayout(main_layout)

        self.log_output.append("올리브영 리뷰 수집기가 시작되었습니다.")
        self.log_output.append("상품 ID 또는 URL을 입력하고 '링크 추가' 버튼으로 여러 링크를 추가하여 수집할 수 있습니다.")

    def _create_input_field(self, layout, label_text, default_value=""):
        hbox = QHBoxLayout()
        label = QLabel(label_text)
        line_edit = QLineEdit(default_value)
        hbox.addWidget(label)
        hbox.addWidget(line_edit)
        # layout.addLayout(hbox) # 직접 추가하지 않고, 외부에서 hbox를 사용하여 위젯 배치
        return line_edit, hbox # hbox도 반환하여 나중에 레이아웃에서 제거할 수 있도록 함

    def _add_input_field_pair(self, default_product_id="", default_max_pages=100):
        pair_widget = QWidget()
        pair_layout = QVBoxLayout(pair_widget) # QVBoxLayout로 변경

        # 상품 ID/URL 입력 필드
        product_id_input, product_id_hbox = self._create_input_field(None, "상품 ID/URL:", default_product_id)
        pair_layout.addLayout(product_id_hbox)

        # 최대 페이지 수 입력 필드 및 삭제 버튼
        max_pages_input, max_pages_hbox = self._create_input_field(None, "최대 페이지 수(페이지 1당 리뷰 10개):")
        max_pages_input.setText(str(default_max_pages))

        delete_button = QPushButton("삭제")
        delete_button.clicked.connect(lambda: self._remove_input_field_pair(pair_widget))
        max_pages_hbox.addWidget(delete_button) # 삭제 버튼을 최대 페이지 수 입력 필드와 같은 줄에 추가
        pair_layout.addLayout(max_pages_hbox)

        self.input_fields_layout.addWidget(pair_widget)

        # 구분선 추가
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        self.input_fields_layout.addWidget(separator)

        self.input_fields.append({
            'widget': pair_widget,
            'separator': separator, # 구분선 위젯 추가
            'product_id_input': product_id_input,
            'max_pages_input': max_pages_input
        })

    def _remove_input_field_pair(self, widget_to_remove):
        for i, field_data in enumerate(self.input_fields):
            if field_data['widget'] == widget_to_remove:
                # 위젯 제거
                widget_to_remove.deleteLater()
                # 구분선 제거
                field_data['separator'].deleteLater()
                # 리스트에서 제거
                del self.input_fields[i]
                break

    def _select_output_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "추출데이터 저장 경로 선택", self.output_dir_input.text())
        if dir_path:
            self.output_dir_input.setText(dir_path)

    def _select_user_data_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "사용자 프로필 경로 선택", self.user_data_dir_input.text())
        if dir_path:
            self.user_data_dir_input.setText(dir_path)

    def init_logging(self):
        self.log_handler = StreamHandler()
        self.log_handler.log_signal.connect(self.update_log_output)
        logging.getLogger().addHandler(self.log_handler)

    @Slot(str)
    def update_log_output(self, msg):
        self.log_output.append(msg)
        self.log_output.verticalScrollBar().setValue(self.log_output.verticalScrollBar().maximum())

    @Slot(str, str, str)
    def _show_message_box(self, type: str, title: str, message: str):
        if type == "warning":
            QMessageBox.warning(self, title, message)
        elif type == "critical":
            QMessageBox.critical(self, title, message)
        elif type == "information":
            QMessageBox.information(self, title, message)

    def start_collection(self):
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.log_output.clear()
        self.log_output.append("리뷰 수집을 시작합니다...")
        self.status_update_signal.emit("수집 준비 중...")
        self.progress_update_signal.emit(0)

        # 모든 입력 필드에서 상품 정보 가져오기
        products_to_scrape = []
        for field_data in self.input_fields:
            input_value = field_data['product_id_input'].text().strip()
            max_pages_str = field_data['max_pages_input'].text().strip()

            if not input_value:
                self.message_box_signal.emit("warning", "입력 오류", "상품 ID 또는 URL을 입력해주세요.")
                self._reset_gui_state()
                return

            product_id = self.extract_product_id(input_value)
            if not product_id:
                self.message_box_signal.emit("warning", "입력 오류", f"유효한 상품 ID 또는 올리브영 URL이 아닙니다: {input_value}")
                self._reset_gui_state()
                return
            
            try:
                max_pages = int(max_pages_str)
                if max_pages <= 0:
                    raise ValueError("페이지 수는 1 이상이어야 합니다.")
            except ValueError as e:
                self.message_box_signal.emit("warning", "입력 오류", f"최대 페이지 수 입력이 잘못되었습니다. {e}")
                self.update_log_output(f"오류: 최대 페이지 수 입력이 잘못되었습니다. {e}")
                self._reset_gui_state()
                return
            products_to_scrape.append({'product_id': product_id, 'max_pages': max_pages})

        if not products_to_scrape:
            self.message_box_signal.emit("warning", "입력 오류", "최소 하나 이상의 상품을 추가해주세요.")
            self._reset_gui_state()
            return

        out_dir = self.output_dir_input.text()
        if not os.path.exists(out_dir):
            try:
                os.makedirs(out_dir)
            except OSError as e:
                self.message_box_signal.emit("critical", "오류", f"출력 디렉토리를 생성할 수 없습니다: {e}")
                self.update_log_output(f"오류: 출력 디렉토리를 생성할 수 없습니다: {e}")
                self._reset_gui_state()
                return
        
        user_data_dir = self.user_data_dir_input.text()
        chrome_main_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe" # 고정된 값
        port = 9222 # 고정된 값

        self.is_running = True
        self.current_scraper_thread = threading.Thread(target=self._run_scraper_thread, args=(
            products_to_scrape, out_dir, user_data_dir, chrome_main_path, port
        ))
        self.current_scraper_thread.start()

    def _run_scraper_thread(self, products_to_scrape, out_dir, user_data_dir, chrome_main_path, port):
        driver = None
        try:
            # 드라이버는 한 번만 연결
            self.status_update_signal.emit("Chrome 드라이버 연결 중...")
            ensure_chrome_debug(port, user_data_dir) # 브라우저 실행 확인
            driver = connect_driver(port, chrome_main_path=chrome_main_path, user_data_dir=user_data_dir)
            self.update_log_output("Chrome 드라이버 연결 완료.")

            for i, product_data in enumerate(products_to_scrape):
                if not self.is_running:
                    self.update_log_output(f"전체 수집이 중지되었습니다.")
                    break

                product_id = product_data['product_id']
                max_pages = product_data['max_pages']
                self.update_log_output(f"\n--- 상품 {i+1}/{len(products_to_scrape)} 수집 시작: 상품 ID={product_id}, 최대 페이지={max_pages} ---")
                self.status_update_signal.emit(f"상품 {i+1}/{len(products_to_scrape)} ({product_id}) 수집 중...")
                self.progress_update_signal.emit(0)

                # 페이지 로드 및 Cloudflare 처리 (driver 객체 재사용)
                if not wait_for_page_load_and_handle_cloudflare(driver, product_id, timeout=60, log_callback=self.update_log_output, stop_check_callback=lambda: not self.is_running):
                    self.update_log_output("Cloudflare 또는 페이지 로드 문제로 인증 정보 획득 실패. 다음 상품으로 넘어갑니다.")
                    continue # 다음 상품으로 이동
                
                if not self.is_running:
                    self.update_log_output(f"사용자에 의해 수집이 중지되었습니다. 다음 상품으로 넘어갑니다.")
                    continue # 다음 상품으로 이동

                session, user_agent = extract_session_from_driver(driver)
                reviews = fetch_reviews(session, user_agent, product_id, max_pages, log_callback=self.update_log_output, stop_check_callback=lambda: not self.is_running)
                
                if not self.is_running:
                    self.update_log_output(f"사용자에 의해 수집이 중지되었습니다. 결과 저장을 건너뜁니다.")
                    continue # 다음 상품으로 이동

                if not reviews:
                    self.update_log_output(f"상품 ID {product_id}에 대해 수집된 리뷰가 없습니다.")
                    continue # 다음 상품으로 이동
                
                df = process_reviews(reviews)
                save_results(product_id, reviews, df, out_dir, log_callback=self.update_log_output)
                self.update_log_output(f"--- 상품 {i+1}/{len(products_to_scrape)} 수집 완료: 상품 ID={product_id} ---")

            if self.is_running: # 모든 상품 수집이 정상적으로 완료되었을 때만 최종 메시지
                self.update_log_output("모든 리뷰 수집이 완료되었습니다.")
                self.status_update_signal.emit("완료")
                self.progress_update_signal.emit(100)
                self.message_box_signal.emit("information", "수집 완료", "모든 리뷰 수집이 완료되었습니다.")
            else:
                self.update_log_output("사용자에 의해 모든 수집이 중지되었습니다.")

        except Exception as e:
            self.update_log_output(f"스크래핑 중 오류 발생: {e}")
            self.status_update_signal.emit("오류 발생")
            self.message_box_signal.emit("critical", "오류", f"리뷰 수집 중 오류가 발생했습니다:\n{e}")
        finally:
            if driver:
                try:
                    driver.quit() # 모든 작업 완료 후 드라이버 명시적 종료
                    self.update_log_output("Chrome 드라이버를 종료했습니다.")
                except Exception as e:
                    self.update_log_output(f"Chrome 드라이버 종료 중 오류 발생: {e}")
                    logging.error(f"Chrome 드라이버 종료 중 오류 발생: {e}", exc_info=True)
            self._reset_gui_state() # GUI 상태 초기화

    def stop_collection(self):
        self.is_running = False
        if self.current_scraper_thread and self.current_scraper_thread.is_alive():
            self.update_log_output("현재 진행 중인 스크래핑 작업을 중지 요청했습니다. 잠시 기다려주세요...")
            # 스레드는 is_running 플래그를 확인하여 스스로 종료될 것임
        else:
            self.update_log_output("리뷰 수집이 중지되었습니다.")
            self._reset_gui_state()

    def _reset_gui_state(self):
        # 메인 스레드에서 GUI 상태를 안전하게 초기화
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.is_running = False
        self.status_update_signal.emit("준비 완료")
        self.progress_update_signal.emit(0)

    def open_save_folder(self):
        path = self.output_dir_input.text()
        if os.path.exists(path):
            try:
                import subprocess # subprocess 임포트
                if sys.platform == 'win32':
                    os.startfile(path)
                elif sys.platform == 'darwin':  # macOS
                    subprocess.Popen(['open', path])
                else:  # Linux
                    subprocess.Popen(['xdg-open', path])
            except Exception as e:
                self.message_box_signal.emit("critical", "오류", f"저장 폴더를 열 수 없습니다: {e}")
                self.update_log_output(f"오류: 저장 폴더를 열 수 없습니다: {e}")
        else:
            self.message_box_signal.emit("warning", "경로 오류", "지정된 저장 경로가 존재하지 않습니다.")
            self.update_log_output("오류: 지정된 저장 경로가 존재하지 않습니다.")

    def extract_product_id(self, input_string: str) -> str | None:
        # URL 형식 확인
        if input_string.startswith("http://") or input_string.startswith("https://"):
            parsed_url = urlparse(input_string)
            query_params = parse_qs(parsed_url.query)
            goods_no = query_params.get('goodsNo', [None])[0]
            if goods_no:
                return goods_no
            else:
                self.update_log_output(f"경고: URL에서 'goodsNo' 파라미터를 찾을 수 없습니다: {input_string}")
                return None
        else:
            if re.fullmatch(r"A[0-9]{12}", input_string):
                return input_string
            else:
                self.update_log_output(f"경고: 유효한 상품 ID 형식이 아닙니다: {input_string}")
                return None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet("QWidget { font-size: 12pt; }")
    gui = OliveScraperGUI()
    gui.show()
    sys.exit(app.exec()) 