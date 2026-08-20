import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

st.set_page_config(page_title="조선대학교 추천채용 통합 관리", layout="wide")

# 구글 시트 연결 (이전의 에러를 방지하기 위해 파일 이름 대신 '고유 ID'로 직접 연결합니다)
@st.cache_resource
def init_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_path = "service_account.json"
    if os.path.exists(creds_path):
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
        client = gspread.authorize(creds)
        # 선생님이 알려주신 구글 시트 고유 ID 적용
        return client.open_by_key("1SWpHQXBHwehSiU_3XNiLnaVGJFtwetWj1MNvRdXYoqQ")
    return None

gc = init_google_sheets()

def load_data(sheet_name):
    if gc:
        try: 
            return pd.DataFrame(gc.worksheet(sheet_name).get_all_records())
        except: 
            return pd.DataFrame()
    return pd.DataFrame()

def save_data(sheet_name, df):
    if gc:
        try:
            ws = gc.worksheet(sheet_name)
            ws.clear()
            ws.update([df.columns.values.tolist()] + df.values.tolist())
        except Exception as e:
            st.error(f"저장 중 오류 발생: {e}")

# 데이터 로드 (세션 상태 초기화)
if "data" not in st.session_state:
    st.session_state.data = {
        "등록기업": load_data("등록기업"),
        "지원학생": load_data("지원학생"),
        "합격자": load_data("합격자"),
        "기업분석": load_data("기업분석")
    }

st.sidebar.title("메뉴")
menu = st.sidebar.radio("이동", ["등록 기업 관리", "지원 학생 관리", "합격자 관리", "기업 분석 보고서"])

# --- 1. 등록 기업 관리 ---
if menu == "등록 기업 관리":
    st.header("🏢 등록 기업 관리")
    df = st.data_editor(st.session_state.data["등록기업"], num_rows="dynamic", use_container_width=True)
    if st.button("구글 시트에 저장하기"):
        st.session_state.data["등록기업"] = df
        save_data("등록기업", df)
        st.success("구글 시트(DB)에 안전하게 저장되었습니다!")

# --- 2. 지원 학생 관리 ---
elif menu == "지원 학생 관리":
    st.header("👨‍🎓 지원 학생 관리")
    df = st.data_editor(st.session_state.data["지원학생"], num_rows="dynamic", use_container_width=True)
    if st.button("구글 시트에 저장하기"):
        st.session_state.data["지원학생"] = df
        save_data("지원학생", df)
        st.success("구글 시트(DB)에 안전하게 저장되었습니다!")

# --- 3. 합격자 관리 ---
elif menu == "합격자 관리":
    st.header("🏆 합격자 관리")
    df = st.data_editor(st.session_state.data["합격자"], num_rows="dynamic", use_container_width=True)
    if st.button("구글 시트에 저장하기"):
        st.session_state.data["합격자"] = df
        save_data("합격자", df)
        st.success("구글 시트(DB)에 안전하게 저장되었습니다!")

# --- 4. 기업 분석 보고서 ---
elif menu == "기업 분석 보고서":
    st.header("📝 기업 분석 보고서 작성 및 출력")
    
    with st.form("report_form"):
        c_name = st.text_input("기업명")
        c_content = st.text_area("분석 내용")
        if st.form_submit_button("보고서 저장"):
            if c_name:
                new_rep = pd.DataFrame([{"기업명": c_name, "분석내용": c_content}])
                st.session_state.data["기업분석"] = pd.concat([st.session_state.data["기업분석"], new_rep], ignore_index=True)
                save_data("기업분석", st.session_state.data["기업분석"])
                st.success("보고서가 구글 시트(DB)에 저장되었습니다!")
            else:
                st.warning("기업명을 입력해주세요.")
            
    st.subheader("📋 작성된 보고서 목록 및 출력")
    st.dataframe(st.session_state.data["기업분석"], use_container_width=True)
