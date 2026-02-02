import os
import sys

# 프로젝트 루트(= tests의 상위 폴더)를 PYTHONPATH에 추가
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
