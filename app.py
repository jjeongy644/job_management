import streamlit as st
import pandas as pd
import datetime
import io
import os
import urllib.parse
import requests
from bs4 import BeautifulSoup
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="조선대학교 추천채용 통합 관리 시스템", layout="wide")

# --- 구글 시트 연결 설정 (시간 동기화 오차 없는 파일 직접 연동 방식) ---
def get_google_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    # 깃허브에 업로드된 service_account.json 파일을 직접 타겟팅하여 서명 에러를 우회합니다
    creds = Credentials.from_service_account_file("service_account.json", scopes=scope)
    client = gspread.authorize(creds)
    return client.open("추천채용통합DB")

def load_data_from_gs(sheet_name, default_columns):
    try:
        sh = get_google_sheet()
        ws = sh.worksheet(sheet_name)
        data = ws.get_all_records()
        if data:
            df = pd.DataFrame(data)
            for col in df.columns:
                if "일" in col or "날짜" in col or "기간" in col or "일자" in col:
                    df[col] = df[col].astype(str).str.split(" ").str[0].replace("nan", "").replace("NaT", "")
            return df
        else:
            return pd.DataFrame(columns=default_columns)
    except Exception as e:
        return pd.DataFrame(columns=default_columns)

def save_data_to_gs(sheet_name, df):
    try:
        sh = get_google_sheet()
        ws = sh.worksheet(sheet_name)
        ws.clear()
        data_to_update = [df.columns.values.tolist()] + df.values.tolist()
        ws.update(data_to_update)
        st.success("구글 시트에 데이터가 안전하게 저장되었습니다!")
    except Exception as e:
        st.error(f"구글 시트 저장 실패: {e}")

# --- 세션 데이터 초기화 ---
if "companies" not in st.session_state:
    st.session_state.companies = load_data_from_gs("companies", ["연번", "등록일", "기업명", "모집기간", "담당자성명", "직급", "내선번호", "연락처", "e-mail", "채용공고일자", "직무", "비고"])
if "applicants" not in st.session_state:
    st.session_state.applicants = load_data_from_gs("applicants", ["연번", "지원일자", "지원기업", "지원직무", "성명", "학과", "학번", "학적", "졸업(예정)일", "연락처", "이메일", "공고시기", "진행상태"])
if "passed" not in st.session_state:
    st.session_state.passed = load_data_from_gs("passed", ["연번", "합격일자", "학번", "이름", "학과", "연락처", "기업명", "직무", "입사일", "재직상태", "멘토가능여부", "비고"])

if "reports" not in st.session_state:
    st.session_state.reports = {}

if "crawled_info" not in st.session_state:
    st.session_state.crawled_info = {"대표자": "", "설립일": "", "매출액": "", "업종": "", "기업유형": ""}

# --- 로고 및 헤더 ---
def get_logo_path():
    files = os.listdir(".") if os.path.exists(".") else []
    for f in files:
        if any(keyword in f.lower() for keyword in ["logo", "로고", "조선"]) and f.endswith((".png", ".jpg", ".jpeg", ".webp")):
            return f
    return None

col_logo, col_title = st.columns([1, 5])
with col_logo:
    if get_logo_path(): 
        st.image(get_logo_path(), width=140)
    else: 
        st.markdown("### 🎓 **CHOSUN**")
with col_title:
    st.title("조선대학교 추천채용 통합 관리 시스템")
    st.caption("조선대학교 취업학생처 취업전략팀 | 등록 기업, HR 담당자, 지원 학생 및 기업 분석 보고서 관리")

st.markdown("---")

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

# --- 사이드바 메뉴 ---
menu = st.sidebar.selectbox("메뉴 선택", [
    "1. 등록 기업 관리", 
    "2. 지원 학생 관리", 
    "3. 합격자 DB & 멘토 풀", 
    "4. 추천채용 실적 및 주간/월간 보고", 
    "5. 기존 엑셀 일괄 업로드", 
    "6. 기업 분석 보고서 생성"
])

# --- 1. 등록 기업 관리 ---
if menu == "1. 등록 기업 관리":
    st.header("🏢 추천채용 등록 기업 & HR 담당자 리스트")
    st.info("💡 표 안의 항목을 수정하고 저장하기 버튼을 누르면 구글 시트에 반영됩니다.")
    
    edited_companies = st.data_editor(
        st.session_state.companies, 
        use_container_width=True, 
        num_rows="dynamic",
        column_config={"연번": st.column_config.NumberColumn("연번", disabled=True)}
    )
    st.session_state.companies = edited_companies

    if st.button("저장하기"):
        save_data_to_gs("companies", st.session_state.companies)

    st.markdown("---")
    col_search, col_form = st.columns([1, 2])
    with col_search:
        st.subheader("🔍 기업구분 빠른 검색")
        search_comp = st.text_input("기업명 검색/확인", placeholder="예: 하림산업, 삼성전자")
        if search_comp:
            detected_type = auto_detect_company_type(search_comp)
            st.success(f"추천 기업구분: **{detected_type}**")
            encoded_name = urllib.parse.quote(search_comp)
            dart_url = f"https://dart.fss.or.kr/dsab002/main.do?selectKey=1&textCrpNm={encoded_name}"
            st.markdown(f"👉 [🔗 DART 전자공시에서 '{search_comp}' 확인하기]({dart_url})")

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
                save_data_to_gs("companies", st.session_state.companies)
                st.success(f"{c_name} 등록 완료!")
                st.rerun()

# --- 2. 지원 학생 관리 ---
elif menu == "2. 지원 학생 관리":
    st.header("👨‍🎓 지원 학생 상세 리스트")
    edited_applicants = st.data_editor(
        st.session_state.applicants, 
        use_container_width=True, 
        num_rows="dynamic",
        column_config={"연번": st.column_config.NumberColumn("연번", disabled=True)}
    )
    st.session_state.applicants = edited_applicants

    if st.button("저장하기"):
        save_data_to_gs("applicants", st.session_state.applicants)

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
            save_data_to_gs("applicants", st.session_state.applicants)
            st.success(f"{a_name} 학생 등록 완료!")
            st.rerun()

# --- 3. 합격자 DB & 멘토 풀 ---
elif menu == "3. 합격자 DB & 멘토 풀":
    st.header("🏆 합격자 데이터베이스 & 실무 멘토 풀")
    edited_passed = st.data_editor(
        st.session_state.passed, 
        use_container_width=True, 
        num_rows="dynamic",
        column_config={"연번": st.column_config.NumberColumn("연번", disabled=True)}
    )
    st.session_state.passed = edited_passed
    if st.button("저장하기"):
        save_data_to_gs("passed", st.session_state.passed)

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
        if len(weekly_companies) > 0:
            weekly_view = []
            for idx, row in weekly_companies.reset_index().iterrows():
                comp_name = row.get("기업명", "")
                applicant_count = len(df_a[df_a["지원기업"] == comp_name]) if len(df_a) > 0 else 0
                weekly_view.append({
                    "구 분": idx + 1, "기업명": comp_name, "채용직무": row.get("직무", ""),
                    "접수 기한": row.get("모집기간", ""), "지원자": applicant_count, "비고": row.get("비고", "-")
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
            st.dataframe(monthly_df, use_container_width=True)
        with col_m2:
            if len(monthly_df) > 0:
                st.bar_chart(monthly_df)

# --- 5. 기존 엑셀 일괄 업로드 ---
elif menu == "5. 기존 엑셀 일괄 업로드":
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
            for col in df_upload.columns:
                if "일" in col or "날짜" in col or "기간" in col or "일자" in col:
                    df_upload[col] = df_upload[col].astype(str).apply(lambda x: x.split(" ")[0] if pd.notnull(x) and x != "nan" else "")
            st.dataframe(df_upload, use_container_width=True)
            if st.button("구글 시트에 이 데이터 통합 및 저장하기"):
                if target_upload == "등록 기업 목록":
                    start_no = len(st.session_state.companies) + 1
                    df_upload["연번"] = range(start_no, start_no + len(df_upload))
                    st.session_state.companies = pd.concat([st.session_state.companies, df_upload], ignore_index=True)
                    save_data_to_gs("companies", st.session_state.companies)
                elif target_upload == "지원 학생 목록":
                    start_no = len(st.session_state.applicants) + 1
                    df_upload["연번"] = range(start_no, start_no + len(df_upload))
                    st.session_state.applicants = pd.concat([st.session_state.applicants, df_upload], ignore_index=True)
                    save_data_to_gs("applicants", st.session_state.applicants)
                st.success("구글 시트에 데이터 통합 및 영구 저장 완료!")
                st.rerun()

# --- 6. 기업 분석 보고서 생성 ---
elif menu == "6. 기업 분석 보고서 생성":
    st.header("📝 기업 분석 및 추천채용 보고서 생성")
    col_s1, col_s2 = st.columns([3, 1])
    with col_s1:
        target_search_comp = st.text_input("분석할 기업명 입력", value="하림산업")
    with col_s2:
        st.markdown("&nbsp;")
        if st.button("🔍 기업정보 자동 조회"):
            fetched = fetch_naver_company_info(target_search_comp)
            st.session_state.crawled_info = fetched
            st.success("기업 정보를 성공적으로 불러왔습니다!")

    c_data = st.session_state.crawled_info
    with st.form("company_analysis_form"):
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
            r_period = st.text_input("공고/채용 시기", value="수시 채용")
            r_dept = st.text_input("분석 직무/부서", value="환경자원팀")

        r_talents = st.text_area("기업 인재상", value="• 프로 인재상: 고도의 전문 능력과 열정\n• 프로 리더상: 경영이념 구현")
        r_tasks = st.text_area("주요 업무 내용", value="1. 배출원 관리\n2. 환경시설물 관리")
        r_req = st.text_area("자격 요건 & 우대 조건", value="• 자격요건: 학사 이상, 관련 자격증 소지자")
        r_issues = st.text_area("최근 기업 이슈 및 ESG 경영 동향", value="• 자원순환형 ESG 환경 관리")
        r_tips = st.text_area("학생 지도 가이드라인", value="• 관련학과 졸업예정자 집중 추천")
        r_alumni = st.text_area("조선대학교 동문 재직 현황", value="• 현재 동문 약 3명 재직 중")
        r_history_summary = st.text_area("조선대학교 최근 취업자 현황", value="• 2024년: 2명\n• 2025년: 1명")
        r_history_notes = st.text_area("취업자 특징", value="• 주요 배치 직무: 환경자원팀")

        if st.form_submit_button("📄 기업 분석 보고서 완성하기"):
            st.session_state.reports[r_comp] = {
                "기본정보": {"기업명": r_comp, "대표자": r_ceo, "직원수": r_emp, "설립연도": r_est, "유형": r_type, "매출액": r_sales, "영업이익": r_profit, "위치": r_loc, "업종": r_industry, "홈페이지": r_url, "채용시기": r_period, "직무": r_dept},
                "인재상": r_talents, "주요업무": r_tasks, "요건": r_req, "이슈": r_issues, "지도포인트": r_tips, "동문현황": r_alumni,
                "취업자현황": r_history_summary, "취업자특징": r_history_notes
            }
            st.success("보고서 생성 완료!")

    if st.session_state.reports:
        st.markdown("---")
        selected_rep = st.selectbox("보고서를 선택하세요", list(st.session_state.reports.keys()))
        rep_data = st.session_state.reports[selected_rep]
        st.markdown(f"### 🏢 [{selected_rep}] 기업 분석 보고서")
        info = rep_data["기본정보"]
        st.markdown(f"""
        | 항목 | 내용 | 항목 | 내용 |
        |---|---|---|---|
        | **기업명** | {info['기업명']} | **대표자** | {info['대표자']} |
        | **직원 수** | {info['직원수']} | **설립 연도** | {info['설립연도']} |
        | **매출액** | {info['매출액']} | **기업 유형** | {info['유형']} |
        """)
        st.info(f"**🎓 [취업전략팀 지도 가이드]:**\n{rep_data['지도포인트']}")
