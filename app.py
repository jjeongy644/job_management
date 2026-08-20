import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests # 다트 검색을 위해 추가

st.set_page_config(page_title="조선대학교 추천채용 통합 관리", layout="wide")

# 1. 인증 설정 (Secrets 연동)
@st.cache_resource
def init_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = dict(st.secrets["gcp"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open_by_key("1SWpHQXBHwehSiU_3XNiLnaVGJFtwetWj1MNvRdXYoqQ")

gc = init_google_sheets()

# 2. 데이터 불러오기 및 저장 함수
def load_data(sheet_name):
    if gc:
        try: return pd.DataFrame(gc.worksheet(sheet_name).get_all_records())
        except: return pd.DataFrame()
    return pd.DataFrame()

def save_data(sheet_name, df):
    if gc:
        ws = gc.worksheet(sheet_name)
        ws.clear()
        ws.update([df.columns.values.tolist()] + df.values.tolist())

# 데이터 로드
if "data" not in st.session_state:
    st.session_state.data = {
        "등록기업": load_data("등록기업"),
        "지원학생": load_data("지원학생"),
        "합격자": load_data("합격자"),
        "기업분석": load_data("기업분석")
    }

# 3. 다트(DART) 기업 검색 기능
def search_dart_info(corp_name):
    # 실제 API 연동 로직 (필요시 상세 구현)
    st.write(f"🔍 '{corp_name}' 기업 정보를 DART에서 조회 중입니다...")
    # 예시 결과
    return "대기업/상장사 (추정)"

st.sidebar.title("메뉴")
menu = st.sidebar.radio("이동", ["등록 기업 관리", "지원 학생 관리", "합격자 관리", "기업 분석 보고서"])

# --- 각 메뉴별 기존 디자인 및 기능 구현 ---
if menu == "등록 기업 관리":
    st.header("🏢 등록 기업 관리")
    
    # 다트 검색창
    with st.expander("💡 신규 기업 정보 검색 (DART 연동)"):
        search_name = st.text_input("기업명 검색")
        if st.button("검색"):
            info = search_dart_info(search_name)
            st.success(f"검색 결과: {info}")
            
    df = st.data_editor(st.session_state.data["등록기업"], num_rows="dynamic", use_container_width=True)
    if st.button("구글 시트에 저장하기"):
        st.session_state.data["등록기업"] = df
        save_data("등록기업", df)
        st.success("저장 완료!")

elif menu == "지원 학생 관리":
    st.header("👨‍🎓 지원 학생 관리")
    df = st.data_editor(st.session_state.data["지원학생"], num_rows="dynamic", use_container_width=True)
    if st.button("구글 시트에 저장하기"):
        st.session_state.data["지원학생"] = df
        save_data("지원학생", df)
        st.success("저장 완료!")

elif menu == "합격자 관리":
    st.header("🏆 합격자 관리")
    df = st.data_editor(st.session_state.data["합격자"], num_rows="dynamic", use_container_width=True)
    if st.button("구글 시트에 저장하기"):
        st.session_state.data["합격자"] = df
        save_data("합격자", df)
        st.success("저장 완료!")

elif menu == "기업 분석 보고서":
    st.header("📝 기업 분석 보고서 작성")
    with st.form("report_form"):
        c_name = st.text_input("기업명")
        c_content = st.text_area("분석 내용 (강점, 약점, 기회, 위협 등)")
        if st.form_submit_button("보고서 저장"):
            new_rep = pd.DataFrame([{"기업명": c_name, "분석내용": c_content}])
            st.session_state.data["기업분석"] = pd.concat([st.session_state.data["기업분석"], new_rep], ignore_index=True)
            save_data("기업분석", st.session_state.data["기업분석"])
            st.success("보고서가 저장되었습니다!")
            
    st.dataframe(st.session_state.data["기업분석"], use_container_width=True)
