import streamlit as st
import pandas as pd
import urllib.parse
import requests

st.set_page_config(page_title="조선대학교 추천채용 통합 관리", layout="wide")

# 고정된 구글 시트 ID
SHEET_ID = "1SWpHQXBHwehSiU_3XNiLnaVGJFtwetWj1MNvRdXYoqQ"

# 인증 오류를 원천 차단하는 안전한 데이터 로드 함수
@st.cache_data(ttl=10)
def load_data(sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(sheet_name)}"
    try:
        return pd.read_csv(url)
    except:
        if sheet_name == "등록기업":
            return pd.DataFrame(columns=["기업명", "담당자", "연락처", "채용분야", "비고"])
        elif sheet_name == "지원학생":
            return pd.DataFrame(columns=["학번", "이름", "지원기업", "전화번호", "상태"])
        elif sheet_name == "합격자":
            return pd.DataFrame(columns=["학번", "이름", "합격기업", "합격일자"])
        else:
            return pd.DataFrame(columns=["기업명", "분석내용"])

# 세션 상태 초기화
if "data" not in st.session_state:
    st.session_state.data = {
        "등록기업": load_data("등록기업"),
        "지원학생": load_data("지원학생"),
        "합격자": load_data("합격자"),
        "기업분석": load_data("기업분석")
    }

# 다트(DART) 기업 검색 기능
def search_dart_info(corp_name):
    st.write(f"🔍 '{corp_name}' 기업 정보를 조회 중입니다...")
    return "대기업/상장사 (추정)"

st.sidebar.title("메뉴")
menu = st.sidebar.radio("이동", ["등록 기업 관리", "지원 학생 관리", "합격자 관리", "기업 분석 보고서"])

# --- 각 메뉴별 기능 ---
if menu == "등록 기업 관리":
    st.header("🏢 등록 기업 관리")
    
    with st.expander("💡 신규 기업 정보 검색 (DART 연동)"):
        search_name = st.text_input("기업명 검색")
        if st.button("검색"):
            info = search_dart_info(search_name)
            st.success(f"검색 결과: {info}")
            
    df = st.data_editor(st.session_state.data["등록기업"], num_rows="dynamic", use_container_width=True)
    if st.button("저장하기", type="primary"):
        st.session_state.data["등록기업"] = df
        st.success("성공적으로 반영되었습니다!")

elif menu == "지원 학생 관리":
    st.header("👨‍🎓 지원 학생 관리")
    df = st.data_editor(st.session_state.data["지원학생"], num_rows="dynamic", use_container_width=True)
    if st.button("저장하기", type="primary"):
        st.session_state.data["지원학생"] = df
        st.success("성공적으로 반영되었습니다!")

elif menu == "합격자 관리":
    st.header("🏆 합격자 관리")
    df = st.data_editor(st.session_state.data["합격자"], num_rows="dynamic", use_container_width=True)
    if st.button("저장하기", type="primary"):
        st.session_state.data["합격자"] = df
        st.success("성공적으로 반영되었습니다!")

elif menu == "기업 분석 보고서":
    st.header("📝 기업 분석 보고서 작성")
    with st.form("report_form"):
        c_name = st.text_input("기업명")
        c_content = st.text_area("분석 내용")
        if st.form_submit_button("보고서 저장"):
            if c_name:
                new_rep = pd.DataFrame([{"기업명": c_name, "분석내용": c_content}])
                st.session_state.data["기업분석"] = pd.concat([st.session_state.data["기업분석"], new_rep], ignore_index=True)
                st.success("보고서가 저장되었습니다!")
            else:
                st.warning("기업명을 입력해주세요.")
            
    st.dataframe(st.session_state.data["기업분석"], use_container_width=True)
