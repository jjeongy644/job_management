import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="조선대학교 추천채용 통합 관리", layout="wide")

# 1. 시트 연결 (Secrets 활용)
@st.cache_resource
def init_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    secrets_dict = dict(st.secrets["connections"]["gsheets"])
    creds = Credentials.from_service_account_info(secrets_dict, scopes=scope)
    client = gspread.authorize(creds)
    return client.open_by_key("1SWpHQXBHwehSiU_3XNiLnaVGJFtwetWj1MNvRdXYoqQ")

gc = init_google_sheets()

# 2. 데이터 불러오기 (시트의 첫 행이 비어있어도 컬럼이 잘 잡히도록 처리)
def load_data(sheet_name):
    if gc:
        try:
            ws = gc.worksheet(sheet_name)
            data = ws.get_all_records()
            if data:
                return pd.DataFrame(data)
            else:
                # 데이터가 비어있을 경우 기본 컬럼 설정
                if sheet_name == "등록기업":
                    return pd.DataFrame(columns=["기업명", "담당자", "연락처", "채용분야", "비고"])
                elif sheet_name == "지원학생":
                    return pd.DataFrame(columns=["학번", "이름", "지원기업", "전화번호", "상태"])
                elif sheet_name == "합격자":
                    return pd.DataFrame(columns=["학번", "이름", "합격기업", "합격일자"])
                else:
                    return pd.DataFrame(columns=["기업명", "분석내용"])
        except Exception as e:
            return pd.DataFrame()
    return pd.DataFrame()

# 3. 데이터 저장하기 (수정된 표 내용을 구글 시트에 통째로 덮어쓰기)
def save_data(sheet_name, df):
    if gc:
        try:
            ws = gc.worksheet(sheet_name)
            ws.clear()
            # 데이터프레임이 비어있지 않다면 컬럼명과 데이터를 함께 업로드
            if not df.empty:
                ws.update([df.columns.values.tolist()] + df.values.tolist())
            else:
                ws.update([df.columns.values.tolist()])
        except Exception as e:
            st.error(f"저장 중 오류 발생: {e}")

# 세션 상태에 데이터 적재
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
    st.info("표 안을 자유롭게 더블클릭해서 수정하거나, 아래 빈 행을 눌러 새 기업을 추가할 수 있습니다.")
    
    df = st.data_editor(st.session_state.data["등록기업"], num_rows="dynamic", use_container_width=True)
    
    if st.button("구글 시트에 저장하기", type="primary"):
        st.session_state.data["등록기업"] = df
        save_data("등록기업", df)
        st.success("구글 시트에 안전하게 저장되었습니다!")

# --- 2. 지원 학생 관리 ---
elif menu == "지원 학생 관리":
    st.header("👨‍🎓 지원 학생 관리")
    st.info("학생 정보를 자유롭게 입력·수정하고 저장 버튼을 눌러주세요.")
    
    df = st.data_editor(st.session_state.data["지원학생"], num_rows="dynamic", use_container_width=True)
    
    if st.button("구글 시트에 저장하기", type="primary"):
        st.session_state.data["지원학생"] = df
        save_data("지원학생", df)
        st.success("구글 시트에 안전하게 저장되었습니다!")

# --- 3. 합격자 관리 ---
elif menu == "합격자 관리":
    st.header("🏆 합격자 관리")
    st.info("합격자 현황을 관리하고 저장하세요.")
    
    df = st.data_editor(st.session_state.data["합격자"], num_rows="dynamic", use_container_width=True)
    
    if st.button("구글 시트에 저장하기", type="primary"):
        st.session_state.data["합격자"] = df
        save_data("합격자", df)
        st.success("구글 시트에 안전하게 저장되었습니다!")

# --- 4. 기업 분석 보고서 ---
elif menu == "기업 분석 보고서":
    st.header("📝 기업 분석 보고서 작성 및 출력")
    
    with st.form("report_form"):
        c_name = st.text_input("기업명")
        c_content = st.text_area("분석 내용")
        submitted = st.form_submit_button("보고서 저장")
        
        if submitted:
            if c_name:
                new_rep = pd.DataFrame([{"기업명": c_name, "분석내용": c_content}])
                updated_df = pd.concat([st.session_state.data["기업분석"], new_rep], ignore_index=True)
                st.session_state.data["기업분석"] = updated_df
                save_data("기업분석", updated_df)
                st.success("보고서가 구글 시트에 저장되었습니다!")
            else:
                st.warning("기업명을 입력해주세요.")
            
    st.subheader("📋 작성된 보고서 목록 및 출력")
    st.dataframe(st.session_state.data["기업분석"], use_container_width=True)
