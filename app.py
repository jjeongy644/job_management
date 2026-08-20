import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

st.set_page_config(page_title="조선대학교 추천채용 통합 관리", layout="wide")

# 1. 인증 설정 (아까 설정한 공유 권한 덕분에 이제 이 코드가 아주 잘 작동할 겁니다)
@st.cache_resource
def init_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_path = "service_account.json"
    if os.path.exists(creds_path):
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
        client = gspread.authorize(creds)
        return client.open_by_key("1SWpHQXBHwehSiU_3XNiLnaVGJFtwetWj1MNvRdXYoqQ")
    return None

gc = init_google_sheets()

# 2. 데이터 불러오기 함수
def load_data(sheet_name):
    if gc:
        try: return pd.DataFrame(gc.worksheet(sheet_name).get_all_records())
        except: return pd.DataFrame()
    return pd.DataFrame()

# 3. 데이터 저장 함수 (이제 이게 다시 작동합니다!)
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

st.sidebar.title("메뉴")
menu = st.sidebar.radio("이동", ["등록 기업 관리", "지원 학생 관리", "합격자 관리", "기업 분석 보고서"])

# --- 각 메뉴별 기능 (원래대로 복구) ---
if menu == "등록 기업 관리":
    st.header("🏢 등록 기업 관리")
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
    st.header("📝 기업 분석 보고서 작성 및 출력")
    with st.form("report_form"):
        c_name = st.text_input("기업명")
        c_content = st.text_area("분석 내용")
        if st.form_submit_button("보고서 저장"):
            new_rep = pd.DataFrame([{"기업명": c_name, "분석내용": c_content}])
            st.session_state.data["기업분석"] = pd.concat([st.session_state.data["기업분석"], new_rep], ignore_index=True)
            save_data("기업분석", st.session_state.data["기업분석"])
            st.success("저장 완료!")
            
    st.subheader("📋 작성된 보고서 목록 및 출력")
    st.dataframe(st.session_state.data["기업분석"], use_container_width=True)
