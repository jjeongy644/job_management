import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="조선대학교 추천채용 통합 관리", layout="wide")

# 고정된 시트 ID
SHEET_ID = "1SWpHQXBHwehSiU_3XNiLnaVGJFtwetWj1MNvRdXYoqQ"

# 파일 인증 대신 링크 기반 데이터 로드 함수
@st.cache_data(ttl=60)
def load_data(sheet_name):
    # 공개된 시트를 CSV로 읽어오는 방식 (인증 에러 원천 차단)
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    try:
        return pd.read_csv(url)
    except:
        return pd.DataFrame()

# 저장 로직은 gspread 인증이 필요하므로, 
# 만약 여전히 인증 문제가 발생한다면 '읽기 전용'으로 먼저 확인해보세요.
# 일단 아래 코드는 화면을 띄우는 데 집중한 버전입니다.

st.title("🎓 조선대학교 추천채용 통합 관리 시스템")

# 데이터 로드
if "data" not in st.session_state:
    st.session_state.data = {
        "등록기업": load_data("등록기업"),
        "지원학생": load_data("지원학생"),
        "합격자": load_data("합격자"),
        "기업분석": load_data("기업분석")
    }

menu = st.sidebar.radio("메뉴 이동", ["등록 기업 관리", "지원 학생 관리", "합격자 관리", "기업 분석 보고서"])

if menu == "등록 기업 관리":
    st.header("🏢 등록 기업 관리")
    st.dataframe(st.session_state.data["등록기업"], use_container_width=True)

elif menu == "지원 학생 관리":
    st.header("👨‍🎓 지원 학생 관리")
    st.dataframe(st.session_state.data["지원학생"], use_container_width=True)

elif menu == "합격자 관리":
    st.header("🏆 합격자 관리")
    st.dataframe(st.session_state.data["합격자"], use_container_width=True)

elif menu == "기업 분석 보고서":
    st.header("📝 기업 분석 보고서 목록")
    st.dataframe(st.session_state.data["기업분석"], use_container_width=True)
