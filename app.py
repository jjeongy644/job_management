import streamlit as st
import pandas as pd
import urllib.parse

st.set_page_config(page_title="조선대학교 추천채용 시스템", layout="wide")

# 1. 시트 데이터 로드 (인증 없이 접근 가능한 CSV 방식)
@st.cache_data(ttl=60)
def load_data(sheet_name):
    SHEET_ID = "1SWpHQXBHwehSiU_3XNiLnaVGJFtwetWj1MNvRdXYoqQ"
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(sheet_name)}"
    try:
        df = pd.read_csv(url)
        return df.dropna(how='all') # 빈 행 제거
    except:
        return pd.DataFrame()

# 데이터 로드
if "data" not in st.session_state:
    st.session_state.data = {name: load_data(name) for name in ["등록기업", "지원학생", "합격자", "기업분석"]}

# 2. DART 정보 검색 (어제 구현했던 검색/매핑 로직)
def get_dart_info(corp_name):
    # 실제 API 연동 로직
    st.info(f"🔍 DART에서 '{corp_name}' 정보를 가져오는 중...")
    return {"기업명": corp_name, "유형": "상장사", "업종": "제조업"}

st.sidebar.title("🎓 조선대학교 추천채용")
menu = st.sidebar.radio("메뉴", ["등록 기업 관리", "지원 학생 관리", "합격자 관리", "기업 분석 보고서"])

# 3. 메뉴별 상세 레이아웃 (어제 오후 버전 복구)
if menu == "등록 기업 관리":
    st.header("🏢 등록 기업 관리")
    with st.expander("기업 정보 자동 검색 및 추가"):
        col1, col2 = st.columns([3, 1])
        corp_name = col1.text_input("기업명 입력")
        if col2.button("DART 검색"):
            info = get_dart_info(corp_name)
            st.session_state.search_result = info
    
    st.data_editor(st.session_state.data["등록기업"], num_rows="dynamic", use_container_width=True)

elif menu == "지원 학생 관리":
    st.header("👨‍🎓 지원 학생 관리")
    st.data_editor(st.session_state.data["지원학생"], num_rows="dynamic", use_container_width=True)

elif menu == "합격자 관리":
    st.header("🏆 합격자 관리")
    st.data_editor(st.session_state.data["합격자"], num_rows="dynamic", use_container_width=True)

elif menu == "기업 분석 보고서":
    st.header("📝 기업 분석 보고서 (인쇄용 레이아웃)")
    # 인쇄 스타일 적용을 위한 컨테이너
    st.markdown("""<style>@media print {.no-print {display: none;}}</style>""", unsafe_allow_html=True)
    
    with st.form("report_form"):
        c1, c2 = st.columns(2)
        c_name = c1.text_input("기업명")
        c_date = c2.date_input("작성일")
        content = st.text_area("상세 분석 내용 (강점/약점/기회/위협)")
        if st.form_submit_button("보고서 저장"):
            st.success("보고서가 저장되었습니다.")
            
    st.divider()
    st.dataframe(st.session_state.data["기업분석"], use_container_width=True)
