import subprocess
import sys
import os

def install_pyinstaller():
    """PyInstaller 설치"""
    try:
        import PyInstaller
        print("PyInstaller가 이미 설치되어 있습니다.")
    except ImportError:
        print("PyInstaller를 설치합니다...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
        print("PyInstaller 설치 완료!")

def build_exe():
    """exe 파일 빌드"""
    print("exe 파일 빌드를 시작합니다...")
    
    # PyInstaller 명령어 구성
    cmd = [
        'pyinstaller',
        '--onedir',  # 폴더 형태로 생성 (라이브러리 호환성 향상)
        '--windowed',  # 콘솔 창 숨김
        '--name=올리브영_리뷰_수집기',  # exe 파일명
        '--icon=icon.ico',  # 아이콘 파일 (있는 경우)
        '--add-data=requirements.txt;.',  # requirements.txt 포함
        
        # 기본 라이브러리
        '--hidden-import=seleniumbase',
        '--hidden-import=seleniumbase.core',
        '--hidden-import=seleniumbase.core.browser_launcher',
        '--hidden-import=seleniumbase.fixtures',
        '--hidden-import=seleniumbase.fixtures.base_case',
        '--hidden-import=pandas',
        '--hidden-import=openpyxl',
        '--hidden-import=requests',
        '--hidden-import=urllib3',
        '--hidden-import=urllib3.util',
        '--hidden-import=urllib3.exceptions',
        
        # tkinter 관련
        '--hidden-import=tkinter',
        '--hidden-import=tkinter.ttk',
        '--hidden-import=tkinter.messagebox',
        '--hidden-import=tkinter.filedialog',
        
        # 셀레니움 관련
        '--hidden-import=selenium',
        '--hidden-import=selenium.webdriver',
        '--hidden-import=selenium.webdriver.chrome',
        '--hidden-import=selenium.webdriver.chrome.options',
        '--hidden-import=selenium.webdriver.chrome.service',
        '--hidden-import=selenium.webdriver.common',
        '--hidden-import=selenium.webdriver.common.by',
        '--hidden-import=selenium.webdriver.support',
        '--hidden-import=selenium.webdriver.support.ui',
        '--hidden-import=selenium.webdriver.support.wait',
        
        # JSON, 날짜 관련
        '--hidden-import=json',
        '--hidden-import=datetime',
        '--hidden-import=time',
        '--hidden-import=random',
        '--hidden-import=traceback',
        '--hidden-import=threading',
        '--hidden-import=subprocess',
        
        # 데이터 수집 관련
        '--collect-all=seleniumbase',
        '--collect-all=selenium',
        '--collect-all=pandas',
        '--collect-all=openpyxl',
        '--collect-all=urllib3',
        '--collect-all=certifi',
        
        # 추가 옵션
        '--noconfirm',  # 기존 빌드 덮어쓰기
        '--clean',  # 캐시 정리
        
        'olive_gui.py'
    ]
    
    # 아이콘 파일이 없으면 해당 옵션 제거
    if not os.path.exists('icon.ico'):
        cmd.remove('--icon=icon.ico')
    
    # requirements.txt가 없으면 해당 옵션 제거
    if not os.path.exists('requirements.txt'):
        cmd.remove('--add-data=requirements.txt;.')
    
    try:
        subprocess.run(cmd, check=True)
        print("\n" + "="*50)
        print("exe 파일 빌드 완료!")
        print("생성된 폴더: dist/올리브영_리뷰_수집기/")
        print("실행 파일: dist/올리브영_리뷰_수집기/올리브영_리뷰_수집기.exe")
        print("\n주의사항:")
        print("- 전체 폴더를 복사하여 사용하세요")
        print("- exe 파일만 따로 복사하면 실행되지 않을 수 있습니다")
        print("="*50)
    except subprocess.CalledProcessError as e:
        print(f"빌드 중 오류 발생: {e}")
        return False
    
    return True

def build_onefile_exe():
    """단일 exe 파일 빌드 (크기는 크지만 배포 편리)"""
    print("단일 exe 파일 빌드를 시작합니다...")
    
    cmd = [
        'pyinstaller',
        '--onefile',  # 단일 exe 파일로 생성
        '--windowed',  # 콘솔 창 숨김
        '--name=올리브영_리뷰_수집기_단일파일',  # exe 파일명
        '--hidden-import=seleniumbase',
        '--hidden-import=pandas',
        '--hidden-import=openpyxl',
        '--hidden-import=requests',
        '--hidden-import=urllib3',
        '--collect-all=seleniumbase',
        '--collect-all=pandas',
        '--collect-all=openpyxl',
        '--noconfirm',
        '--clean',
        'olive_gui.py'
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("\n단일 exe 파일 빌드 완료!")
        print("생성된 파일: dist/올리브영_리뷰_수집기_단일파일.exe")
        return True
    except subprocess.CalledProcessError as e:
        print(f"단일 파일 빌드 중 오류 발생: {e}")
        return False

def main():
    print("올리브영 리뷰 수집기 exe 빌드 도구")
    print("="*40)
    
    # PyInstaller 설치
    install_pyinstaller()
    
    print("\n빌드 옵션을 선택하세요:")
    print("1. 폴더 형태 (권장 - 안정성 높음)")
    print("2. 단일 exe 파일 (배포 편리)")
    print("3. 둘 다 빌드")
    
    choice = input("\n선택 (1/2/3): ").strip()
    
    success = False
    
    if choice == "1":
        success = build_exe()
    elif choice == "2":
        success = build_onefile_exe()
    elif choice == "3":
        print("\n폴더 형태 빌드 먼저 시작...")
        success1 = build_exe()
        print("\n단일 파일 빌드 시작...")
        success2 = build_onefile_exe()
        success = success1 or success2
    else:
        print("기본값으로 폴더 형태 빌드를 진행합니다...")
        success = build_exe()
    
    if success:
        print("\n빌드가 성공적으로 완료되었습니다!")
        print("dist 폴더에서 파일을 확인하세요.")
    else:
        print("\n빌드에 실패했습니다.")

if __name__ == "__main__":
    main() 