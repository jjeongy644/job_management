import streamlit as st
import pandas as pd
import datetime
import io
import os
import urllib.parse
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="조선대학교 추천채용 통합 관리 시스템", layout="wide")

# --- 데이터 영구 저장 경로 설정 ---
DATA_DIR = "saved_data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def load_data(filename, default_columns):
    filepath = os.path.join(DATA_DIR, filename)
    if os.path.exists(filepath):
        try:
            df = pd.read_csv(filepath)
            for col in df.columns:
                if "일" in col or "날짜" in col or "기간" in col or "일자" in col:
                    df[col] = df[col].astype(str).str.split(" ").str[0].replace("nan", "").replace("NaT", "")
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
if "reports" not in st.session_state: st.session_state.reports = {}
if "crawled_info" not in st.session_state: st.session_state.crawled_info = {"대표자": "", "설립일": "", "매출액": "", "업종": "", "기업유형": ""}

# --- 로고 및 헤더 ---
col_logo, col_title = st.columns([1, 5])
with col_logo:
    st.markdown("### 🎓 **CHOSUN**")
with col_title:
    st.title("조선대학교 추천채용 통합 관리 시스템")
    st.caption("조선대학교 취업학생처 취업전략팀 | 등록 기업, HR 담당자, 지원 학생 및 기업 분석 보고서 관리")
st.markdown("---")

# --- 유틸리티 함수 ---
def auto_detect_company_type(comp_name):
    if "공사" in comp_name or "공단" in comp_name: return "공공기관"
    elif "(주)" in comp_name: return "중견기업"
    return "우수기업"

def create_template(target_type):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        if target_type == "등록 기업 목록":
            pd.DataFrame(columns=["연번", "등록일", "기업명", "모집기간", "담당자성명", "직급", "내선번호", "연락처", "e-mail", "채용공고일자", "직무", "비고"]).to_excel(writer, index=False)
        else:
            pd.DataFrame(columns=["연번", "지원일자", "지원기업", "지원직무", "성명", "학과", "학번", "학적", "졸업(예정)일", "연락처", "이메일", "공고시기", "진행상태"]).to_excel(writer, index=False)
    return output.getvalue()

# --- 사이드바 메뉴 ---
menu = st.sidebar.selectbox("메뉴 선택", [
    "1. 등록 기업 관리", "2. 지원 학생 관리", "3. 합격자 DB & 멘토 풀", 
    "4. 추천채용 실적 및 주간/월간 보고", "5. 기존 엑셀 일괄 업로드", "6. 기업 분석 보고서 생성"
])

# --- 1. 등록 기업 관리 ---
if menu == "1. 등록 기업 관리":
    st.header("🏢 등록 기업 & HR 담당자 리스트")
    st.session_state.companies = st.data_editor(st.session_state.companies, use_container_width=True, num_rows="dynamic", column_config={"연번": st.column_config.NumberColumn(disabled=True)})
    if st.button("저장하기"):
        save_data("companies.csv", st.session_state.companies)
        st.success("저장 완료!")

# --- 2. 지원 학생 관리 ---
elif menu == "2. 지원 학생 관리":
    st.header("👨‍🎓 지원 학생 상세 리스트")
    st.session_state.applicants = st.data_editor(st.session_state.applicants, use_container_width=True, num_rows="dynamic", column_config={"연번": st.column_config.NumberColumn(disabled=True)})
    if st.button("저장하기"):
        save_data("applicants.csv", st.session_state.applicants)
        st.success("저장 완료!")

# --- 3. 합격자 DB ---
elif menu == "3. 합격자 DB & 멘토 풀":
    st.header("🏆 합격자 DB & 멘토 풀")
    st.session_state.passed = st.data_editor(st.session_state.passed, use_container_width=True, num_rows="dynamic")
    if st.button("저장하기"):
        save_data("passed.csv", st.session_state.passed)
        st.success("저장 완료!")

# --- 4. 실적 보고 ---
elif menu == "4. 추천채용 실적 및 주간/월간 보고":
    st.header("📊 추천채용 실적 보고")
    if st.button("전체 DB 엑셀 다운로드"):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            st.session_state.companies.to_excel(writer, sheet_name='기업', index=False)
            st.session_state.applicants.to_excel(writer, sheet_name='학생', index=False)
        st.download_button("파일 다운로드", data=output.getvalue(), file_name="Total_Data.xlsx")

# --- 5. 엑셀 업로드 ---
elif menu == "5. 기존 엑셀 일괄 업로드":
    st.header("📂 엑셀 데이터 업로드")
    target = st.selectbox("업로드 대상", ["등록 기업 목록", "지원 학생 목록"])
    uploaded = st.file_uploader("파일 선택", type=["xlsx"])
    if uploaded:
        df_new = pd.read_excel(uploaded)
        if st.button("데이터 통합 저장"):
            if "기업" in target:
                st.session_state.companies = pd.concat([st.session_state.companies, df_new], ignore_index=True)
                save_data("companies.csv", st.session_state.companies)
            else:
                st.session_state.applicants = pd.concat([st.session_state.applicants, df_new], ignore_index=True)
                save_data("applicants.csv", st.session_state.applicants)
            st.success("통합 완료!")
            st.rerun()

# --- 6. 기업 분석 보고서 ---
elif menu == "6. 기업 분석 보고서 생성":
    st.header("📝 기업 분석 보고서 생성")
    with st.form("a"):
        comp = st.text_input("기업명")
        if st.form_submit_button("저장"): st.success("저장됨")
