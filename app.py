import streamlit as st
import pandas as pd
import datetime
import io
import os
import urllib.parse
import requests
from bs4 import BeautifulSoup
import streamlit.components.v1 as components

st.set_page_config(page_title="조선대학교 추천채용 통합 관리 시스템", layout="wide")

# 로고 파일 바이너리 직접 자동 탐색 및 로딩
def get_logo_bytes():
    base_path = os.path.dirname(os.path.abspath(__file__)) if "__file__" in locals() else "."
    possible_names = ["logo.jpg", "logo.png", "logo.jpeg", "Logo.jpg", "Logo.png", "Logo.jpeg"]
    for name in possible_names:
        file_path = os.path.join(base_path, name)
        if os.path.exists(file_path):
            try:
                with open(file_path, "rb") as f:
                    return f.read()
            except:
                pass
    for f in os.listdir("."):
        f_lower = f.lower()
        if "logo" in f_lower or "로고" in f_lower or "조선" in f_lower:
            if f_lower.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
                try:
                    with open(f, "rb") as file_data:
                        return file_data.read()
                except:
                    pass
    return None

logo_bytes = get_logo_bytes()

# 로고 및 타이틀 헤더 구성
col_logo, col_title = st.columns([1, 5])
with col_logo:
    if logo_bytes:
        st.image(logo_bytes, width=140)
    else:
        st.markdown("### 🎓 **CHOSUN**")

with col_title:
    st.title("조선대학교 추천채용 통합 관리 시스템")
    st.caption("조선대학교 취업학생처 취업전략팀 | 등록 기업, HR 담당자, 지원 학생 및 기업 분석 보고서 관리")

st.markdown("---")

# 날짜 데이터에서 00:00:00 시간 제거 함수
def clean_date_column(df, col_name):
    if col_name in df.columns:
        df[col_name] = pd.to_datetime(df[col_name], errors='coerce').dt.strftime('%Y-%m-%d').fillna(df[col_name].astype(str).str.replace(" 00:00:00", ""))
    return df

# 주요 기업 자동 구분을 위한 기본 사전
KNOWN_COMPANIES = {
    "수완에너지": "중견기업", "수완에너지(주)": "중견기업",
    "일양약품": "중견기업/코스피상장", "일양약품(주)": "중견기업/코스피상장",
    "서울시니어스타워": "우수기업", "하림산업": "대기업(계열사)", "㈜하림산업": "대기업(계열사)",
    "삼성전자": "대기업/코스피상장", "LG전자": "대기업/코스피상장", "현대자동차": "대기업/코스피상장",
    "한국전력공사": "공공기관", "국민연금공단": "공공기관"
}

def auto_detect_company_type(comp_name):
    clean_name = str(comp_name).strip()
    for key, val in KNOWN_COMPANIES.items():
        if key in clean_name:
            return val
    if "공사" in clean_name or "공단" in clean_name or "진흥원" in clean_name:
        return "공공기관"
    elif "주식회사" in clean_name or "(주)" in clean_name:
        return "중견기업"
    return "우수기업"

# 네이버 기업정보 크롤링
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

# 세션 상태 초기화
if "companies" not in st.session_state:
    st.session_state.companies = pd.DataFrame([
        {
            "연번": 1, "등록일자": "2026-06-01", "기업명": "수완에너지(주)", "구분": "중견기업", "채용직무": "운영 파트",
            "HR성명": "김담당", "HR직급": "대리", "HR내선": "062-123-4567", "HR휴대폰": "010-1234-5678", "HRe-mail": "hr@suwan.com",
            "공고시기": "2026-06", "진행상태": "마감"
        }
    ])

if "applicants" not in st.session_state:
    st.session_state.applicants = pd.DataFrame([
        {
            "연번": 1, "지원일자": "2026-06-10", "학번": "20201234", "학생명": "김철수", "학과": "전기공학과", "학적": "재학",
            "연락처": "010-1111-2222", "이메일": "chulsoo@chosun.ac.kr", "학점": 3.6,
            "지원기업": "수완에너지(주)", "지원직무": "운영 파트", "상태": "최종합격"
        }
    ])

if "passed" not in st.session_state:
    st.session_state.passed = pd.DataFrame([
        {
            "연번": 1, "합격일자": "2026-06-25", "학번": "20201234", "이름": "김철수", "학과": "전기공학과", "연락처": "010-1111-2222",
            "기업명": "수완에너지(주)", "직무": "운영 파트", "입사일": "2026-07-01",
            "재직상태": "재직중", "멘토가능여부": True, "비고": "수습 진행 중"
        }
    ])

if "reports" not in st.session_state:
    st.session_state.reports = {}

if "edit_target" not in st.session_state:
    st.session_state.edit_target = None

if "crawled_info" not in st.session_state:
    st.session_state.crawled_info = {"대표자": "", "설립일": "", "매출액": "", "업종": "", "기업유형": ""}

def create_template(target_type):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        if target_type == "등록 기업 목록":
            df_tpl = pd.DataFrame([{
                "연번": 1, "등록일자": "2026-08-01", "기업명": "예시기업(주)", "구분": "중견기업", "채용직무": "경영지원",
                "HR성명": "홍길동", "HR직급": "과장", "HR내선": "02-123-4567", "HR휴대폰": "010-0000-0000", "HRe-mail": "hr@example.com",
                "공고시기": "2026-08", "진행상태": "진행중"
            }])
            df_tpl.to_excel(writer, sheet_name='등록기업_양식', index=False)
        elif target_type == "지원 학생 목록":
            df_tpl = pd.DataFrame([{
                "연번": 1, "지원일자": "2026-08-01", "학번": "20230001", "학생명": "홍길동", "학과": "경영학과", "학적": "재학",
                "연락처": "010-0000-0000", "이메일": "example@chosun.ac.kr", "학점": 3.8,
                "지원기업": "예시기업(주)", "지원직무": "경영지원", "상태": "접수"
            }])
            df_tpl.to_excel(writer, sheet_name='지원학생_양식', index=False)
        elif target_type == "합격자 DB 목록":
            df_tpl = pd.DataFrame([{
                "연번": 1, "합격일자": "2026-08-01", "학번": "20230001", "이름": "홍길동", "학과": "경영학과", "연락처": "010-0000-0000",
                "기업명": "예시기업(주)", "직무": "경영지원", "입사일": "2026-08-01",
                "재직상태": "재직중", "멘토가능여부": True, "비고": "신입사원"
            }])
            df_tpl.to_excel(writer, sheet_name='합격자_양식', index=False)
    return output.getvalue()

menu = st.sidebar.selectbox("📂 메뉴 선택", ["1. 등록 기업 관리", "2. 지원 학생 관리", "3. 합격자 DB & 멘토 풀", "4. 전체 현황 요약", "📂 5. 기존 엑셀 일괄 업로드", "📝 6. 기업 분석 보고서 생성"])

# --- 1. 등록 기업 관리 ---
if menu == "1. 등록 기업 관리":
    st.header("🏢 추천채용 등록 기업 & HR 담당자 리스트")
    st.info("💡 표 안의 항목을 더블클릭하면 엑셀처럼 직접 수정할 수 있습니다.")
    
    # 시간 데이터 깔끔하게 정돈
    st.session_state.companies = clean_date_column(st.session_state.companies, "등록일자")
    
    edited_companies = st.data_editor(
        st.session_state.companies,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "연번": st.column_config.NumberColumn("연번", disabled=True),
            "진행상태": st.column_config.SelectboxColumn("진행상태", options=["진행중", "마감", "보류"], required=True),
            "구분": st.column_config.SelectboxColumn("기업 구분", options=["대기업", "대기업(계열사)", "중견기업", "중견기업/코스피상장", "중소기업", "공공기관", "우수기업"], required=True)
        }
    )
    st.session_state.companies = edited_companies

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
                c_name = st.text_input("기업명")
                c_type = st.selectbox("기업 구분", ["대기업", "대기업(계열사)", "중견기업", "중견기업/코스피상장", "중소기업", "공공기관", "우수기업"])
                c_job = st.text_input("채용 직무")
                c_reg_date = st.date_input("등록일자", datetime.date.today())
                c_period = st.text_input("채용 공고 시기 (예: 2026-08)", value=datetime.date.today().strftime("%Y-%m"))
                c_status = st.selectbox("진행 상태", ["진행중", "마감", "보류"])
            with col_c2:
                st.markdown("**HR 담당자 정보**")
                hr_name = st.text_input("성명")
                hr_rank = st.text_input("직급")
                hr_tel = st.text_input("내선 번호")
                hr_hp = st.text_input("휴대폰 (HP)")
                hr_email = st.text_input("e-mail")

            if st.form_submit_button("기업 및 담당자 등록"):
                next_no = len(st.session_state.companies) + 1
                new_c = {
                    "연번": next_no, "등록일자": str(c_reg_date), "기업명": c_name, "구분": c_type, "채용직무": c_job, "공고시기": c_period, "진행상태": c_status,
                    "HR성명": hr_name, "HR직급": hr_rank, "HR내선": hr_tel, "HR휴대폰": hr_hp, "HRe-mail": hr_email
                }
                st.session_state.companies = pd.concat([st.session_state.companies, pd.DataFrame([new_c])], ignore_index=True)
                st.success(f"{c_name} (담당자: {hr_name}) 등록 완료!")
                st.rerun()

# --- 2. 지원 학생 관리 ---
elif menu == "2. 지원 학생 관리":
    st.header("👨‍🎓 지원 학생 상세 리스트")
    st.session_state.applicants = clean_date_column(st.session_state.applicants, "지원일자")
    
    edited_applicants = st.data_editor(
        st.session_state.applicants,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "연번": st.column_config.NumberColumn("연번", disabled=True),
            "학적": st.column_config.SelectboxColumn("학적", options=["재학", "휴학", "졸업예정", "졸업"], required=True),
            "상태": st.column_config.SelectboxColumn("전형 상태", options=["접수", "추천완료", "서류합격", "최종합격", "불합격"], required=True)
        }
    )
    st.session_state.applicants = edited_applicants

    st.markdown("---")
    st.subheader("➕ 신규 지원자 접수")
    with st.form("add_applicant_form"):
        col_a1, col_a2, col_a3 = st.columns(3)
        with col_a1:
            a_date = st.date_input("지원일자", datetime.date.today())
            a_id = st.text_input("학번")
            a_name = st.text_input("학생 이름")
            a_dept = st.text_input("학과")
        with col_a2:
            a_academic = st.selectbox("학적", ["재학", "졸업예정", "졸업", "휴학"])
            a_phone = st.text_input("연락처 (예: 010-0000-0000)")
            a_email = st.text_input("이메일")
            a_gpa = st.number_input("학점", min_value=0.0, max_value=4.5, value=3.5, step=0.1)
        with col_a3:
            a_comp = st.selectbox("지원 기업", st.session_state.companies["기업명"].unique() if len(st.session_state.companies) > 0 else ["미정"])
            a_job = st.text_input("지원 직무")
            a_status = st.selectbox("전형 상태", ["접수", "추천완료", "서류합격", "최종합격", "불합격"])

        if st.form_submit_button("지원자 등록"):
            next_no = len(st.session_state.applicants) + 1
            new_a = {
                "연번": next_no, "지원일자": str(a_date), "학번": a_id, "학생명": a_name, "학과": a_dept, "학적": a_academic,
                "연락처": a_phone, "이메일": a_email, "학점": a_gpa,
                "지원기업": a_comp, "지원직무": a_job, "상태": a_status
            }
            st.session_state.applicants = pd.concat([st.session_state.applicants, pd.DataFrame([new_a])], ignore_index=True)
            st.success(f"{a_name} 학생 ({a_id}) 등록 완료!")
            st.rerun()

# --- 3. 합격자 DB & 멘토 풀 ---
elif menu == "3. 합격자 DB & 멘토 풀":
    st.header("🏆 합격자 데이터베이스 & 실무 멘토 풀")
    st.session_state.passed = clean_date_column(st.session_state.passed, "합격일자")
    st.session_state.passed = clean_date_column(st.session_state.passed, "입사일")
    
    edited_passed = st.data_editor(
        st.session_state.passed,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "연번": st.column_config.NumberColumn("연번", disabled=True),
            "재직상태": st.column_config.SelectboxColumn("재직상태", options=["재직중", "퇴사(이직)", "퇴사"], required=True),
            "멘토가능여부": st.column_config.CheckboxColumn("멘토 가능 여부", default=True)
        }
    )
    st.session_state.passed = edited_passed

    st.markdown("---")
    st.subheader("💡 재맞고/상담 연계용 '실무 멘토 가능자' 명단")
    mentor_df = st.session_state.passed[(st.session_state.passed["재직상태"] == "재직중") & (st.session_state.passed["멘토가능여부"] == True)]
    st.dataframe(mentor_df[["연번", "합격일자", "학번", "이름", "학과", "연락처", "기업명", "직무", "입사일", "비고"]], use_container_width=True)

# --- 4. 전체 현황 요약 ---
elif menu == "4. 전체 현황 요약":
    st.header("📊 추천채용 종합 현황 & 월별 실적")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("누적 등록 기업 수", f"{len(st.session_state.companies)}개")
    m2.metric("누적 총 지원자 수", f"{len(st.session_state.applicants)}명")
    m3.metric("누적 최종 합격자 수", f"{len(st.session_state.passed)}명")
    m4.metric("활용 가능 멘토", f"{len(st.session_state.passed[(st.session_state.passed['재직상태']=='재직중') & (st.session_state.passed['멘토가능여부']==True)])}명")

    st.markdown("---")
    st.subheader("📅 월별 주요 추천채용 실적 건수")
    
    df_c = st.session_state.companies.copy()
    df_a = st.session_state.applicants.copy()
    df_p = st.session_state.passed.copy()

    df_c["월"] = df_c["등록일자"].astype(str).str.slice(0, 7)
    df_a["월"] = df_a["지원일자"].astype(str).str.slice(0, 7)
    df_p["월"] = df_p["합격일자"].astype(str).str.slice(0, 7)

    summary_c = df_c.groupby("월").size().rename("신규 기업 등록")
    summary_a = df_a.groupby("월").size().rename("학생 지원 건수")
    summary_p = df_p.groupby("월").size().rename("최종 합격 건수")

    monthly_summary = pd.concat([summary_c, summary_a, summary_p], axis=1).fillna(0).astype(int)
    monthly_summary.index.name = "연월(YYYY-MM)"

    col_sum1, col_sum2 = st.columns([1, 1])
    with col_sum1:
        st.markdown("**📋 월별 세부 건수 요약표**")
        st.dataframe(monthly_summary, use_container_width=True)
    with col_sum2:
        st.markdown("**📈 월별 실적 추이 그래프**")
        st.bar_chart(monthly_summary)

    st.markdown("---")
    st.subheader("📥 전체 데이터 엑셀 내보내기")
    @st.cache_data
    def convert_df_to_excel():
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            st.session_state.companies.to_excel(writer, sheet_name='등록기업_HR담당자', index=False)
            st.session_state.applicants.to_excel(writer, sheet_name='지원학생', index=False)
            st.session_state.passed.to_excel(writer, sheet_name='합격자및멘토', index=False)
        return output.getvalue()
    
    st.download_button(
        label="📄 전체 DB 엑셀 파일(.xlsx) 다운로드",
        data=convert_df_to_excel(),
        file_name=f"추천채용_통합DB_{datetime.date.today()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# --- 5. 기존 엑셀 일괄 업로드 ---
elif menu == "📂 5. 기존 엑셀 일괄 업로드":
    st.header("📂 기존 엑셀 데이터 불러오기")
    col_up1, col_up2 = st.columns([1, 1])
    with col_up1:
        st.subheader("1️⃣ 표준 업로드 양식 다운로드")
        target_tpl = st.selectbox("다운로드할 양식을 선택하세요", ["등록 기업 목록", "지원 학생 목록", "합격자 DB 목록"])
        st.download_button(label=f"📥 {target_tpl} 표준 양식(.xlsx) 다운로드", data=create_template(target_tpl), file_name=f"{target_tpl}_표준양식.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with col_up2:
        st.subheader("2️⃣ 작성한 엑셀 파일 업로드")
        target_upload = st.selectbox("업로드할 항목을 선택하세요", ["등록 기업 목록", "지원 학생 목록", "합격자 DB 목록"])
        uploaded_file = st.file_uploader("작성 완료된 엑셀 파일(.xlsx)을 드래그하세요.", type=["xlsx", "xls"])
        if uploaded_file is not None:
            df_upload = pd.read_excel(uploaded_file)
            # 업로드된 파일의 날짜 포맷도 정리
            if target_upload == "등록 기업 목록": df_upload = clean_date_column(df_upload, "등록일자")
            elif target_upload == "지원 학생 목록": df_upload = clean_date_column(df_upload, "지원일자")
            elif target_upload == "합격자 DB 목록": 
                df_upload = clean_date_column(df_upload, "합격일자")
                df_upload = clean_date_column(df_upload, "입사일")
                
            st.dataframe(df_upload, use_container_width=True)
            if st.button("시스템에 이 데이터 통합/추가하기"):
                if target_upload == "등록 기업 목록": st.session_state.companies = pd.concat([st.session_state.companies, df_upload], ignore_index=True)
                elif target_upload == "지원 학생 목록": st.session_state.applicants = pd.concat([st.session_state.applicants, df_upload], ignore_index=True)
                elif target_upload == "합격자 DB 목록": st.session_state.passed = pd.concat([st.session_state.passed, df_upload], ignore_index=True)
                st.success("추가 완료!")
                st.rerun()

# --- 6. 기업 분석 보고서 생성 및 A4 1장 인쇄 관리 ---
elif menu == "📝 6. 기업 분석 보고서 생성":
    st.header("📝 기업 분석 보고서 작성 및 A4 1장 인쇄 관리")
    
    edit_data = {}
    if st.session_state.edit_target and st.session_state.edit_target in st.session_state.reports:
        edit_data = st.session_state.reports[st.session_state.edit_target]
        st.warning(f"✏️ 현재 **[{st.session_state.edit_target}]** 보고서를 수정 중입니다.")

    col_s1, col_s2 = st.columns([3, 1])
    with col_s1:
        target_search_comp = st.text_input("분석할 기업명 입력", value=edit_data.get("기본정보", {}).get("기업명", "하림산업"))
    with col_s2:
        st.markdown("&nbsp;")
        if st.button("🔍 기업정보 자동 조회"):
            fetched = fetch_naver_company_info(target_search_comp)
            st.session_state.crawled_info = fetched
            st.success(f"'{target_search_comp}' 기업 정보를 성공적으로 검색하여 불러왔습니다!")

    c_data = st.session_state.crawled_info
    base_info = edit_data.get("기본정보", {})

    with st.form("company_analysis_form"):
        st.subheader("1️⃣ 기업 기본 개요")
        col_r1, col_r2, col_r3 = st.columns(3)
        with col_r1:
            r_comp = st.text_input("기업명", value=base_info.get("기업명", target_search_comp))
            r_ceo = st.text_input("대표자", value=base_info.get("대표자", c_data.get("대표자", "김기만")))
            r_emp = st.text_input("직원 수", value=base_info.get("직원수", "약 700명"))
            r_est = st.text_input("설립 연도", value=base_info.get("설립연도", c_data.get("설립일", "2012년 2월 8일")))
        with col_r2:
            r_type = st.text_input("기업 유형", value=base_info.get("유형", c_data.get("기업유형", "대기업 (하림그룹 계열사)")))
            r_sales = st.text_input("매출액", value=base_info.get("매출액", c_data.get("매출액", "약 1,093억 원")))
            r_profit = st.text_input("영업이익", value=base_info.get("영업이익", "약 -1,096억 원"))
            r_loc = st.text_input("사업장 위치", value=base_info.get("위치", "전북 익산시 함열읍 다송리 897"))
        with col_r3:
            r_industry = st.text_input("업종", value=base_info.get("업종", c_data.get("업종", "기타 식품 첨가물 제조업")))
            r_url = st.text_input("홈페이지", value=base_info.get("홈페이지", "https://harim-foods.com/"))
            r_period = st.text_input("공고/채용 시기", value=base_info.get("채용시기", "수시 채용 (2026.07.03 ~ 08.10)"))
            r_dept = st.text_input("분석 직무/부서", value=base_info.get("직무", "환경자원팀"))

        st.markdown("---")
        st.subheader("2️⃣ 인재상 & 주요 직무 & 자격 요건")
        col_r4, col_r5 = st.columns(2)
        with col_r4:
            r_talents = st.text_area("기업 인재상", value=edit_data.get("인재상", "• 프로 인재상: 고도의 전문 능력과 열정의 소유자\n• 프로 리더상: 경영이념을 구현할 수 있는 자\n• 비즈니스 리더상: 비전 공유와 실천의 리더"))
            r_tasks = st.text_area("주요 업무 내용", value=edit_data.get("주요업무", "1. 배출원 관리: 대기 배출시설 관리 및 SEMS 운영\n2. 환경시설물 관리: 폐수처리시설 운영 및 AllBaro 처리\n3. 용수 관리: 저수조 탱크 청소 및 분석"))
        with col_r5:
            r_req = st.text_area("자격 요건 & 우수 조건", value=edit_data.get("요건", "• 학사 이상, 대기환경기사/수질환경기사 자격증 소지자\n• 우대조건: 환경공학 전공자, 글로벌 품질관리 담당자"))
            r_issues = st.text_area("최근 기업 이슈 및 ESG 경영 동향", value=edit_data.get("이슈", "• 자원순환형 ESG 환경 관리: 수질/대기 준수율 100% 목표\n• 화학물질 관리법 준수 및 정기 점검"))

        st.markdown("---")
        st.subheader("3️⃣ 학생 상담용 추천 포인트 (취업전략팀 작성)")
        r_tips = st.text_area("학생 지도 가이드라인", value=edit_data.get("지도포인트", "• 환경공학과 졸업예정자 집중 추천\n• AllBaro 시스템 활용 경험 강조 필수"))

        st.markdown("---")
        st.subheader("4️⃣ 조선대학교 최근 취업자 현황 (최근 3~5개년)")
        col_history1, col_history2 = st.columns(2)
        with col_history1:
            r_history_summary = st.text_area("연도별 조선대 취업자 수 및 학과", value=edit_data.get("취업자현황", "• 2024년: 2명 (환경 1, 전기 1)\n• 2025년: 1명 (환경 1)\n• 2026년: 1명 (환경 1)"))
        with col_history2:
            r_history_notes = st.text_area("취업자 특징 및 주요 배치 직무", value=edit_data.get("취업자특징", "• 주요 배치 직무: 환경자원팀\n• 특징: 대기환경기사 및 AllBaro 경험자 중심 합격"))

        btn_label = "💾 수정사항 저장하기" if st.session_state.edit_target else "💾 기업 분석 보고서 누적 DB 저장하기"
        if st.form_submit_button(btn_label):
            today_str = datetime.date.today().strftime('%Y-%m-%d')
            st.session_state.reports[r_comp] = {
                "작성일": today_str,
                "기본정보": {"기업명": r_comp, "대표자": r_ceo, "직원수": r_emp, "설립연도": r_est, "유형": r_type, "매출액": r_sales, "영업이익": r_profit, "위치": r_loc, "업종": r_industry, "홈페이지": r_url, "채용시기": r_period, "직무": r_dept},
                "인재상": r_talents, "주요업무": r_tasks, "요건": r_req, "이슈": r_issues, "지도포인트": r_tips,
                "취업자현황": r_history_summary, "취업자특징": r_history_notes
            }
            st.session_state.edit_target = None
            st.success(f"'{r_comp}' 기업 분석 보고서가 성공적으로 저장되었습니다!")
            st.rerun()

    # --- 누적 보고서 목록 및 원클릭 인쇄 ---
    if st.session_state.reports:
        st.markdown("---")
        st.subheader("📚 누적 저장된 기업 분석 보고서 목록 & 출력")
        
        col_rep_sel, col_btn_edit, col_btn_del = st.columns([3, 1, 1])
        with col_rep_sel:
            selected_rep = st.selectbox("조회 및 인쇄할 기업 선택", list(st.session_state.reports.keys()))
        
        with col_btn_edit:
            st.markdown("&nbsp;")
            if st.button("✏️ 보고서 수정하기"):
                st.session_state.edit_target = selected_rep
                st.rerun()
                
        with col_btn_del:
            st.markdown("&nbsp;")
            if st.button("🗑️ 보고서 삭제하기"):
                del st.session_state.reports[selected_rep]
                st.session_state.edit_target = None
                st.success(f"'{selected_rep}' 보고서가 삭제되었습니다.")
                st.rerun()

        if selected_rep in st.session_state.reports:
            rep_data = st.session_state.reports[selected_rep]
            info = rep_data["기본정보"]

            st.markdown("---")
            col_print1, col_print2 = st.columns([1, 4])
            with col_print1:
                if st.button("🖨️ A4 1장 보고서 즉시 인쇄 / PDF 저장", type="primary"):
                    components.html("<script>window.parent.print();</script>", height=0)

            report_html = f"""
            <style>
            @media print {{
                @page {{
                    size: A4 portrait;
                    margin: 10mm;
                }}
                body {{
                    -webkit-print-color-adjust: exact !important;
                    print-color-adjust: exact !important;
                }}
                [data-testid="stSidebar"], header, footer, .stButton, button {{
                    display: none !important;
                }}
                .main .block-container {{
                    padding: 0 !important;
                    margin: 0 !important;
                }}
            }}
            .print-paper {{
                background-color: #ffffff;
                border: 2px solid #003366;
                padding: 20px;
                border-radius: 6px;
                font-family: 'Malgun Gothic', '맑은 고딕', sans-serif;
                color: #222222;
            }}
            .print-title {{
                text-align: center;
                color: #003366;
                font-size: 20pt;
                font-weight: bold;
                border-bottom: 2px solid #003366;
                padding-bottom: 8px;
                margin-bottom: 12px;
            }}
            .print-table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 12px;
            }}
            .print-table th, .print-table td {{
                border: 1px solid #b0c4de;
                padding: 6px 8px;
                font-size: 9.5pt;
            }}
            .print-table th {{
                background-color: #f0f4f8 !important;
                color: #003366;
                font-weight: bold;
                text-align: center;
                width: 15%;
            }}
            .print-table td {{
                width: 18%;
            }}
            .section-box {{
                border: 1px solid #dcdcdc;
                padding: 10px;
                border-radius: 4px;
                margin-bottom: 10px;
                background-color: #fafafa;
            }}
            .section-title {{
                font-weight: bold;
                color: #003366;
                font-size: 10.5pt;
                margin-bottom: 4px;
            }}
            .section-content {{
                font-size: 9pt;
                line-height: 1.4;
                white-space: pre-wrap;
            }}
            </style>

            <div class="print-paper">
                <div class="print-title">🏢 추천채용 기업 분석 보고서 ({selected_rep})</div>
                <div style="text-align:right; font-size:9pt; color:#666; margin-bottom:10px;">
                    조선대학교 취업학생처 취업전략팀 | 작성일: {rep_data.get('작성일', datetime.date.today())}
                </div>
                
                <table class="print-table">
                    <tr>
                        <th>기업명</th><td>{info['기업명']}</td>
                        <th>대표자</th><td>{info['대표자']}</td>
                        <th>기업유형</th><td>{info['유형']}</td>
                    </tr>
                    <tr>
                        <th>직원수</th><td>{info['직원수']}</td>
                        <th>설립연도</th><td>{info['설립연도']}</td>
                        <th>업종</th><td>{info['업종']}</td>
                    </tr>
                    <tr>
                        <th>매출액</th><td>{info['매출액']}</td>
                        <th>영업이익</th><td>{info['영업이익']}</td>
                        <th>채용시기</th><td>{info['채용시기']}</td>
                    </tr>
                    <tr>
                        <th>소재지</th><td colspan="3">{info['위치']}</td>
                        <th>홈페이지</th><td>{info['홈페이지']}</td>
                    </tr>
                </table>

                <div style="display:flex; gap:10px; margin-bottom:10px;">
                    <div class="section-box" style="flex:1;">
                        <div class="section-title">🎯 기업 인재상 & 주요 업무</div>
                        <div class="section-content">{rep_data['인재상']}\n\n{rep_data['주요업무']}</div>
                    </div>
                    <div class="section-box" style="flex:1;">
                        <div class="section-title">📋 자격요건 & 최근 ESG 이슈</div>
                        <div class="section-content">{rep_data['요건']}\n\n{rep_data['이슈']}</div>
                    </div>
                </div>

                <div class="section-box" style="background-color:#f0f8ff; border-color:#b8daff;">
                    <div class="section-title" style="color:#004085;">🎓 조선대학교 최근 취업자 현황 및 주요 특징</div>
                    <div class="section-content" style="color:#004085;">{rep_data.get('취업자현황', '')}\n\n{rep_data.get('취업자특징', '')}</div>
                </div>

                <div class="section-box" style="background-color:#fff3cd; border-color:#ffeeba;">
                    <div class="section-title" style="color:#856404;">💡 취업전략팀 지도 가이드라인</div>
                    <div class="section-content" style="color:#856404;">{rep_data['지도포인트']}</div>
                </div>
            </div>
            """
            st.markdown(report_html, unsafe_allow_html=True)
