import streamlit as st
import pandas as pd
import datetime
import io

st.set_page_config(page_title="조선대학교 추천채용 통합 관리 시스템", layout="wide")

# 각 시트별 정의된 헤더 구조
def get_empty_df(sheet_type):
    if sheet_type == "companies":
        # 요청하신 등록기업 리스트 컬럼
        return pd.DataFrame(columns=["등록일", "기업명", "모집기간", "담당자성명", "직급", "내선번호", "연락처", "e-mail", "채용공고일자", "직무", "비고"])
    elif sheet_type == "applicants":
        # 요청하신 지원자 리스트 컬럼
        return pd.DataFrame(columns=["지원일자", "지원기업", "지원직무", "성명", "학과", "학번", "학적", "졸업(예정)일", "연락처", "이메일", "공고시기", "진행상태"])
    elif sheet_type == "passed":
        return pd.DataFrame(columns=["연번", "합격일자", "학번", "이름", "학과", "연락처", "기업명", "직무", "입사일", "재직상태", "멘토가능여부", "비고"])
    return pd.DataFrame()

# 세션 상태 초기화
if "companies" not in st.session_state: st.session_state.companies = get_empty_df("companies")
if "applicants" not in st.session_state: st.session_state.applicants = get_empty_df("applicants")
if "passed" not in st.session_state: st.session_state.passed = get_empty_df("passed")

menu = st.sidebar.selectbox("📂 메뉴 선택", ["1. 등록 기업 관리", "2. 지원 학생 관리", "3. 합격자 DB & 멘토 풀", "6. 기업 분석 보고서 생성"])

# --- 1. 등록 기업 관리 ---
if menu == "1. 등록 기업 관리":
    st.header("🏢 추천채용 등록 기업 & HR 담당자 리스트")
    st.info("💡 행을 추가하거나 셀을 더블클릭하여 수정하세요.")
    st.session_state.companies = st.data_editor(st.session_state.companies, use_container_width=True, num_rows="dynamic")
    if st.button("저장"): st.success("기업 리스트가 업데이트되었습니다.")

# --- 2. 지원 학생 관리 ---
elif menu == "2. 지원 학생 관리":
    st.header("👨‍🎓 지원 학생 상세 리스트")
    st.info("💡 지원자 정보를 관리합니다.")
    st.session_state.applicants = st.data_editor(st.session_state.applicants, use_container_width=True, num_rows="dynamic")
    if st.button("저장"): st.success("지원자 리스트가 업데이트되었습니다.")

# --- 3. 합격자 DB ---
elif menu == "3. 합격자 DB & 멘토 풀":
    st.header("🏆 합격자 데이터베이스")
    st.session_state.passed = st.data_editor(st.session_state.passed, use_container_width=True, num_rows="dynamic")
    if st.button("저장"): st.success("합격자 DB가 업데이트되었습니다.")

# --- 6. 기업 분석 보고서 생성 ---
elif menu == "📝 6. 기업 분석 보고서 생성":
    st.header("📝 기업 분석 보고서 생성")
    # 기존 보고서 로직 유지...
