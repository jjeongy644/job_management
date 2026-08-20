import streamlit as st
import pandas as pd
import datetime
import io
import os
import urllib.parse
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="조선대학교 추천채용 통합 관리 시스템", layout="wide")

# 로고 파일 자동 감지
def get_logo_path():
    files = os.listdir(".") if os.path.exists(".") else []
    for f in files:
        f_lower = f.lower()
        if f_lower.startswith("logo") or "로고" in f_lower or "조선" in f_lower:
            if f_lower.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
                return f
    return None

logo_file = get_logo_path()

col_logo, col_title = st.columns([1, 5])
with col_logo:
    if logo_file:
        st.image(logo_file, width=140)
    else:
        st.markdown("### 🎓 **CHOSUN**")

with col_title:
    st.title("조선대학교 추천채용 통합 관리 시스템")
    st.caption("조선대학교 취업학생처 취업전략팀 | 등록 기업, HR 담당자, 지원 학생 및 기업 분석 보고서 관리")

st.markdown("---")

# --- 데이터 영구 축적 함수 ---
DATA_DIR = "saved_data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def load_persistent_data(filename, default_df):
    filepath = os.path.join(DATA_DIR, filename)
    if os.path.exists(filepath):
        try:
            return pd.read_csv(filepath)
        except:
            return default_df
    return default_df

def save_persistent_data(filename, df):
    filepath = os.path.join(DATA_DIR, filename)
    df.to_csv(filepath, index=False)

# 메뉴 선택 (아이콘 제거)
menu = st.sidebar.selectbox("메뉴 선택", [
    "1. 등록 기업 관리", 
    "2. 지원 학생 관리", 
    "3. 합격자 DB & 멘토 풀", 
    "4. 추천채용 실적 및 주간/월간 보고", 
    "5. 기존 엑셀 일괄 업로드", 
    "6. 기업 분석 보고서 생성"
])

# 세션 초기화 및 유틸 함수
if "companies" not in st.session_state:
    st.session_state.companies = load_persistent_data("companies.csv", pd.DataFrame(columns=["연번", "등록일", "기업명", "모집기간", "담당자성명", "직급", "내선번호", "연락처", "e-mail", "채용공고일자", "직무", "비고"]))
if "applicants" not in st.session_state:
    st.session_state.applicants = load_persistent_data("applicants.csv", pd.DataFrame(columns=["연번", "지원일자", "지원기업", "지원직무", "성명", "학과", "학번", "학적", "졸업(예정)일", "연락처", "이메일", "공고시기", "진행상태"]))
if "reports" not in st.session_state: st.session_state.reports = {}
if "crawled_info" not in st.session_state: st.session_state.crawled_info = {"대표자": "", "설립일": "", "매출액": "", "업종": "", "기업유형": ""}

# --- 메뉴 로직 ---
if menu == "1. 등록 기업 관리":
    st.header("🏢 추천채용 등록 기업 & HR 담당자 리스트")
    edited_companies = st.data_editor(st.session_state.companies, use_container_width=True, num_rows="dynamic", column_config={"연번": st.column_config.NumberColumn("연번", disabled=True)})
    st.session_state.companies = edited_companies
    if st.button("저장하기"): # 빨간 버튼 삭제 및 기본색 적용
        save_persistent_data("companies.csv", st.session_state.companies)
        st.success("데이터가 저장되었습니다!")

elif menu == "2. 지원 학생 관리":
    st.header("👨‍🎓 지원 학생 상세 리스트")
    edited_applicants = st.data_editor(st.session_state.applicants, use_container_width=True, num_rows="dynamic", column_config={"연번": st.column_config.NumberColumn("연번", disabled=True)})
    st.session_state.applicants = edited_applicants
    if st.button("저장하기"):
        save_persistent_data("applicants.csv", st.session_state.applicants)
        st.success("데이터가 저장되었습니다!")

elif menu == "3. 합격자 DB & 멘토 풀":
    st.header("🏆 합격자 데이터베이스 & 실무 멘토 풀")
    # ... (생략된 로직 동일)

elif menu == "4. 추천채용 실적 및 주간/월간 보고":
    st.header("📊 추천채용 실적 보고 (주간 / 월간)")
    # ... (주간/월간 로직 동일, 엑셀 다운로드 버튼 포함)

elif menu == "5. 기존 엑셀 일괄 업로드":
    st.header("기존 엑셀 데이터 불러오기")
    # ... (양식 다운로드 및 업로드 로직 동일)

elif menu == "6. 기업 분석 보고서 생성":
    st.header("기업 분석 및 추천채용 보고서 생성")
    # ... (상세 보고서 로직 동일)
