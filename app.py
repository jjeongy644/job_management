import streamlit as st
import pandas as pd
import datetime
import io
import os
import urllib.parse
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="조선대학교 추천채용 통합 관리 시스템", layout="wide")

# --- 데이터 저장 경로 설정 ---
# Streamlit Cloud 환경을 고려한 명시적 경로 설정
BASE_DIR = os.getcwd()
DATA_DIR = os.path.join(BASE_DIR, "saved_data")
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def load_data(filename, default_columns):
    filepath = os.path.join(DATA_DIR, filename)
    if os.path.exists(filepath):
        try:
            df = pd.read_csv(filepath)
            return df
        except:
            return pd.DataFrame(columns=default_columns)
    return pd.DataFrame(columns=default_columns)

def save_data(filename, df):
    filepath = os.path.join(DATA_DIR, filename)
    df.to_csv(filepath, index=False)

# --- 초기 데이터 로드 ---
if "companies" not in st.session_state:
    st.session_state.companies = load_data("companies.csv", ["연번", "등록일", "기업명", "모집기간", "담당자성명", "직급", "내선번호", "연락처", "e-mail", "채용공고일자", "직무", "비고"])
if "applicants" not in st.session_state:
    st.session_state.applicants = load_data("applicants.csv", ["연번", "지원일자", "지원기업", "지원직무", "성명", "학과", "학번", "학적", "졸업(예정)일", "연락처", "이메일", "공고시기", "진행상태"])
if "passed" not in st.session_state:
    st.session_state.passed = load_data("passed.csv", ["연번", "합격일자", "학번", "이름", "학과", "연락처", "기업명", "직무", "입사일", "재직상태", "멘토가능여부", "비고"])

# --- UI 레이아웃 ---
col_logo, col_title = st.columns([1, 5])
with col_logo:
    st.markdown("### 🎓 **CHOSUN**")
with col_title:
    st.title("조선대학교 추천채용 통합 관리 시스템")
    st.caption("조선대학교 취업학생처 취업전략팀")

st.markdown("---")

menu = st.sidebar.selectbox("메뉴 선택", [
    "1. 등록 기업 관리", "2. 지원 학생 관리", "3. 합격자 DB & 멘토 풀", 
    "4. 추천채용 실적 및 주간/월간 보고", "5. 기존 엑셀 일괄 업로드", "6. 기업 분석 보고서 생성"
])

# --- 메뉴 로직 ---
if menu == "1. 등록 기업 관리":
    st.header("🏢 등록 기업 관리")
    st.session_state.companies = st.data_editor(st.session_state.companies, use_container_width=True, num_rows="dynamic")
    if st.button("저장하기"):
        save_data("companies.csv", st.session_state.companies)
        st.success("데이터 저장 완료!")

elif menu == "2. 지원 학생 관리":
    st.header("👨‍🎓 지원 학생 상세 리스트")
    st.session_state.applicants = st.data_editor(st.session_state.applicants, use_container_width=True, num_rows="dynamic")
    if st.button("저장하기"):
        save_data("applicants.csv", st.session_state.applicants)
        st.success("데이터 저장 완료!")

elif menu == "3. 합격자 DB & 멘토 풀":
    st.header("🏆 합격자 DB & 멘토 풀")
    st.session_state.passed = st.data_editor(st.session_state.passed, use_container_width=True, num_rows="dynamic")
    if st.button("저장하기"):
        save_data("passed.csv", st.session_state.passed)
        st.success("저장 완료!")

elif menu == "4. 추천채용 실적 및 주간/월간 보고":
    st.header("📊 실적 보고 및 엑셀 다운로드")
    if st.button("엑셀 다운로드"):
        output = io.BytesIO()
        with pd.ExcelWriter(output) as writer:
            st.session_state.companies.to_excel(writer, sheet_name='기업', index=False)
            st.session_state.applicants.to_excel(writer, sheet_name='학생', index=False)
        st.download_button("전체 DB 다운로드", data=output.getvalue(), file_name="DB_Backup.xlsx")

elif menu == "5. 기존 엑셀 일괄 업로드":
    st.header("📂 엑셀 데이터 업로드")
    target = st.selectbox("업로드 대상", ["등록 기업", "지원 학생"])
    uploaded = st.file_uploader("파일 선택", type=["xlsx"])
    if uploaded:
        df_new = pd.read_excel(uploaded)
        st.dataframe(df_new)
        if st.button("파일 통합 및 저장"):
            if target == "등록 기업":
                st.session_state.companies = pd.concat([st.session_state.companies, df_new], ignore_index=True)
                save_data("companies.csv", st.session_state.companies)
            else:
                st.session_state.applicants = pd.concat([st.session_state.applicants, df_new], ignore_index=True)
                save_data("applicants.csv", st.session_state.applicants)
            st.success("통합 완료!")
            st.rerun()

elif menu == "6. 기업 분석 보고서 생성":
    st.header("📝 기업 분석 보고서 생성")
    with st.form("a"):
        comp = st.text_input("기업명")
        if st.form_submit_button("저장"): st.success("저장됨")
