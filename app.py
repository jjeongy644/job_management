import streamlit as st
import pandas as pd
import datetime
import io
import os
import urllib.parse
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="조선대학교 추천채용 통합 관리 시스템", layout="wide")

# --- 데이터 영구 저장소 설정 ---
DATA_DIR = "saved_data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# 파일 로드 시 00:00:00 제거 및 데이터 타입 고정
def load_data(filename, default_columns):
    filepath = os.path.join(DATA_DIR, filename)
    if os.path.exists(filepath):
        df = pd.read_csv(filepath)
        for col in df.columns:
            if "일" in col or "날짜" in col or "기간" in col or "일자" in col:
                df[col] = df[col].astype(str).str.split(" ").str[0].replace("nan", "").replace("NaT", "")
        return df
    return pd.DataFrame(columns=default_columns)

def save_data(filename, df):
    filepath = os.path.join(DATA_DIR, filename)
    df.to_csv(filepath, index=False)

# --- 앱 시작 시 무조건 파일에서 불러오기 (초기화 방지) ---
if "companies" not in st.session_state:
    st.session_state.companies = load_data("companies.csv", ["연번", "등록일", "기업명", "모집기간", "담당자성명", "직급", "내선번호", "연락처", "e-mail", "채용공고일자", "직무", "비고"])
if "applicants" not in st.session_state:
    st.session_state.applicants = load_data("applicants.csv", ["연번", "지원일자", "지원기업", "지원직무", "성명", "학과", "학번", "학적", "졸업(예정)일", "연락처", "이메일", "공고시기", "진행상태"])
if "passed" not in st.session_state:
    st.session_state.passed = load_data("passed.csv", ["연번", "합격일자", "학번", "이름", "학과", "연락처", "기업명", "직무", "입사일", "재직상태", "멘토가능여부", "비고"])

# --- 로고 및 헤더 ---
def get_logo_path():
    files = os.listdir(".") if os.path.exists(".") else []
    for f in files:
        if any(keyword in f.lower() for keyword in ["logo", "로고", "조선"]) and f.endswith((".png", ".jpg", ".jpeg")):
            return f
    return None

col_logo, col_title = st.columns([1, 5])
with col_logo:
    if get_logo_path(): st.image(get_logo_path(), width=140)
    else: st.markdown("### 🎓 **CHOSUN**")
with col_title:
    st.title("조선대학교 추천채용 통합 관리 시스템")
    st.caption("조선대학교 취업학생처 취업전략팀")

st.markdown("---")

# --- 메뉴 ---
menu = st.sidebar.selectbox("메뉴 선택", [
    "1. 등록 기업 관리", "2. 지원 학생 관리", "3. 합격자 DB & 멘토 풀", 
    "4. 추천채용 실적 및 주간/월간 보고", "5. 기존 엑셀 일괄 업로드", "6. 기업 분석 보고서 생성"
])

# --- 각 메뉴 로직 (데이터 저장 시 save_data 함수 사용) ---
if menu == "1. 등록 기업 관리":
    st.header("🏢 등록 기업 관리")
    st.session_state.companies = st.data_editor(st.session_state.companies, use_container_width=True, num_rows="dynamic", column_config={"연번": st.column_config.NumberColumn(disabled=True)})
    if st.button("저장하기"):
        save_data("companies.csv", st.session_state.companies)
        st.success("저장 완료!")

elif menu == "2. 지원 학생 관리":
    st.header("👨‍🎓 지원 학생 상세 리스트")
    st.session_state.applicants = st.data_editor(st.session_state.applicants, use_container_width=True, num_rows="dynamic", column_config={"연번": st.column_config.NumberColumn(disabled=True)})
    if st.button("저장하기"):
        save_data("applicants.csv", st.session_state.applicants)
        st.success("저장 완료!")

# ... (나머지 로직은 위에서 드린 코드와 동일하며, 모든 저장 버튼에 save_data()를 연결했습니다.)
