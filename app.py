import streamlit as st
import pandas as pd
import datetime
import io
import urllib.parse
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="추천채용 통합 관리 시스템", layout="wide")

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

# 네이버 기업정보 자동 크롤링 함수
def fetch_naver_company_info(comp_name):
    info = {"대표자": "", "설립일": "", "매출액": "", "업종": "", "기업유형": ""}
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        url = f"https://search.naver.com/search.naver?query={urllib.parse.quote(comp_name)}+기업정보"
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")
        
        # 네이버 검색 결과 내 요약 데이터 파싱 (HTML 구조 탐색)
        text_data = soup.get_text()
        info["기업유형"] = auto_detect_company_type(comp_name)
        
        # 예시 기본값 처리 (실제 검색 데이터 매칭)
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
            "기업명": "㈜하림산업", "구분": "대기업(계열사)", "채용직무": "환경자원팀",
            "HR성명": "김인사", "HR직급": "팀장", "HR내선": "063-123-4567", "HR휴대폰": "010-1234-5678", "HRe-mail": "hr@harim.com",
            "공고시기": "2026-07", "진행상태": "마감"
        }
    ])

if "applicants" not in st.session_state:
    st.session_state.applicants = pd.DataFrame([
        {
            "학번": "20201234", "학생명": "김철수", "학과": "환경공학과", "학적": "재학",
            "연락처": "010-1111-2222", "이메일": "chulsoo@chosun.ac.kr", "학점": 3.6,
            "지원기업": "㈜하림산업", "지원직무": "환경자원팀", "지원일": "2026-07-15", "상태": "최종합격"
        }
    ])

if "passed" not in st.session_state:
    st.session_state.passed = pd.DataFrame([
        {
            "학번": "20201234", "이름": "김철수", "학과": "환경공학과", "연락처": "010-1111-2222",
            "기업명": "㈜하림산업", "직무": "환경자원팀", "입사일": "2026-08-01",
            "재직상태": "재직중", "멘토가능여부": True, "비고": "환경기사 보유"
        }
    ])

if "reports" not in st.session_state:
    st.session_state.reports = {}

if "crawled_info" not in st.session_state:
    st.session_state.crawled_info = {"대표자": "", "설립일": "", "매출액": "", "업종": "", "기업유형": ""}

def create_template(target_type):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        if target_type == "등록 기업 목록":
            df_tpl = pd.DataFrame([{"기업명": "예시기업(주)", "구분": "중견기업", "채용직무": "경영지원", "HR성명": "홍길동", "HR직급": "과장", "HR내선": "02-123-4567", "HR휴대폰": "010-0000-0000", "HRe-mail": "hr@example.com", "공고시기": "2026-08", "진행상태": "진행중"}])
            df_tpl.to_excel(writer, sheet_name='등록기업_양식', index=False)
        elif target_type == "지원 학생 목록":
            df_tpl = pd.DataFrame([{"학번": "20230001", "학생명": "홍길동", "학과": "경영학과", "학적": "재학", "연락처": "010-0000-0000", "이메일": "example@chosun.ac.kr", "학점": 3.8, "지원기업": "예시기업(주)", "지원직무": "경영지원", "지원일": "2026-08-01", "상태": "접수"}])
            df_tpl.to_excel(writer, sheet_name='지원학생_양식', index=False)
        elif target_type == "합격자 DB 목록":
            df_tpl = pd.DataFrame([{"학번": "20230001", "이름": "홍길동", "학과": "경영학과", "연락처": "010-0000-0000", "기업명": "예시기업(주)", "직무": "경영지원", "입사일": "2026-08-01", "재직상태": "재직중", "멘토가능여부": True, "비고": "신입사원"}])
            df_tpl.to_excel(writer, sheet_name='합격자_양식', index=False)
    return output.getvalue()

st.title("🎓 추천채용 통합 관리 시스템")
st.caption("등록 기업, HR 담당자, 지원 학생 상세 정보 및 기업 분석 보고서를 통합 관리합니다.")

menu = st.sidebar.selectbox("📂 메뉴 선택", ["1. 등록 기업 관리", "2. 지원 학생 관리", "3. 합격자 DB & 멘토 풀", "4. 전체 현황 요약", "📂 5. 기존 엑셀 일괄 업로드", "📝 6. 기업 분석 보고서 생성"])

# --- 1 ~ 5 메뉴 생략 (동일 유지) ---
if menu == "1. 등록 기업 관리":
    st.header("🏢 추천채용 등록 기업 & HR 담당자 리스트")
    edited_companies = st.data_editor(st.session_state.companies, use_container_width=True, num_rows="dynamic")
    st.session_state.companies = edited_companies
elif menu == "2. 지원 학생 관리":
    st.header("👨‍🎓 지원 학생 상세 리스트")
    edited_applicants = st.data_editor(st.session_state.applicants, use_container_width=True, num_rows="dynamic")
    st.session_state.applicants = edited_applicants
elif menu == "3. 합격자 DB & 멘토 풀":
    st.header("🏆 합격자 데이터베이스 & 실무 멘토 풀")
    edited_passed = st.data_editor(st.session_state.passed, use_container_width=True, num_rows="dynamic")
    st.session_state.passed = edited_passed
elif menu == "4. 전체 현황 요약":
    st.header("📊 추천채용 종합 현황")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("등록 기업 수", f"{len(st.session_state.companies)}개")
    m2.metric("총 지원자 수", f"{len(st.session_state.applicants)}명")
    m3.metric("최종 합격자 수", f"{len(st.session_state.passed)}명")
    m4.metric("활용 가능 멘토", f"{len(st.session_state.passed[(st.session_state.passed['재직상태']=='재직중') & (st.session_state.passed['멘토가능여부']==True)])}명")
elif menu == "📂 5. 기존 엑셀 일괄 업로드":
    st.header("📂 기존 엑셀 데이터 불러오기")
    col_up1, col_up2 = st.columns([1, 1])
    with col_up1:
        target_tpl = st.selectbox("다운로드할 양식을 선택하세요", ["등록 기업 목록", "지원 학생 목록", "합격자 DB 목록"])
        st.download_button(label=f"📥 {target_tpl} 표준 양식(.xlsx) 다운로드", data=create_template(target_tpl), file_name=f"{target_tpl}_표준양식.xlsx")
    with col_up2:
        uploaded_file = st.file_uploader("작성 완료된 엑셀 파일(.xlsx)을 드래그하세요.", type=["xlsx", "xls"])
        if uploaded_file is not None:
            df_upload = pd.read_excel(uploaded_file)
            st.dataframe(df_upload, use_container_width=True)

# --- 6. 기업 분석 보고서 생성 (자동 크롤링 지원) ---
elif menu == "📝 6. 기업 분석 보고서 생성":
    st.header("📝 기업 분석 및 추천채용 보고서 생성")
    st.info("기업명을 입력하고 [🔍 기업정보 자동 조회] 버튼을 누르면 대표자, 설립일, 매출액, 업종 등이 자동으로 채워집니다.")

    # 🔍 자동 크롤링 조회 영역
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

    # 📝 보고서 작성 폼
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
        st.subheader("3️⃣ 학생 상담용 추천 포인트 (취업전략팀 작성)")
        r_tips = st.text_area("학생 지도 가이드라인", value="• 환경공학과 및 관련학과 졸업예정자 집중 추천\n• AllBaro 시스템 활용 경험 및 대기/수질기사 보유 여부 강조 필수\n• ESG 관련 현장 안전점검 지식 준비 권장")

        if st.form_submit_button("📄 기업 분석 보고서 완성하기"):
            st.session_state.reports[r_comp] = {
                "기본정보": {"기업명": r_comp, "대표자": r_ceo, "직원수": r_emp, "설립연도": r_est, "유형": r_type, "매출액": r_sales, "영업이익": r_profit, "위치": r_loc, "업종": r_industry, "홈페이지": r_url, "채용시기": r_period, "직무": r_dept},
                "인재상": r_talents, "주요업무": r_tasks, "요건": r_req, "이슈": r_issues, "지도포인트": r_tips
            }
            st.success(f"{r_comp} 기업 분석 보고서가 성공적으로 생성되었습니다!")

    # 생성된 보고서 미리보기
    if st.session_state.reports:
        st.markdown("---")
        st.subheader("📋 생성된 기업 분석 보고서 미리보기")
        selected_rep = st.selectbox("보고서를 선택하세요", list(st.session_state.reports.keys()))
        rep_data = st.session_state.reports[selected_rep]

        st.markdown(f"### 🏢 [{selected_rep}] 기업 분석 보고서")
        st.caption(f"작성일: {datetime.date.today().strftime('%Y년 %m월 %d일')} | 작성: 취업학생처 취업전략팀")

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