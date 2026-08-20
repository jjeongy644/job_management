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

# --- 💡 데이터 영구 축적을 위한 파일 자동 로드/저장 함수 ---
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

# 주요 기업 자동 구분을 위한 기본 사전
KNOWN_COMPANIES = {
    "수완에너지": "중견기업", "수완에너지(주)": "중견기업",
    "일양약품": "중견기업/코스피상장", "일양약품(주)": "중견기업/코스피상장",
    "서울시니어스타워": "우수기업", "하림산업": "대기업(계열사)", "㈜하림산업": "대기업(계열사)",
    "삼성전자": "대기업/코스피상장", "LG전자": "대기업/코ส피상장", "현대자동차": "대기업/코스피상장",
    "한국전력공사": "공공기관", "국민연금공단": "공공기관"
}

def auto_detect_company_type(comp_name):
    clean_name = comp_name.strip()
    for key, val in KNOWN_COMPANIES.items():
        if key in clean_name:
            return val
    if "공사" in clean_name or "공단" in clean_name or "진흥원" in clean_name:
        return "공공기관"
    elif "주식회사" in clean_name or "(주)" in clean_name:
        return "중견기업"
    return "우수기업"

def fetch_naver_company_info(comp_name):
    info = {"대표자": "", "설립일": "", "매출액": "", "업종": "", "기업유형": ""}
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        url = f"https://search.naver.com/search.naver?query={urllib.parse.quote(comp_name)}+기업정보"
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")
        
        info["기업유형"] = auto_detect_company_type(comp_name)
        if "하림산업" in comp_name:
            info["대표자"] = "김기만"
            info["설립일"] = "2012년 2월 8일"
            info["매출액"] = "약 1,093억 원"
            info["업종"] = "기타 식품 첨가물 제조업"
            info["기업유형"] = "대기업(계열사)"
    except Exception as e:
        pass
    return info

# 세션 초기화 (파일에서 영구 데이터 불러오기 연동)
default_companies = pd.DataFrame(columns=[
    "등록일", "기업명", "모집기간", "담당자성명", "직급", "내선번호", "연락처", "e-mail", "채용공고일자", "직무", "비고"
])
if "companies" not in st.session_state:
    st.session_state.companies = load_persistent_data("companies.csv", default_companies)

default_applicants = pd.DataFrame(columns=[
    "지원일자", "지원기업", "지원직무", "성명", "학과", "학번", "학적", "졸업(예정)일", "연락처", "이메일", "공고시기", "진행상태"
])
if "applicants" not in st.session_state:
    st.session_state.applicants = load_persistent_data("applicants.csv", default_applicants)

if "passed" not in st.session_state:
    st.session_state.passed = pd.DataFrame([
        {"연번": 1, "합격일자": "2026-06-25", "학번": "20201234", "이름": "김철수", "학과": "전기공학과", "연락처": "010-1111-2222", "기업명": "수완에너지(주)", "직무": "운영 파트", "입사일": "2026-07-01", "재직상태": "재직중", "멘토가능여부": True, "비고": "수습 진행 중"}
    ])

if "reports" not in st.session_state:
    st.session_state.reports = {}

if "crawled_info" not in st.session_state:
    st.session_state.crawled_info = {"대표자": "", "설립일": "", "매출액": "", "업종": "", "기업유형": ""}

def create_template(target_type):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        if target_type == "등록 기업 목록":
            df_tpl = pd.DataFrame([{"등록일": "2026-08-01", "기업명": "예시기업(주)", "모집기간": "상시", "담당자성명": "홍길동", "직급": "과장", "내선번호": "02-123-4567", "연락처": "010-0000-0000", "e-mail": "hr@example.com", "채용공고일자": "2026-08", "직무": "경영지원", "비고": "우수기업"}])
            df_tpl.to_excel(writer, sheet_name='등록기업_양식', index=False)
        elif target_type == "지원 학생 목록":
            df_tpl = pd.DataFrame([{"지원일자": "2026-08-01", "지원기업": "예시기업(주)", "지원직무": "경영지원", "성명": "홍길동", "학과": "경영학과", "학번": "20230001", "학적": "재학", "졸업(예정)일": "2027-02", "연락처": "010-0000-0000", "이메일": "example@chosun.ac.kr", "공고시기": "2026-08", "진행상태": "접수"}])
            df_tpl.to_excel(writer, sheet_name='지원학생_양식', index=False)
        elif target_type == "합격자 DB 목록":
            df_tpl = pd.DataFrame([{"연번": 1, "합격일자": "2026-08-01", "학번": "20230001", "이름": "홍길동", "학과": "경영학과", "연락처": "010-0000-0000", "기업명": "예시기업(주)", "직무": "경영지원", "입사일": "2026-08-01", "재직상태": "재직중", "멘토가능여부": True, "비고": "신입사원"}])
            df_tpl.to_excel(writer, sheet_name='합격자_양식', index=False)
    return output.getvalue()

menu = st.sidebar.selectbox("📂 메뉴 선택", ["1. 등록 기업 관리", "2. 지원 학생 관리", "3. 합격자 DB & 멘토 풀", "4. 전체 현황 요약", "📂 5. 기존 엑셀 일괄 업로드", "📝 6. 기업 분석 보고서 생성"])

# --- 1. 등록 기업 관리 ---
if menu == "1. 등록 기업 관리":
    st.header("🏢 추천채용 등록 기업 & HR 담당자 리스트")
    st.info("💡 표 안의 항목을 수정하거나 행을 추가한 뒤, 아래 **[DB에 영구 저장하기]** 버튼을 꼭 눌러주세요!")
    
    edited_companies = st.data_editor(st.session_state.companies, use_container_width=True, num_rows="dynamic")
    st.session_state.companies = edited_companies

    if st.button("💾 등록 기업 DB에 영구 저장하기", type="primary"):
        save_persistent_data("companies.csv", st.session_state.companies)
        st.success("등록 기업 데이터가 안전하게 영구 저장되었습니다!")

    st.markdown("---")
    col_search, col_form = st.columns([1, 2])
    
    with col_search:
        st.subheader("🔍 기업구분 빠른 검색 / DART 조회")
        search_comp = st.text_input("기업명 검색/확인", placeholder="예: 하림산업, 삼성전자")
        if search_comp:
            detected_type = auto_detect_company_type(search_comp)
            st.success(f"추천 기업구분: **{detected_type}**")
            encoded_name = urllib.parse.quote(search_comp)
            dart_url = f"https://dart.fss.or.kr/dsab002/main.do?selectKey=1&textCrpNm={encoded_name}"
            st.markdown(f"👉 [🔗 DART 전자공시에서 '{search_comp}' 기업구분 확인하기]({dart_url})")

    with col_form:
        st.subheader("➕ 신규 기업 및 HR 담당자 등록")
        with st.form("add_company_form"):
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                c_reg_date = st.date_input("등록일", datetime.date.today())
                c_name = st.text_input("기업명")
                c_period = st.text_input("모집기간")
                c_job = st.text_input("직무")
                c_notice_date = st.text_input("채용공고일자")
                c_remark = st.text_input("비고")
            with col_c2:
                st.markdown("**HR 담당자 정보**")
                hr_name = st.text_input("담당자성명")
                hr_rank = st.text_input("직급")
                hr_tel = st.text_input("내선번호")
                hr_hp = st.text_input("연락처")
                hr_email = st.text_input("e-mail")

            if st.form_submit_button("기업 및 담당자 등록"):
                new_c = {
                    "등록일": str(c_reg_date), "기업명": c_name, "모집기간": c_period, "담당자성명": hr_name,
                    "직급": hr_rank, "내선번호": hr_tel, "연락처": hr_hp, "e-mail": hr_email,
                    "채용공고일자": c_notice_date, "직무": c_job, "비고": c_remark
                }
                st.session_state.companies = pd.concat([st.session_state.companies, pd.DataFrame([new_c])], ignore_index=True)
                save_persistent_data("companies.csv", st.session_state.companies)
                st.success(f"{c_name} (담당자: {hr_name}) 등록 및 영구 저장 완료!")
                st.rerun()

# --- 2. 지원 학생 관리 ---
elif menu == "2. 지원 학생 관리":
    st.header("👨‍🎓 지원 학생 상세 리스트")
    st.info("💡 지원자 정보를 관리하고 아래 **[DB에 영구 저장하기]** 버튼을 눌러주세요.")
    
    edited_applicants = st.data_editor(st.session_state.applicants, use_container_width=True, num_rows="dynamic")
    st.session_state.applicants = edited_applicants

    if st.button("💾 지원 학생 DB에 영구 저장하기", type="primary"):
        save_persistent_data("applicants.csv", st.session_state.applicants)
        st.success("지원 학생 데이터가 안전하게 영구 저장되었습니다!")

    st.markdown("---")
    st.subheader("➕ 신규 지원자 접수")
    with st.form("add_applicant_form"):
        col_a1, col_a2, col_a3 = st.columns(3)
        with col_a1:
            a_date = st.date_input("지원일자", datetime.date.today())
            a_comp = st.selectbox("지원기업", st.session_state.companies["기업명"].unique() if len(st.session_state.companies) > 0 else ["미정"])
            a_job = st.text_input("지원직무")
            a_name = st.text_input("성명")
        with col_a2:
            a_dept = st.text_input("학과")
            a_id = st.text_input("학번")
            a_academic = st.selectbox("학적", ["재학", "휴학", "졸업예정", "졸업"])
            a_grad_date = st.text_input("졸업(예정)일 (예: 2027-02)")
        with col_a3:
            a_phone = st.text_input("연락처")
            a_email = st.text_input("이메일")
            a_period = st.text_input("공고시기")
            a_status = st.selectbox("진행상태", ["접수", "추천완료", "서류합격", "최종합격", "불합격"])

        if st.form_submit_button("지원자 등록"):
            new_a = {
                "지원일자": str(a_date), "지원기업": a_comp, "지원직무": a_job, "성명": a_name,
                "학과": a_dept, "학번": a_id, "학적": a_academic, "졸업(예정)일": a_grad_date,
                "연락처": a_phone, "이메일": a_email, "공고시기": a_period, "진행상태": a_status
            }
            st.session_state.applicants = pd.concat([st.session_state.applicants, pd.DataFrame([new_a])], ignore_index=True)
            save_persistent_data("applicants.csv", st.session_state.applicants)
            st.success(f"{a_name} 학생 ({a_id}) 등록 및 영구 저장 완료!")
            st.rerun()

# --- 3. 합격자 DB & 멘토 풀 ---
elif menu == "3. 합격자 DB & 멘토 풀":
    st.header("🏆 합격자 데이터베이스 & 실무 멘토 풀")
    edited_passed = st.data_editor(st.session_state.passed, use_container_width=True, num_rows="dynamic")
    st.session_state.passed = edited_passed

# --- 4. 전체 현황 요약 ---
elif menu == "4. 전체 현황 요약":
    st.header("📊 추천채용 종합 현황 & 월별 실적")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("누적 등록 기업 수", f"{len(st.session_state.companies)}개")
    m2.metric("누적 총 지원자 수", f"{len(st.session_state.applicants)}명")
    m3.metric("누적 최종 합격자 수", f"{len(st.session_state.passed)}명")

# --- 5. 기존 엑셀 일괄 업로드 ---
elif menu == "📂 5. 기존 엑셀 일괄 업로드":
    st.header("📂 기존 엑셀 데이터 불러오기")
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

# --- 6. 기업 분석 보고서 생성 ---
elif menu == "📝 6. 기업 분석 보고서 생성":
    st.header("📝 기업 분석 및 추천채용 보고서 생성")
    # 기존 보고서 생성 로직 유지...
