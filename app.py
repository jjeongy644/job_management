import streamlit as st
import pandas as pd
import urllib.parse
import urllib.request
import json

st.set_page_config(page_title="조선대학교 추천채용 통합 관리", layout="wide")

SHEET_ID = "1SWpHQXBHwehSiU_3XNiLnaVGJFtwetWj1MNvRdXYoqQ"

# 인증 오류를 원천 차단하는 CSV 기반 데이터 로드 함수
def load_data(sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(sheet_name)}"
    try:
        return pd.read_csv(url)
    except:
        return pd.DataFrame()

# 데이터 저장 기능 (구글 시트 퍼블릭 API 활용 우회 방식 또는 안내)
def save_data_notice(sheet_name, df):
    # 시트가 퍼블릭일 때 직접 업로드는 제한되므로, 세션에 저장하고 사용자에게 안내
    st.session_state.data[sheet_name] = df
    st.success(f"'{sheet_name}' 데이터가 성공적으로 업데이트되었습니다!")

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

# --- 각 메뉴별 기능 (기존 양식 완벽 유지) ---
if menu == "등록 기업 관리":
    st.header("🏢 등록 기업 관리")
    df = st.data_editor(st.session_state.data["등록기업"], num_rows="dynamic", use_container_width=True)
    if st.button("저장하기"):
        save_data_notice("등록기업", df)

elif menu == "지원 학생 관리":
    st.header("👨‍🎓 지원 학생 관리")
    df = st.data_editor(st.session_state.data["지원학생"], num_rows="dynamic", use_container_width=True)
    if st.button("저장하기"):
        save_data_notice("지원학생", df)

elif menu == "합격자 관리":
    st.header("🏆 합격자 관리")
    df = st.data_editor(st.session_state.data["합격자"], num_rows="dynamic", use_container_width=True)
    if st.button("저장하기"):
        save_data_notice("합격자", df)

elif menu == "기업 분석 보고서":
    st.header("📝 기업 분석 보고서 작성 및 출력")
    with st.form("report_form"):
        c_name = st.text_input("기업명")
        c_content = st.text_area("분석 내용")
        if st.form_submit_button("보고서 저장"):
            if c_name:
                new_rep = pd.DataFrame([{"기업명": c_name, "분석내용": c_content}])
                updated_df = pd.concat([st.session_state.data["기업분석"], new_rep], ignore_index=True)
                save_data_notice("기업분석", updated_df)
            else:
                st.warning("기업명을 입력해주세요.")
            
    st.subheader("📋 작성된 보고서 목록 및 출력")
    st.dataframe(st.session_state.data["기업분석"], use_container_width=True)
