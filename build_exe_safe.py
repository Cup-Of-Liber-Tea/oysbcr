import subprocess
import sys
import os
import shutil

def install_pyinstaller():
    """PyInstaller 설치"""
    try:
        import PyInstaller
        print("PyInstaller가 이미 설치되어 있습니다.")
    except ImportError:
        print("PyInstaller를 설치합니다...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
        print("PyInstaller 설치 완료!")

def prepare_seleniumbase():
    """셀레니움베이스 드라이버 준비"""
    print("셀레니움베이스 드라이버를 준비합니다...")
    try:
        # 셀레니움베이스 설치 확인
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'seleniumbase'])
        
        # 크롬 드라이버 설치
        subprocess.check_call([sys.executable, '-m', 'seleniumbase', 'install', 'chrome'])
        print("셀레니움베이스 드라이버 준비 완료!")
        return True
    except Exception as e:
        print(f"셀레니움베이스 준비 중 오류: {e}")
        return False

def create_hook_files():
    """PyInstaller 훅 파일 생성"""
    hooks_dir = "hooks"
    if not os.path.exists(hooks_dir):
        os.makedirs(hooks_dir)
    
    # 셀레니움베이스 훅 파일
    hook_content = '''
from PyInstaller.utils.hooks import collect_all, collect_data_files

# 셀레니움베이스 모든 데이터 수집
datas, binaries, hiddenimports = collect_all('seleniumbase')

# 추가 데이터 파일들
datas += collect_data_files('seleniumbase')

# 추가 숨겨진 import들
hiddenimports += [
    'seleniumbase.core.browser_launcher',
    'seleniumbase.fixtures.base_case',
    'seleniumbase.core.sb',
    'seleniumbase.drivers',
    'seleniumbase.utilities',
    'selenium.webdriver.chrome.options',
    'selenium.webdriver.chrome.service',
    'selenium.webdriver.common.desired_capabilities',
]
'''
    
    with open(os.path.join(hooks_dir, 'hook-seleniumbase.py'), 'w', encoding='utf-8') as f:
        f.write(hook_content)
    
    print("PyInstaller 훅 파일 생성 완료!")
    return hooks_dir

def build_exe_ultra_safe():
    """초안전 exe 파일 빌드"""
    print("초안전 exe 파일 빌드를 시작합니다...")
    
    # 훅 파일 생성
    hooks_dir = create_hook_files()
    
    # PyInstaller 명령어 구성
    cmd = [
        'pyinstaller',
        '--onedir',  # 폴더 형태로 생성
        '--windowed',  # 콘솔 창 숨김
        '--name=올리브영_리뷰_수집기_안전버전',  # exe 파일명
        f'--additional-hooks-dir={hooks_dir}',  # 커스텀 훅 사용
        
        # 기본 라이브러리들
        '--hidden-import=seleniumbase',
        '--hidden-import=seleniumbase.core',
        '--hidden-import=seleniumbase.core.browser_launcher',
        '--hidden-import=seleniumbase.fixtures',
        '--hidden-import=seleniumbase.fixtures.base_case',
        '--hidden-import=seleniumbase.core.sb',
        '--hidden-import=seleniumbase.drivers',
        '--hidden-import=seleniumbase.utilities',
        '--hidden-import=seleniumbase.utilities.selenium_ide',
        
        # 셀레니움 관련
        '--hidden-import=selenium',
        '--hidden-import=selenium.webdriver',
        '--hidden-import=selenium.webdriver.chrome',
        '--hidden-import=selenium.webdriver.chrome.options',
        '--hidden-import=selenium.webdriver.chrome.service',
        '--hidden-import=selenium.webdriver.common',
        '--hidden-import=selenium.webdriver.common.by',
        '--hidden-import=selenium.webdriver.common.keys',
        '--hidden-import=selenium.webdriver.common.desired_capabilities',
        '--hidden-import=selenium.webdriver.support',
        '--hidden-import=selenium.webdriver.support.ui',
        '--hidden-import=selenium.webdriver.support.wait',
        '--hidden-import=selenium.webdriver.support.expected_conditions',
        
        # 데이터 처리
        '--hidden-import=pandas',
        '--hidden-import=pandas.core',
        '--hidden-import=pandas.io',
        '--hidden-import=pandas.io.excel',
        '--hidden-import=openpyxl',
        '--hidden-import=openpyxl.workbook',
        '--hidden-import=openpyxl.worksheet',
        
        # 네트워크 관련
        '--hidden-import=requests',
        '--hidden-import=requests.adapters',
        '--hidden-import=requests.auth',
        '--hidden-import=urllib3',
        '--hidden-import=urllib3.util',
        '--hidden-import=urllib3.exceptions',
        '--hidden-import=urllib3.poolmanager',
        '--hidden-import=certifi',
        
        # GUI 관련
        '--hidden-import=tkinter',
        '--hidden-import=tkinter.ttk',
        '--hidden-import=tkinter.messagebox',
        '--hidden-import=tkinter.filedialog',
        
        # 기타 필수 모듈들
        '--hidden-import=json',
        '--hidden-import=datetime',
        '--hidden-import=time',
        '--hidden-import=random',
        '--hidden-import=traceback',
        '--hidden-import=threading',
        '--hidden-import=subprocess',
        '--hidden-import=os',
        '--hidden-import=sys',
        
        # 데이터 수집
        '--collect-all=seleniumbase',
        '--collect-all=selenium',
        '--collect-all=pandas',
        '--collect-all=openpyxl',
        '--collect-all=urllib3',
        '--collect-all=certifi',
        '--collect-all=requests',
        
        # 빌드 옵션
        '--noconfirm',  # 기존 빌드 덮어쓰기
        '--clean',  # 캐시 정리
        '--debug=imports',  # 디버그 정보 포함
        
        'olive_gui.py'
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("\n" + "="*60)
        print("초안전 exe 파일 빌드 완료!")
        print("생성된 폴더: dist/올리브영_리뷰_수집기_안전버전/")
        print("실행 파일: dist/올리브영_리뷰_수집기_안전버전/올리브영_리뷰_수집기_안전버전.exe")
        print("\n주의사항:")
        print("- 전체 폴더를 복사하여 사용하세요")
        print("- Chrome 브라우저가 설치되어 있어야 합니다")
        print("- 첫 실행 시 Windows Defender에서 허용해주세요")
        print("="*60)
        return True
    except subprocess.CalledProcessError as e:
        print(f"빌드 중 오류 발생: {e}")
        return False

def create_runtime_check():
    """런타임 체크 스크립트 생성"""
    check_script = '''
import sys
import os

def check_environment():
    """실행 환경 체크"""
    print("=== 실행 환경 체크 ===")
    
    # Python 버전
    print(f"Python 버전: {sys.version}")
    
    # 필수 모듈 체크
    modules_to_check = [
        'seleniumbase', 'selenium', 'pandas', 
        'openpyxl', 'requests', 'urllib3', 'tkinter'
    ]
    
    for module in modules_to_check:
        try:
            __import__(module)
            print(f"✓ {module}: OK")
        except ImportError as e:
            print(f"✗ {module}: 누락 - {e}")
    
    # Chrome 브라우저 체크
    chrome_paths = [
        r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        r"C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
    ]
    
    chrome_found = False
    for path in chrome_paths:
        if os.path.exists(path):
            print(f"✓ Chrome 브라우저: {path}")
            chrome_found = True
            break
    
    if not chrome_found:
        print("✗ Chrome 브라우저: 설치되지 않음")
    
    print("===================")

if __name__ == "__main__":
    check_environment()
    input("Enter를 눌러 종료...")
'''
    
    with open('환경체크.py', 'w', encoding='utf-8') as f:
        f.write(check_script)
    
    print("환경체크.py 파일 생성 완료!")

def main():
    print("올리브영 리뷰 수집기 초안전 exe 빌드 도구")
    print("="*50)
    
    # PyInstaller 설치
    install_pyinstaller()
    
    # 셀레니움베이스 준비
    if not prepare_seleniumbase():
        print("셀레니움베이스 준비에 실패했습니다. 계속 진행합니다...")
    
    # 환경 체크 스크립트 생성
    create_runtime_check()
    
    # exe 빌드
    if build_exe_ultra_safe():
        print("\n빌드가 성공적으로 완료되었습니다!")
        print("\n다음 단계:")
        print("1. 환경체크.py를 실행하여 환경을 확인하세요")
        print("2. dist 폴더의 exe 파일을 테스트하세요")
        print("3. 문제가 있으면 환경체크 결과를 확인하세요")
    else:
        print("\n빌드에 실패했습니다.")
        print("환경체크.py를 실행하여 문제를 확인해보세요.")

if __name__ == "__main__":
    main() 