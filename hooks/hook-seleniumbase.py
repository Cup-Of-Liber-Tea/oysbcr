
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
