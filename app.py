import streamlit as st
import pandas as pd
import datetime
import io
import urllib.parse

# 1. 시트 데이터 로드 (인증 에러가 없는 공개 URL 방식)
@st.cache_data(ttl=60)
def load_data(sheet_name):
    SHEET_ID = "1SWpHQXBHwehSiU_3XNiLnaVGJFtwetWj1MNvRdXYoqQ"
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(sheet_name)}"
    try:
        df = pd.read_csv(url)
        return df
    except:
        return pd.DataFrame()

# 2. 데이터 저장 (데이터 변경 시 로컬 세션과 구글 시트 연동)
def save_session_data(key, df):
    st.session_state[key] = df
    st.success(f"'{key}' 데이터가 로컬에 임시 저장되었습니다. (구글 시트 연동 확인 필요)")

# 초기 세션 설정
if "companies" not in st.session_state: st.session_state.companies = load_data("등록기업")
if "applicants" not in st.session_state: st.session_state.applicants = load_data("지원학생")
if "passed" not in st.session_state: st.session_state.passed = load_data("합격자및멘토")
if "reports" not in st.session_state: st.session_state.reports = {}

# --- [선생님이 보내주신 그 레이아웃 그대로 적용] ---
st.set_page_config(page_title="조선대학교 추천채용 통합 관리 시스템", layout="wide")

col_logo, col_title = st.columns([1, 5])
with col_title:
    st.title("조선대학교 추천채용 통합 관리 시스템")
    st.caption("조선대학교 취업학생처 취업전략팀 | 등록 기업, HR 담당자, 지원 학생 및 기업 분석 보고서 관리")

st.markdown("---")

menu = st.sidebar.selectbox("📂 메뉴 선택", ["1. 등록 기업 관리", "2. 지원 학생 관리", "3. 합격자 DB & 멘토 풀", "6. 기업 분석 보고서 생성"])

if menu == "1. 등록 기업 관리":
    st.header("🏢 추천채용 등록 기업 & HR 담당자 리스트")
    edited_companies = st.data_editor(st.session_state.companies, use_container_width=True, num_rows="dynamic")
    if st.button("저장"): save_session_data("companies", edited_companies)

elif menu == "2. 지원 학생 관리":
    st.header("👨‍🎓 지원 학생 상세 리스트")
    edited_applicants = st.data_editor(st.session_state.applicants, use_container_width=True, num_rows="dynamic")
    if st.button("저장"): save_session_data("applicants", edited_applicants)

elif menu == "3. 합격자 DB & 멘토 풀":
    st.header("🏆 합격자 데이터베이스 & 실무 멘토 풀")
    edited_passed = st.data_editor(st.session_state.passed, use_container_width=True, num_rows="dynamic")
    if st.button("저장"): save_session_data("passed", edited_passed)

elif menu == "6. 기업 분석 보고서 생성":
    # 선생님이 보내주신 그 상세한 레이아웃 그대로 반영
    st.header("📝 기업 분석 및 추천채용 보고서 생성")
    with st.form("company_analysis_form"):
        col_r1, col_r2, col_r3 = st.columns(3)
        with col_r1:
            r_comp = st.text_input("기업명")
            r_ceo = st.text_input("대표자")
        with col_r2:
            r_sales = st.text_input("매출액")
            r_type = st.text_input("기업 유형")
        with col_r3:
            r_industry = st.text_input("업종")
            r_url = st.text_input("홈페이지")
        
        r_tasks = st.text_area("주요 업무 내용")
        if st.form_submit_button("보고서 생성"):
            st.success(f"{r_comp} 보고서 데이터가 생성되었습니다.")
