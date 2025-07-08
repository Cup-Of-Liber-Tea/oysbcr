
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
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
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
