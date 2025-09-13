import sys
import os
import threading
import logging
import re
from urllib.parse import urlparse, parse_qs
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog, QFrame, QProgressBar, QMessageBox
from PySide6.QtCore import Signal, QObject, Slot, Qt

from olive_scraper import scrape_reviews

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class StreamHandler(logging.Handler, QObject):
    log_signal = Signal(str)

    def __init__(self):
        super().__init__()
        QObject.__init__(self)

    def emit(self, record):
        msg = self.format(record)
        self.log_signal.emit(msg)

class OliveScraperGUI(QWidget):
    status_update_signal = Signal(str)
    progress_update_signal = Signal(int)
    message_box_signal = Signal(str, str, str) # type, title, message

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.init_logging()
        self.is_running = False

        self.status_update_signal.connect(self.status_label.setText)
        self.progress_update_signal.connect(self.progress_bar.setValue)
        self.message_box_signal.connect(self._show_message_box)

    def init_ui(self):
        self.setWindowTitle("올리브영 리뷰 수집기")
        self.setGeometry(100, 100, 800, 700)

        main_layout = QVBoxLayout()

        title_label = QLabel("올리브영 리뷰 수집기1.3 - by 꼬질강쥐")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        input_frame = QFrame()
        input_frame.setFrameShape(QFrame.StyledPanel)
        input_layout = QVBoxLayout()
        input_frame.setLayout(input_layout)
        
        self.product_id_input = self._create_input_field(input_layout, "상품 ID 또는 URL전체 복붙:")
        self.product_id_input.setText("A000000213959")
        
        product_id_hint = QLabel("예: A000000159233 또는 상품페이지 URL")
        # product_id_hint.setStyleSheet("font-size: 9pt;")
        hint_hbox = QHBoxLayout()
        hint_hbox.addStretch(1)
        hint_hbox.addWidget(product_id_hint)
        input_layout.addLayout(hint_hbox)

        self.max_pages_input = self._create_input_field(input_layout, "최대 페이지 수(페이지 1당 리뷰 10개, Max 100):")
        self.max_pages_input.setText("100")
        
        output_format_label = QLabel("출력 형식: 엑셀(.xlsx)과 JSON 파일 모두 저장됩니다")
        # output_format_label.setStyleSheet("font-size: 12pt;")
        format_hbox = QHBoxLayout()
        format_hbox.addStretch(1)
        format_hbox.addWidget(output_format_label)
        input_layout.addLayout(format_hbox)

        output_dir_hbox = QHBoxLayout()
        output_dir_label = QLabel("추출데이터 저장 경로:")
        self.output_dir_input = QLineEdit(os.getcwd())
        output_dir_select_btn = QPushButton("찾아보기")
        output_dir_select_btn.clicked.connect(self._select_output_directory)
        output_dir_hbox.addWidget(output_dir_label)
        output_dir_hbox.addWidget(self.output_dir_input)
        output_dir_hbox.addWidget(output_dir_select_btn)
        input_layout.addLayout(output_dir_hbox)

        # Chrome 사용자 데이터 디렉토리 입력은 유지
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
        self.log_output.append("상품 ID 또는 URL을 입력하고 '리뷰 수집 시작' 버튼을 클릭하세요.")

    def _create_input_field(self, layout, label_text):
        hbox = QHBoxLayout()
        label = QLabel(label_text)
        line_edit = QLineEdit()
        hbox.addWidget(label)
        hbox.addWidget(line_edit)
        layout.addLayout(hbox)
        return line_edit

    def _select_output_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "출력 디렉토리 선택", self.output_dir_input.text())
        if dir_path:
            self.output_dir_input.setText(dir_path)

    def _select_user_data_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Chrome 사용자 데이터 디렉토리 선택", self.user_data_dir_input.text())
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

        input_value = self.product_id_input.text().strip()
        if not input_value:
            self.message_box_signal.emit("warning", "입력 오류", "상품 ID 또는 URL을 입력해주세요.")
            self.update_log_output("오류: 상품 ID 또는 URL을 입력해주세요.")
            self.status_update_signal.emit("오류 발생")
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            return

        product_id = self.extract_product_id(input_value)
        if not product_id:
            self.message_box_signal.emit("warning", "입력 오류", "유효한 상품 ID 또는 올리브영 URL을 입력해주세요.")
            self.update_log_output("오류: 유효한 상품 ID 또는 올리브영 URL을 입력해주세요.")
            self.status_update_signal.emit("오류 발생")
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            return
        
        max_pages_str = self.max_pages_input.text()
        try:
            max_pages = int(max_pages_str)
            if max_pages <= 0:
                raise ValueError("페이지 수는 1 이상이어야 합니다.")
        except ValueError as e:
            self.message_box_signal.emit("warning", "입력 오류", f"최대 페이지 수 입력이 잘못되었습니다. {e}")
            self.update_log_output(f"오류: 최대 페이지 수 입력이 잘못되었습니다. {e}")
            self.status_update_signal.emit("오류 발생")
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            return

        out_dir = self.output_dir_input.text()
        if not os.path.exists(out_dir):
            try:
                os.makedirs(out_dir)
            except OSError as e:
                self.message_box_signal.emit("critical", "오류", f"출력 디렉토리를 생성할 수 없습니다: {e}")
                self.update_log_output(f"오류: 출력 디렉토리를 생성할 수 없습니다: {e}")
                self.status_update_signal.emit("오류 발생")
                self.start_button.setEnabled(True)
                self.stop_button.setEnabled(False)
                return
        
        user_data_dir = self.user_data_dir_input.text()
        chrome_main_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe" # 고정된 값
        port = "9222" # 고정된 값

        self.is_running = True
        threading.Thread(target=self._run_scraper_thread, args=(
            product_id, max_pages, out_dir, user_data_dir, chrome_main_path, port
        )).start()

    def _run_scraper_thread(self, product_id, max_pages, out_dir, user_data_dir, chrome_main_path, port):
        try:
            scrape_reviews(
                product_id=product_id,
                max_pages=max_pages,
                out_dir=out_dir,
                port=int(port), # port를 int로 변환하여 전달
                user_data_dir=user_data_dir,
                chrome_main_path=chrome_main_path,
                log_callback=self.update_log_output,
                stop_check_callback=lambda: not self.is_running
            )
            if self.is_running:
                self.update_log_output("리뷰 수집이 완료되었습니다.")
                self.status_update_signal.emit("완료")
                self.progress_update_signal.emit(100)
                self.message_box_signal.emit("information", "수집 완료", "리뷰 수집이 완료되었습니다.")
        except Exception as e:
            self.update_log_output(f"오류 발생: {e}")
            self.status_update_signal.emit("오류 발생")
            self.message_box_signal.emit("critical", "오류", f"리뷰 수집 중 오류가 발생했습니다:\n{e}")
        finally:
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.is_running = False

    def stop_collection(self):
        self.is_running = False
        self.update_log_output("리뷰 수집이 중지되었습니다.")
        self.status_update_signal.emit("중지됨")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def open_save_folder(self):
        path = self.output_dir_input.text()
        if os.path.exists(path):
            try:
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
                # URL은 맞지만 goodsNo 파라미터가 없는 경우
                self.update_log_output(f"경고: URL에서 'goodsNo' 파라미터를 찾을 수 없습니다: {input_string}")
                return None
        else:
            # URL 형식이 아니면 상품 ID로 간주 (A로 시작하는 13자리 영숫자)
            if re.fullmatch(r"A[0-9]{12}", input_string):
                return input_string
            else:
                self.update_log_output(f"경고: 유효한 상품 ID 형식이 아닙니다: {input_string}")
                return None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet("QWidget { font-size: 10pt; }") # 모든 위젯의 기본 폰트 크기를 14pt로 설정
    gui = OliveScraperGUI()
    gui.show()
    sys.exit(app.exec()) 