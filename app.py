import streamlit as st
import pandas as pd
import datetime
import io
import os
import urllib.parse
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="조선대학교 추천채용 통합 관리 시스템", layout="wide")

# 로고 파일 자동 감지
def get_logo_path():
    files = os.listdir(".") if os.path.exists(".") else []
    for f in files:
        f_lower = f.lower()
        if f_lower.startswith("logo") or "로고" in f_lower or "조선" in f_lower:
            if f_lower.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
                return f
    return None

logo_file = get_logo_path()

col_logo, col_title = st.columns([1, 5])
with col_logo:
    if logo_file:
        st.image(logo_file, width=140)
    else:
        st.markdown("### 🎓 **CHOSUN**")

with col_title:
    st.title("조선대학교 추천채용 통합 관리 시스템")
    st.caption("조선대학교 취업학생처 취업전략팀 | 등록 기업, HR 담당자, 지원 학생 및 기업 분석 보고서 관리")

st.markdown("---")

# --- 데이터 영구 축적을 위한 파일 자동 로드/저장 함수 ---
DATA_DIR = "saved_data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def load_persistent_data(filename, default_df):
    filepath = os.path.join(DATA_DIR, filename)
    if os.path.exists(filepath):
        try:
            return pd.read_csv(filepath)
        except:
            return default_df
    return default_df

def save_persistent_data(filename, df):
    filepath = os.path.join(DATA_DIR, filename)
    df.to_csv(filepath, index=False)

# --- 템플릿 생성 함수 (필수 항목 반영) ---
def create_template(target_type):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        if target_type == "등록 기업 목록":
            df_tpl = pd.DataFrame(columns=["등록일", "기업명", "모집기간", "담당자성명", "직급", "내선번호", "연락처", "e-mail", "채용공고일자", "직무", "비고"])
            df_tpl.to_excel(writer, sheet_name='등록기업_양식', index=False)
        elif target_type == "지원 학생 목록":
            df_tpl = pd.DataFrame(columns=["지원일자", "지원기업", "지원직무", "성명", "학과", "학번", "학적", "졸업(예정)일", "연락처", "이메일", "공고시기", "진행상태"])
            df_tpl.to_excel(writer, sheet_name='지원학생_양식', index=False)
    return output.getvalue()

# [기존 로직 유지...]
# (중략: 위에서 사용한 세션 상태 초기화 및 네이버 크롤링 등 로직은 동일)
# [기존과 동일하므로 생략 - 전체 코드 복사 시 위쪽의 완전한 코드를 참조하세요]

# --- 5. 기존 엑셀 일괄 업로드 (복구 완료) ---
elif menu == "📂 5. 기존 엑셀 일괄 업로드":
    st.header("📂 기존 엑셀 데이터 불러오기")
    col_up1, col_up2 = st.columns([1, 1])
    with col_up1:
        st.subheader("1️⃣ 표준 업로드 양식 다운로드")
        target_tpl = st.selectbox("다운로드할 양식을 선택하세요", ["등록 기업 목록", "지원 학생 목록"])
        st.download_button(
            label=f"📥 {target_tpl} 표준 양식(.xlsx) 다운로드", 
            data=create_template(target_tpl), 
            file_name=f"{target_tpl}_표준양식.xlsx", 
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    with col_up2:
        st.subheader("2️⃣ 작성한 엑셀 파일 업로드")
        target_upload = st.selectbox("업로드할 항목을 선택하세요", ["등록 기업 목록", "지원 학생 목록"])
        uploaded_file = st.file_uploader("작성 완료된 엑셀 파일(.xlsx)을 드래그하세요.", type=["xlsx", "xls"])
        if uploaded_file is not None:
            df_upload = pd.read_excel(uploaded_file)
            st.dataframe(df_upload, use_container_width=True)
            if st.button("시스템에 이 데이터 통합 및 영구 저장하기"):
                if target_upload == "등록 기업 목록":
                    st.session_state.companies = pd.concat([st.session_state.companies, df_upload], ignore_index=True)
                    save_persistent_data("companies.csv", st.session_state.companies)
                elif target_upload == "지원 학생 목록":
                    st.session_state.applicants = pd.concat([st.session_state.applicants, df_upload], ignore_index=True)
                    save_persistent_data("applicants.csv", st.session_state.applicants)
                st.success("데이터 통합 및 영구 저장 완료!")
                st.rerun()
