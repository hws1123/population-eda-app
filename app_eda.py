import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        st.markdown("""
        이 앱은 대한민국의 인구 변화 데이터를 바탕으로 다양한 통계와 시각화를 제공합니다.  
        아래와 같은 기능을 탐색해보세요:

        - **기초 통계**: 인구, 출생아수, 사망자수 등의 기본 통계와 결측치 처리 현황을 확인할 수 있습니다.  
        - **연도별 추이**: 전국 인구의 연도별 변화와 2035년까지의 인구 예측을 시각적으로 확인할 수 있습니다.  
        - **지역별 분석**: 각 지역의 최근 5년간 인구 변화량과 변화율을 비교하고 분석할 수 있습니다.  
        - **변화량 분석**: 전국에서 인구가 가장 많이 증가하거나 감소한 지역·연도 TOP 100을 확인할 수 있습니다.  
        - **시각화**: 지역별·연도별 인구를 히트맵과 누적 영역 그래프로 한눈에 파악할 수 있습니다.

        📊 좌측 메뉴에서 'EDA'를 선택하여 탐색을 시작해보세요!
        """)

# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("Population trends EDA")
        uploaded = st.file_uploader("population_trends.csv", type="csv")
        if not uploaded:
            st.info("population_trends.csv 파일을 업로드 해주세요.")
            return

        df = pd.read_csv(uploaded)
        tabs = st.tabs(["기초 통계", "연도별 추이", "지역별 분석", "변화량 분석", "시각화"])

         # Tab 1: 기초 통계
        with tabs[0]:
            st.header("기초 통계")

            # 3. 결측치 '-' 처리 및 숫자 변환
            df.replace('-', np.nan, inplace=True)

            numeric_cols = ['인구', '출생아수(명)', '사망자수(명)']
            df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')

            # 4. '세종' 지역의 결측치를 0으로 치환
            df.loc[df['지역'] == '세종', numeric_cols] = df.loc[df['지역'] == '세종', numeric_cols].fillna(0)

            # 5. 데이터프레임 구조 출력 (df.info())
            st.subheader("📋 데이터프레임 구조 (df.info())")
            buffer = io.StringIO()
            df.info(buf=buffer)
            st.text(buffer.getvalue())

            # 6. 요약 통계 출력 (df.describe())
            st.subheader("📈 수치형 데이터 요약 통계 (df.describe())")
            st.dataframe(df[numeric_cols].describe())

        # Tab 2: 연도별 전체 인구 추이 및 예측
        with tabs[1]:
            st.header("연도별 추이")
            # 2. 데이터 로드 및 기본 전처리
            df.replace('-', pd.NA, inplace=True)
            df[['인구', '출생아수(명)', '사망자수(명)']] = df[['인구', '출생아수(명)', '사망자수(명)']].apply(pd.to_numeric, errors='coerce')

            # 3. 전국 데이터 필터링
            df_national = df[df['지역'] == '전국'].dropna(subset=['인구'])

            # 4. 최근 3년 평균 증감 계산
            df_national_sorted = df_national.sort_values('연도')
            recent = df_national_sorted.tail(3)
            avg_change = (recent['출생아수(명)'] - recent['사망자수(명)']).mean()

            # 5. 마지막 연도와 인구
            last_year = recent['연도'].max()
            last_population = recent[recent['연도'] == last_year]['인구'].values[0]

            # 6. 2035년 인구 예측
            future_year = 2035
            years_forward = future_year - last_year
            predicted_population = last_population + avg_change * years_forward

            # 7. 시각화
            fig, ax = plt.subplots(figsize=(10, 5))
            sns.lineplot(data=df_national_sorted, x='연도', y='인구', marker='o', ax=ax)
            ax.axvline(future_year, linestyle='--', color='gray')
            ax.scatter(future_year, predicted_population, color='red', label='2035 Prediction')
            ax.text(future_year, predicted_population, f"{int(predicted_population):,}", color='red', va='bottom')

            ax.set_title("National Population Trend")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            ax.legend()

            st.pyplot(fig)

            st.markdown(f"""
            **Prediction Summary**  
            - Average annual net change (Births - Deaths): `{avg_change:,.0f}`  
            - Predicted population in {future_year}: `{int(predicted_population):,}`
            """)

        # Tab 3: 지역별 인구 변화량
        with tabs[2]:
            st.header("지역별 분석")
            df.replace('-', pd.NA, inplace=True)
            df[['인구']] = df[['인구']].apply(pd.to_numeric, errors='coerce')
            df = df[df['지역'] != '전국'].dropna(subset=['인구'])

            # 📍 지역명 영문 변환 (예시 맵핑: 필요시 더 추가 가능)
            region_map = {
                '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
                '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
                '경기': 'Gyeonggi', '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam',
                '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam',
                '제주': 'Jeju'
            }
            df['region_en'] = df['지역'].map(region_map)

            # 🧮 피벗 테이블
            pivot = df.pivot(index='region_en', columns='연도', values='인구')
            pivot = pivot.dropna()

            # 최근 5년 변화량 및 변화율 계산
            recent_years = sorted(pivot.columns)[-5:]
            change = pivot[recent_years[-1]] - pivot[recent_years[0]]
            rate = (change / pivot[recent_years[0]]) * 100

            # 내림차순 정렬
            change_sorted = change.sort_values(ascending=False)
            rate_sorted = rate.loc[change_sorted.index]

            # 단위: 천 명
            change_k = change_sorted / 1000

            # 🎨 그래프 1: 변화량
            fig1, ax1 = plt.subplots(figsize=(10, 8))
            sns.barplot(x=change_k.values, y=change_k.index, ax=ax1, palette="Blues_d")
            ax1.set_title("Population Change (Last 5 Years)")
            ax1.set_xlabel("Change (thousands)")
            ax1.set_ylabel("Region")
            for i, val in enumerate(change_k.values):
                ax1.text(val, i, f"{val:,.0f}", va='center')
            st.pyplot(fig1)

            # 🎨 그래프 2: 변화율
            fig2, ax2 = plt.subplots(figsize=(10, 8))
            sns.barplot(x=rate_sorted.values, y=rate_sorted.index, ax=ax2, palette="Greens_d")
            ax2.set_title("Population Change Rate (%)")
            ax2.set_xlabel("Change Rate (%)")
            ax2.set_ylabel("Region")
            for i, val in enumerate(rate_sorted.values):
                ax2.text(val, i, f"{val:.1f}%", va='center')
            st.pyplot(fig2)

            # 📘 해설
            st.markdown("### Interpretation")
            st.markdown(f"""
            - The first chart shows the **absolute change** in population (in thousands) from {recent_years[0]} to {recent_years[-1]} for each region.
            - The second chart shows the **relative change (%)**, allowing comparison regardless of initial population size.
            - Regions like **Gyeonggi** may show large absolute increases due to size, while **Sejong** may stand out in percentage terms.
            """)

        # Tab 4: 증감률 상위 100개
        with tabs[3]:
            st.header("변화량 분석")
            df.replace('-', np.nan, inplace=True)
            df[['인구']] = df[['인구']].apply(pd.to_numeric, errors='coerce')
            df = df[df['지역'] != '전국'].dropna(subset=['인구'])

            # 증감 계산
            df = df.sort_values(['지역', '연도'])
            df['증감'] = df.groupby('지역')['인구'].diff()

            # 상위 100개 추출
            top100 = df.dropna(subset=['증감']).sort_values(by='증감', ascending=False).head(100)

            # 숫자 열 전체 지정
            numeric_cols = top100.select_dtypes(include='number').columns.tolist()

            # 컬러 강조 함수
            def highlight_change(val):
                color = (
                    'background-color: rgba(0, 100, 255, 0.15)' if val > 0 else
                    'background-color: rgba(255, 80, 80, 0.15)'
                )
                return color

            # 강조 및 포맷 스타일
            st.subheader("🔝 증감률 상위 100개 (지역-연도별)")
            st.dataframe(
                top100.style
                .applymap(highlight_change, subset=['증감'])
                .format({col: '{:,.0f}' for col in numeric_cols})  # 👈 모든 숫자 천단위 콤마 처리
            )

            st.markdown(f"""
            ### Interpretation
            - This table shows the **top 100 increases** in population by region and year.
            - **Blue background**: population increased from the previous year.  
            - **Red background**: population decreased.
            - All numbers are formatted with **thousands separators**.
            """)

        # Tab 5: 지역-연도 피벗 히트맵
        with tabs[4]:
            st.header("시각화")
            # 2. 데이터 로드 및 전처리
            df.replace('-', pd.NA, inplace=True)
            df = df[df['지역'] != '전국']  # '전국' 제외
            df['인구'] = pd.to_numeric(df['인구'], errors='coerce')
            df = df.dropna(subset=['인구'])

            # 3. 지역명을 영문으로 매핑
            region_map = {
                '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
                '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
                '경기': 'Gyeonggi', '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam',
                '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam',
                '제주': 'Jeju'
            }
            df['region_en'] = df['지역'].map(region_map)

            # 4. 피벗 테이블 생성 (지역: 행, 연도: 열)
            pivot_df = df.pivot(index='region_en', columns='연도', values='인구').fillna(0)
            pivot_df = pivot_df.sort_index()

            # 5. 누적 영역 그래프
            years = pivot_df.columns.tolist()
            regions = pivot_df.index.tolist()
            data = pivot_df.values

            fig, ax = plt.subplots(figsize=(12, 6))

            # 색상 구분 (tab10 등 컬러맵)
            colors = cm.get_cmap('tab20', len(regions)).colors

            ax.stackplot(years, data, labels=regions, colors=colors, alpha=0.9)

            ax.set_title("Population by Region Over Years")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
            ax.margins(x=0)
            ax.set_xlim(min(years), max(years))

            st.pyplot(fig)

            # 피벗 테이블도 아래에 출력
            st.subheader("📋 Pivot Table (Population by Region and Year)")
            st.dataframe(pivot_df.style.format('{:,.0f}'))


# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()