import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
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

        # Kaggle 데이터셋 출처 및 소개
        st.markdown("")

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
        st.title("📊 Bike Sharing Demand EDA")
        uploaded = st.file_uploader("데이터셋 업로드 (train.csv)", type="csv")
        if not uploaded:
            st.info("train.csv 파일을 업로드 해주세요.")
            return

        df = pd.read_csv(uploaded, parse_dates=['datetime'])

         # Tab 1: 기초 통계
        with tabs[0]:
            st.header("기초 통계")
            buffer = io.StringIO()
            df.info(buf=buffer)
            st.subheader("Data Info")
            st.text(buffer.getvalue())

            st.subheader("Summary Statistics")
            st.dataframe(df.describe())

        # Tab 2: 연도별 전체 인구 추이 및 예측
        with tabs[1]:
            st.header("연도별 추이")
            national = df[df['지역'] == '전국'].copy()
            recent = national.sort_values('연도').tail(3)
            avg_delta = (recent['출생아수(명)'] - recent['사망자수(명)']).mean()
            last_year = recent['연도'].max()
            last_population = national[national['연도'] == last_year]['인구'].values[0]
            predicted_population = last_population + avg_delta * (2035 - last_year)

            fig, ax = plt.subplots(figsize=(10, 5))
            sns.lineplot(data=national, x='연도', y='인구', marker='o', ax=ax)
            ax.axvline(2035, color='gray', linestyle='--')
            ax.scatter(2035, predicted_population, color='red', label='2035 prediction')
            ax.text(2035, predicted_population, f'{int(predicted_population):,}', color='red')
            ax.set_title("Population Trend (National)")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            ax.legend()
            st.pyplot(fig)

        # Tab 3: 지역별 인구 변화량
        with tabs[2]:
            st.header("지역별분석")
            region_df = df[df['지역'] != '전국']
            pivot = region_df.pivot(index='지역', columns='연도', values='인구').dropna()
            last_5_years = sorted(pivot.columns)[-5:]
            delta = pivot[last_5_years[-1]] - pivot[last_5_years[0]]
            delta_sorted = delta.sort_values(ascending=False)

            fig1, ax1 = plt.subplots(figsize=(10, 8))
            sns.barplot(x=delta_sorted.values / 1000, y=delta_sorted.index, ax=ax1)
            ax1.set_title("Population Change (Last 5 Years)")
            ax1.set_xlabel("Change (thousands)")
            ax1.set_ylabel("Region")
            for i, val in enumerate(delta_sorted.values / 1000):
                ax1.text(val, i, f"{val:,.0f}", va='center')
            st.pyplot(fig1)

            rate = (pivot[last_5_years[-1]] - pivot[last_5_years[0]]) / pivot[last_5_years[0]] * 100
            rate_sorted = rate.sort_values(ascending=False)

            fig2, ax2 = plt.subplots(figsize=(10, 8))
            sns.barplot(x=rate_sorted.values, y=rate_sorted.index, ax=ax2)
            ax2.set_title("Population Change Rate (%)")
            ax2.set_xlabel("Change Rate (%)")
            ax2.set_ylabel("Region")
            for i, val in enumerate(rate_sorted.values):
                ax2.text(val, i, f"{val:.1f}%", va='center')
            st.pyplot(fig2)

        # Tab 4: 증감률 상위 100개
        with tabs[3]:
            st.header("변화량 분석")
            df_sorted = df[df['지역'] != '전국'].sort_values(['지역', '연도'])
            df_sorted['증감'] = df_sorted.groupby('지역')['인구'].diff()
            top_100 = df_sorted.dropna().nlargest(100, '증감')

            st.dataframe(
                top_100.style
                .background_gradient(subset=['증감'], cmap='RdBu', axis=0)
                .format({'인구': '{:,.0f}', '출생아수(명)': '{:,.0f}', '사망자수(명)': '{:,.0f}', '증감': '{:,.0f}'})
            )

        # Tab 5: 지역-연도 피벗 히트맵
        with tabs[4]:
            st.header("시각화")
            pivot_table = df[df['지역'] != '전국'].pivot(index='지역', columns='연도', values='인구').dropna()
            pivot_table_k = pivot_table / 1000  # 천 단위

            fig3, ax3 = plt.subplots(figsize=(12, 6))
            sns.heatmap(pivot_table_k, cmap="YlGnBu", annot=False, ax=ax3)
            ax3.set_title("Population Heatmap (Thousands)")
            ax3.set_xlabel("Year")
            ax3.set_ylabel("Region")
            st.pyplot(fig3)


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