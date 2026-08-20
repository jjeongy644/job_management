import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="조선대학교 추천채용 통합 관리", layout="wide")

# Secrets에서 인증 정보를 가져와 연결하는 방식
@st.cache_resource
def init_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # GitHub에 파일을 올리지 않고 Streamlit Secrets에서 가져옴
    creds_dict = dict(st.secrets["gcp"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open_by_key("1SWpHQXBHwehSiU_3XNiLnaVGJFtwetWj1MNvRdXYoqQ")

gc = init_google_sheets()

def load_data(sheet_name):
    try: return pd.DataFrame(gc.worksheet(sheet_name).get_all_records())
    except: return pd.DataFrame()

def save_data(sheet_name, df):
    ws = gc.worksheet(sheet_name)
    ws.clear()
    ws.update([df.columns.values.tolist()] + df.values.tolist())

# 기존 기능 유지 (데이터 로드)
if "data" not in st.session_state:
    st.session_state.data = {
        "등록기업": load_data("등록기업"),
        "지원학생": load_data("지원학생"),
        "합격자": load_data("합격자"),
        "기업분석": load_data("기업분석")
    }

st.sidebar.title("메뉴")
menu = st.sidebar.radio("이동", ["등록 기업 관리", "지원 학생 관리", "합격자 관리", "기업 분석 보고서"])

# 기존 디자인 및 저장 기능 전부 포함
if menu == "등록 기업 관리":
    st.header("🏢 등록 기업 관리")
    df = st.data_editor(st.session_state.data["등록기업"], num_rows="dynamic", use_container_width=True)
    if st.button("저장하기"):
        save_data("등록기업", df)
        st.success("데이터가 구글 시트에 저장되었습니다!")

elif menu == "지원 학생 관리":
    st.header("👨‍🎓 지원 학생 관리")
    df = st.data_editor(st.session_state.data["지원학생"], num_rows="dynamic", use_container_width=True)
    if st.button("저장하기"):
        save_data("지원학생", df)
        st.success("데이터가 구글 시트에 저장되었습니다!")

elif menu == "합격자 관리":
    st.header("🏆 합격자 관리")
    df = st.data_editor(st.session_state.data["합격자"], num_rows="dynamic", use_container_width=True)
    if st.button("저장하기"):
        save_data("합격자", df)
        st.success("데이터가 구글 시트에 저장되었습니다!")

elif menu == "기업 분석 보고서":
    st.header("📝 기업 분석 보고서 작성 및 출력")
    with st.form("report_form"):
        c_name = st.text_input("기업명")
        c_content = st.text_area("분석 내용")
        if st.form_submit_button("보고서 저장"):
            new_rep = pd.DataFrame([{"기업명": c_name, "분석내용": c_content}])
            updated_df = pd.concat([st.session_state.data["기업분석"], new_rep], ignore_index=True)
            save_data("기업분석", updated_df)
            st.success("보고서 저장 완료!")
            
    st.dataframe(st.session_state.data["기업분석"], use_container_width=True)
