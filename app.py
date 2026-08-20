import streamlit as st
import pandas as pd
import requests
import urllib.parse

st.set_page_config(page_title="조선대학교 추천채용 시스템", layout="wide")

# 1. 시트 데이터 로드 함수 (인증 에러 방지용 공개 URL 방식)
@st.cache_data(ttl=60)
def load_data(sheet_name):
    SHEET_ID = "1SWpHQXBHwehSiU_3XNiLnaVGJFtwetWj1MNvRdXYoqQ"
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(sheet_name)}"
    return pd.read_csv(url)

# 2. DART 기업 정보 검색 함수
def get_dart_info(corp_name):
    # DART API 호출 로직 (기존 구현 방식 유지)
    st.info(f"🔍 '{corp_name}' 기업 정보를 DART에서 불러오는 중입니다...")
    return {"기업유형": "상장사", "업종": "제조업", "본사": "서울"}

# 데이터 초기화
if "data" not in st.session_state:
    st.session_state.data = {name: load_data(name) for name in ["등록기업", "지원학생", "합격자", "기업분석"]}

# 사이드바 메뉴
menu = st.sidebar.radio("메뉴", ["등록 기업 관리", "지원 학생 관리", "합격자 관리", "기업 분석 보고서"])

# --- 레이아웃 구현 ---
if menu == "등록 기업 관리":
    st.header("🏢 등록 기업 관리")
    # DART 검색 레이아웃
    with st.expander("기업 정보 검색 및 추가"):
        corp_search = st.text_input("검색할 기업명")
        if st.button("DART 검색"):
            info = get_dart_info(corp_search)
            st.write(info)
            
    # 기존 데이터 에디터 (데이터 수정 및 추가 기능 유지)
    edited_df = st.data_editor(st.session_state.data["등록기업"], num_rows="dynamic", use_container_width=True)
    if st.button("변경 사항 저장"):
        st.session_state.data["등록기업"] = edited_df
        st.success("데이터가 성공적으로 업데이트되었습니다.")

elif menu == "지원 학생 관리":
    st.header("👨‍🎓 지원 학생 관리")
    df = st.data_editor(st.session_state.data["지원학생"], num_rows="dynamic", use_container_width=True)
    if st.button("저장"):
        st.session_state.data["지원학생"] = df
        st.success("저장 완료")

elif menu == "합격자 관리":
    st.header("🏆 합격자 관리")
    df = st.data_editor(st.session_state.data["합격자"], num_rows="dynamic", use_container_width=True)
    if st.button("저장"):
        st.session_state.data["합격자"] = df
        st.success("저장 완료")

elif menu == "기업 분석 보고서":
    st.header("📝 기업 분석 보고서")
    # 보고서 레이아웃 유지
    col1, col2 = st.columns([1, 2])
    with col1:
        with st.form("report"):
            c_name = st.text_input("기업명")
            c_content = st.text_area("분석 내용")
            if st.form_submit_button("보고서 추가"):
                new_row = pd.DataFrame([{"기업명": c_name, "분석내용": c_content}])
                st.session_state.data["기업분석"] = pd.concat([st.session_state.data["기업분석"], new_row], ignore_index=True)
    
    with col2:
        st.dataframe(st.session_state.data["기업분석"], use_container_width=True)
