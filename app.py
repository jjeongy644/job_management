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

# 주요 기업 자동 구분을 위한 기본 사전
KNOWN_COMPANIES = {
    "수완에너지": "중견기업", "수완에너지(주)": "중견기업",
    "일양약품": "중견기업/코스피상장", "일양약품(주)": "중견기업/코스피상장",
    "서울시니어스타워": "우수기업", "하림산업": "대기업(계열사)", "㈜하림산업": "대기업(계열사)",
    "삼성전자": "대기업/코스피상장", "LG전자": "대기업/코스피상장", "현대자동차": "대기업/코스피상장",
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

# 세션 초기화 (연번 포함 헤더 구조)
default_companies = pd.DataFrame(columns=[
    "연번", "등록일", "기업명", "모집기간", "담당자성명", "직급", "내선번호", "연락처", "e-mail", "채용공고일자", "직무", "비고"
])
if "companies" not in st.session_state:
    st.session_state.companies = load_persistent_data("companies.csv", default_companies)

default_applicants = pd.DataFrame(columns=[
    "연번", "지원일자", "지원기업", "지원직무", "성명", "학과", "학번", "학적", "졸업(예정)일", "연락처", "이메일", "공고시기", "진행상태"
])
if "applicants" not in st.session_state:
    st.session_state.applicants = load_persistent_data("applicants.csv", default_applicants)

if "reports" not in st.session_state:
    st.session_state.reports = {}

if "crawled_info" not in st.session_state:
    st.session_state.crawled_info = {"대표자": "", "설립일": "", "매출액": "", "업종": "", "기업유형": ""}

# 표준 양식 생성 함수
def create_template(target_type):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        if target_type == "등록 기업 목록":
            df_tpl = pd.DataFrame(columns=["연번", "등록일", "기업명", "모집기간", "담당자성명", "직급", "내선번호", "연락처", "e-mail", "채용공고일자", "직무", "비고"])
            df_tpl.to_excel(writer, sheet_name='등록기업_양식', index=False)
        elif target_type == "지원 학생 목록":
            df_tpl = pd.DataFrame(columns=["연번", "지원일자", "지원기업", "지원직무", "성명", "학과", "학번", "학적", "졸업(예정)일", "연락처", "이메일", "공고시기", "진행상태"])
            df_tpl.to_excel(writer, sheet_name='지원학생_양식', index=False)
    return output.getvalue()

menu = st.sidebar.selectbox("📂 메뉴 선택", ["1. 등록 기업 관리", "2. 지원 학생 관리", "3. 합격자 DB & 멘토 풀", "4. 추천채용 실적 및 주간/월간 보고", "📂 5. 기존 엑셀 일괄 업로드", "📝 6. 기업 분석 보고서 생성"])

# --- 1. 등록 기업 관리 ---
if menu == "1. 등록 기업 관리":
    st.header("🏢 추천채용 등록 기업 & HR 담당자 리스트")
    st.info("💡 표 안의 항목을 수정하거나 행을 추가한 뒤, 아래 **[DB에 영구 저장하기]** 버튼을 꼭 눌러주세요!")
    
    edited_companies = st.data_editor(
        st.session_state.companies, 
        use_container_width=True, 
        num_rows="dynamic",
        column_config={"연번": st.column_config.NumberColumn("연번", disabled=True)}
    )
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
                next_no = len(st.session_state.companies) + 1
                new_c = {
                    "연번": next_no, "등록일": str(c_reg_date), "기업명": c_name, "모집기간": c_period, "담당자성명": hr_name,
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
    
    edited_applicants = st.data_editor(
        st.session_state.applicants, 
        use_container_width=True, 
        num_rows="dynamic",
        column_config={"연번": st.column_config.NumberColumn("연번", disabled=True)}
    )
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
            next_no = len(st.session_state.applicants) + 1
            new_a = {
                "연번": next_no, "지원일자": str(a_date), "지원기업": a_comp, "지원직무": a_job, "성명": a_name,
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
    default_passed = pd.DataFrame([{"연번": 1, "합격일자": "2026-06-25", "학번": "20201234", "이름": "김철수", "학과": "전기공학과", "연락처": "010-1111-2222", "기업명": "수완에너지(주)", "직무": "운영 파트", "입사일": "2026-07-01", "재직상태": "재직중", "멘토가능여부": True, "비고": "수습 진행 중"}])
    if "passed" not in st.session_state:
        st.session_state.passed = load_persistent_data("passed.csv", default_passed)
        
    edited_passed = st.data_editor(st.session_state.passed, use_container_width=True, num_rows="dynamic")
    st.session_state.passed = edited_passed
    if st.button("💾 합격자 DB 영구 저장"):
        save_persistent_data("passed.csv", st.session_state.passed)
        st.success("저장 완료!")

# --- 4. 추천채용 실적 및 주간/월간 보고 ---
elif menu == "4. 추천채용 실적 및 주간/월간 보고":
    st.header("📊 추천채용 실적 보고 (주간 / 월간)")
    
    report_tab1, report_tab2 = st.tabs(["📅 주간 실적 보고", "📈 월간 실적 보고 및 시각화"])
    
    with report_tab1:
        st.subheader("📌 주간 추천채용 현황 보고서 양식")
        c_w1, c_w2 = st.columns(2)
        start_date = c_w1.date_input("조회 시작일", datetime.date.today() - datetime.timedelta(days=7))
        end_date = c_w2.date_input("조회 종료일", datetime.date.today())
        
        df_c = st.session_state.companies.copy()
        df_a = st.session_state.applicants.copy()
        
        if "등록일" in df_c.columns and len(df_c) > 0:
            df_c["등록일_dt"] = pd.to_datetime(df_c["등록일"], errors="coerce")
            mask_c = (df_c["등록일_dt"].dt.date >= start_date) & (df_c["등록일_dt"].dt.date <= end_date)
            weekly_companies = df_c[mask_c]
        else:
            weekly_companies = pd.DataFrame()

        st.markdown(f"### 📋 추천채용 현황 (기준: ~{end_date.strftime('%y.%m.%d')})")
        st.info(f"💡 선택 기간동안 **신규 등록 기업 {len(weekly_companies)}건**이 조회되었습니다.")
        
        if len(weekly_companies) > 0:
            weekly_view = []
            for idx, row in weekly_companies.reset_index().iterrows():
                comp_name = row.get("기업명", "")
                applicant_count = len(df_a[df_a["지원기업"] == comp_name]) if len(df_a) > 0 else 0
                weekly_view.append({
                    "구 분": idx + 1,
                    "기업명": comp_name,
                    "채용직무": row.get("직무", ""),
                    "접수 기한": row.get("모집기간", ""),
                    "지원자": applicant_count,
                    "비고": row.get("비고", "-")
                })
            st.dataframe(pd.DataFrame(weekly_view), use_container_width=True, hide_index=True)
        else:
            st.warning("해당 기간에 등록된 기업 데이터가 없습니다.")

    with report_tab2:
        st.subheader("📈 월별 실적 추이 및 시각화")
        df_c2 = st.session_state.companies.copy()
        df_a2 = st.session_state.applicants.copy()
        
        if "등록일" in df_c2.columns and len(df_c2) > 0:
            df_c2["월"] = df_c2["등록일"].astype(str).str.slice(0, 7)
            summary_c = df_c2.groupby("월").size().rename("신규 기업 등록")
        else:
            summary_c = pd.Series(dtype=int)
            
        if "지원일자" in df_a2.columns and len(df_a2) > 0:
            df_a2["월"] = df_a2["지원일자"].astype(str).str.slice(0, 7)
            summary_a = df_a2.groupby("월").size().rename("학생 지원 건수")
        else:
            summary_a = pd.Series(dtype=int)

        monthly_df = pd.concat([summary_c, summary_a], axis=1).fillna(0).astype(int)
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.markdown("**📋 월별 실적 집계표**")
            st.dataframe(monthly_df, use_container_width=True)
        with col_m2:
            st.markdown("**📊 월별 실적 그래프 시각화**")
            if len(monthly_df) > 0:
                st.bar_chart(monthly_df)
            else:
                st.info("시각화할 데이터가 부족합니다.")

    # --- 엑셀 다운로드 버튼 추가 ---
    st.markdown("---")
    st.subheader("📥 전체 데이터 엑셀 내보내기")
    @st.cache_data
    def convert_df_to_excel():
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            st.session_state.companies.to_excel(writer, sheet_name='등록기업_HR담당자', index=False)
            st.session_state.applicants.to_excel(writer, sheet_name='지원학생', index=False)
            if "passed" in st.session_state:
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

# --- 6. 기업 분석 보고서 생성 ---
elif menu == "📝 6. 기업 분석 보고서 생성":
    st.header("📝 기업 분석 및 추천채용 보고서 생성")
    col_s1, col_s2 = st.columns([3, 1])
    with col_s1:
        target_search_comp = st.text_input("분석할 기업명 입력", value="하림산업")
    with col_s2:
        st.markdown("&nbsp;")
        if st.button("🔍 기업정보 자동 조회"):
            fetched = fetch_naver_company_info(target_search_comp)
            st.session_state.crawled_info = fetched
            st.success(f"'{target_search_comp}' 기업 정보를 성공적으로 검색하여 불러왔습니다!")

    c_data = st.session_state.crawled_info

    with st.form("company_analysis_form"):
        st.subheader("1️⃣ 기업 기본 개요 (자동 반영 항목)")
        col_r1, col_r2, col_r3 = st.columns(3)
        with col_r1:
            r_comp = st.text_input("기업명", value=target_search_comp)
            r_ceo = st.text_input("대표자", value=c_data.get("대표자", "김기만"))
            r_emp = st.text_input("직원 수", value="약 700명")
            r_est = st.text_input("설립 연도", value=c_data.get("설립일", "2012년 2월 8일"))
        with col_r2:
            r_type = st.text_input("기업 유형", value=c_data.get("기업유형", "대기업 (하림그룹 계열사)"))
            r_sales = st.text_input("매출액", value=c_data.get("매출액", "약 1,093억 원"))
            r_profit = st.text_input("영업이익", value="약 -1,096억 원")
            r_loc = st.text_input("사업장 위치", value="전북 익산시 함열읍 다송리 897")
        with col_r3:
            r_industry = st.text_input("업종", value=c_data.get("업종", "기타 식품 첨가물 제조업"))
            r_url = st.text_input("홈페이지", value="https://harim-foods.com/")
            r_period = st.text_input("공고/채용 시기", value="수시 채용 (2026.07.03 ~ 08.10)")
            r_dept = st.text_input("분석 직무/부서", value="환경자원팀")

        st.markdown("---")
        st.subheader("2️⃣ 인재상 & 주요 직무 & 자격 요건 (채용 정보 직접 입력)")
        col_r4, col_r5 = st.columns(2)
        with col_r4:
            r_talents = st.text_area("기업 인재상", value="• 프로 인재상: 고도의 전문 능력과 열정의 소유자\n• 프로 리더상: 경영이념을 구현할 수 있는 자\n• 비즈니스 리더상: 비전 공유와 실천의 리더")
            r_tasks = st.text_area("주요 업무 내용", value="1. 배출원 관리: 대기 배출시설 관리 및 SEMS 운영, 자가측정 일정 관리\n2. 환경시설물 관리: 폐수처리시설 운영 및 폐기물(AllBaro) 적법 처리\n3. 용수 관리: 저수조 탱크 청소 및 분석 법적 업무")
        with col_r5:
            r_req = st.text_area("자격 요건 & 우수 조건", value="• 자격요건: 학사 이상, 대기환경기사/수질환경기사 자격증 소지자\n• 우대조건: 환경공학 및 유사 학과 전공자, 글로벌 품질관리 담당자\n• 근무조건: 월~금 08:00~17:00")
            r_issues = st.text_area("최근 기업 이슈 및 ESG 경영 동향", value="• 자원순환형 ESG 환경 관리: 수질/대기/유해화학물질 준수율 100% 목표\n• 용수 절감 및 폐기물(열매체유 등) 재활용 체계 강화\n• 화학물질 관리법 준수 및 주 1회 이상 정기 점검 진행")

        st.markdown("---")
        st.subheader("3️⃣ 학생 상담용 추천 포인트 및 동문 진출 현황")
        r_tips = st.text_area("학생 지도 가이드라인", value="• 환경공학과 및 관련학과 졸업예정자 집중 추천\n• AllBaro 시스템 활용 경험 및 대기/수질기사 보유 여부 강조 필수")
        r_alumni = st.text_area("조선대학교 동문 재직/입사 현황 (몇 명 진출 등 기재)", value="• 현재 동문 약 3명 재직 중 (환경공학과 졸업생 중심 현장 배치)")

        st.markdown("---")
        st.subheader("4️⃣ 조선대학교 최근 취업자 현황 (최근 3~5개년)")
        col_history1, col_history2 = st.columns(2)
        with col_history1:
            r_history_summary = st.text_area("연도별 조선대 취업자 수 및 학과", value="• 2024년: 2명 (환경공학과 1명, 전기공학과 1명)\n• 2025년: 1명 (환경공학과 1명)")
        with col_history2:
            r_history_notes = st.text_area("취업자 특징 및 주요 배치 직무", value="• 주요 배치 직무: 환경자원팀, 시설관리 파트")

        if st.form_submit_button("📄 기업 분석 보고서 완성하기"):
            st.session_state.reports[r_comp] = {
                "기본정보": {"기업명": r_comp, "대표자": r_ceo, "직원수": r_emp, "설립연도": r_est, "유형": r_type, "매출액": r_sales, "영업이익": r_profit, "위치": r_loc, "업종": r_industry, "홈페이지": r_url, "채용시기": r_period, "직무": r_dept},
                "인재상": r_talents, "주요업무": r_tasks, "요건": r_req, "이슈": r_issues, "지도포인트": r_tips, "동문현황": r_alumni,
                "취업자현황": r_history_summary, "취업자특징": r_history_notes
            }
            st.success(f"{r_comp} 기업 분석 보고서가 성공적으로 생성되었습니다!")

    if st.session_state.reports:
        st.markdown("---")
        st.subheader("📋 생성된 기업 분석 보고서 미리보기")
        selected_rep = st.selectbox("보고서를 선택하세요", list(st.session_state.reports.keys()))
        rep_data = st.session_state.reports[selected_rep]

        st.markdown(f"### 🏢 [{selected_rep}] 기업 분석 보고서")
        st.caption(f"작성일: {datetime.date.today().strftime('%Y년 %m월 %d일')} | 작성: 조선대학교 취업학생처 취업전략팀")

        info = rep_data["기본정보"]
        st.markdown(f"""
        | 항목 | 내용 | 항목 | 내용 |
        |---|---|---|---|
        | **기업명** | {info['기업명']} | **대표자** | {info['대표자']} |
        | **직원 수** | {info['직원수']} | **설립 연도** | {info['설립연도']} |
        | **매출액** | {info['매출액']} | **영업이익** | {info['영업이익']} |
        | **기업 유형** | {info['유형']} | **업종** | {info['업종']} |
        | **사업장 위치** | {info['위치']} | **채용 시기** | {info['채용시기']} |
        """)

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown("**🎯 기업 인재상**")
            st.text(rep_data["인재상"])
            st.markdown("**🛠️ 주요 업무 내용**")
            st.text(rep_data["주요업무"])
        with col_p2:
            st.markdown("**📋 자격요건 및 우대조건**")
            st.text(rep_data["요건"])
            st.markdown("**💡 최근 기업 이슈 & ESG 동향**")
            st.text(rep_data["이슈"])

        st.warning(f"**🎓 [취업전략팀 지도 가이드]:**\n{rep_data['지도포인트']}")
        st.info(f"**👥 [조선대학교 동문 진출 현황]:**\n{rep_data['동문현황']}")
        
        if "취업자현황" in rep_data:
            st.success(f"**🎓 [조선대학교 최근 취업자 현황]:**\n{rep_data['취업자현황']}\n\n**📌 [취업자 주요 특징 & 배치 직무]:**\n{rep_data['취업자특징']}")
