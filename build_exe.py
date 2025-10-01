import os
import subprocess
import shutil
import sys
from datetime import datetime

def build_exe():
    print("--- PyInstaller 빌드 시작 ---")

    # 기존 빌드 디렉토리 삭제
    print("기존 'build' 및 'dist' 디렉토리 삭제 중...")
    if os.path.exists("build"):
        shutil.rmtree("build")
        print("'build' 디렉토리 삭제 완료.")
    if os.path.exists("dist"):
        shutil.rmtree("dist")
        print("'dist' 디렉토리 삭제 완료.")
    print("정리 완료.")

    # PyInstaller 명령어 구성
    # --windowed (또는 -w)는 GUI 실행 시 콘솔 창을 숨깁니다.
    # 디버깅을 위해 잠시 이 옵션을 제거하고 콘솔과 함께 실행하는 것이 좋습니다.
    # 만약 안정성을 확인한 후에는 다시 --windowed를 추가할 수 있습니다.
    command = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", "올리브영_리뷰_수집기_GUI",
        "olive_gui.py",
        "--add-data", "olive_scraper.py;.",
        "--add-data", "hooks;hooks",
        "--hidden-import", "pandas._libs.tslibs.np_datetime",
        "--hidden-import", "pandas._libs.tslibs.nattype",
        "--hidden-import", "pandas._libs.interval",
        "--hidden-import", "pandas._libs.json",
        "--hidden-import", "pandas._libs.period",
        "--hidden-import", "pandas._libs.index",
        "--hidden-import", "pandas._libs.skiplist",
        "--hidden-import", "pandas._libs.hashing",
        "--hidden-import", "pandas._libs.lib",
        "--hidden-import", "pandas._libs.sparse",
        "--hidden-import", "pandas._libs.writers",
        "--hidden-import", "pandas._libs.window",
        "--hidden-import", "pandas._libs.reshape",
        "--hidden-import", "pandas._libs.reduction",
        "--hidden-import", "pandas._libs.algos",
        "--hidden-import", "pandas._libs.join",
        "--hidden-import", "pandas._libs.hashtable",
        "--hidden-import", "pandas._libs.indexing",
        "--hidden-import", "pandas._libs.internals",
        "--hidden-import", "pandas._libs.parsers",
        "--hidden-import", "pandas._libs.properties",
        "--hidden-import", "pandas._libs.missing",
        "--hidden-import", "pandas._libs.interval",
        "--hidden-import", "pandas._libs.arrays",
        "--hidden-import", "pandas._libs.tslibs.timedeltas",
        "--hidden-import", "numpy",
        "--hidden-import", "numpy.core",
        "--hidden-import", "numpy.linalg",
        "--hidden-import", "openpyxl",
        "--hidden-import", "xlsxwriter",
        "--hidden-import", "scipy.stats",
        "--hidden-import", "scipy.special"
        # --windowed 옵션을 추가하려면 아래 주석을 해제하세요. (안정화 후)
        # "--windowed"
    ]

    print("PyInstaller 명령 실행 중...")
    try:
        # Popen을 사용하여 실시간 출력 확인
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, encoding='utf-8', errors='replace')
        for line in process.stdout:
            print(line, end='')
        process.wait()

        if process.returncode == 0:
            print(f"\n빌드 성공! 실행 파일은 'dist\\올리브영_리뷰_수집기_GUI.exe' 에 있습니다.")
            # 빌드 성공 후 config.ini 복사 (필요한 경우)
            if os.path.exists("config.ini"):
                shutil.copy("config.ini", "dist")
                print("config.ini 파일이 'dist' 폴더로 복사되었습니다.")
        else:
            print(f"\n빌드 실패! 종료 코드: {process.returncode}")
            print("자세한 내용은 빌드 과정 중 출력된 로그를 확인하세요.")
            if os.path.exists("build/올리브영_리뷰_수집기_GUI/warn-올리브영_리뷰_수집기_GUI.txt"):
                print(f"경고 로그 파일: build/올리브영_리뷰_수집기_GUI/warn-올리브영_리뷰_수집기_GUI.txt")

    except FileNotFoundError:
        print("오류: PyInstaller를 찾을 수 없습니다. 'pip install PyInstaller'를 실행했는지 확인하세요.")
    except Exception as e:
        print(f"빌드 중 예외 발생: {e}")

    print("--- PyInstaller 빌드 종료 ---")

if __name__ == "__main__":
    build_exe()
