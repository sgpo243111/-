import streamlit as st
import pandas as pd
import os
import re

# ========== 페이지 설정 ==========
st.set_page_config(
    page_title="제주 청년 지원금 추천",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== 제목 ==========
st.title("🎯 제주 청년 지원금 추천 시스템")
st.markdown("당신에게 맞는 지원금을 찾아보세요!")
st.markdown("---")

# ========== 데이터 로드 ==========
@st.cache_data
def load_data():
    try:
        df = pd.read_excel('청년지원금.xlsx')
        st.success(f"✅ 파일을 성공적으로 로드했습니다!")
        return df
    except FileNotFoundError:
        st.error("❌ 파일을 찾을 수 없습니다!")
        st.write(f"찾는 파일: 청년지원금.xlsx")
        st.write(f"현재 폴더 위치: {os.getcwd()}")
        return None
    except Exception as e:
        st.error(f"❌ 파일 읽기 실패: {e}")
        return None

df = load_data()

if df is None:
    st.stop()

st.write(f"총 {len(df)}개의 지원금 정보가 있습니다.")
st.markdown("---")

# ========== 나이 판별 함수 (새로 추가된 똑똑한 계산기) ==========
def is_age_eligible(age_input, age_cell):
    age_str = str(age_cell).strip()
    
    # 제한 없음, 무관인 경우 패스
    if age_str in ['제한 없음', '무관', 'nan', '상관없음']:
        return True
        
    # '15세 이상' 형태 판별
    if '이상' in age_str:
        match = re.search(r'\d+', age_str)
        if match:
            min_age = int(match.group())
            return age_input >= min_age
            
    # '34세 이하' 형태 판별
    if '이하' in age_str:
        match = re.search(r'\d+', age_str)
        if match:
            max_age = int(match.group())
            return age_input <= max_age

    # '19~39세' 또는 '19세~39세' 범위 형태 판별
    numbers = [int(s) for s in re.findall(r'\d+', age_str)]
    if len(numbers) == 2:
        return numbers[0] <= age_input <= numbers[1]
        
    # 만약 판별이 안 되면 글자가 포함되어 있는지만 검사
    return str(age_input) in age_str

# ========== 레이아웃: 좌측/우측 ==========
col1, col2 = st.columns(2)

# ========== 왼쪽: 입력 영역 ==========
with col1:
    st.subheader("📋 당신의 정보를 입력하세요")
    
    age = st.number_input(
        "👤 나이를 입력하세요",
        min_value=15,
        max_value=69,
        value=25,
        step=1
    )
    
    location = st.selectbox(
        "📍 거주 지역을 선택하세요",
        ["상관없음", "제주시", "서귀포시"]
    )
    
    income = st.number_input(
        "💰 연소득을 입력하세요 (만원)",
        min_value=0,
        max_value=10000,
        value=3000,
        step=100
    )
    
    marriage = st.selectbox(
        "💍 결혼 상태",
        ["상관없음", "미혼", "신혼부부"]
    )
    
    job_status = st.selectbox(
        "🏢 현재 직업/상태",
        ["상관없음", "미취업자", "재직자", "창업자", "영농종사자"]
    )
    
    st.markdown("---")
    
    st.info(f"""
    **📝 입력 정보 요약:**
    - 나이: {age}세
    - 지역: {location}
    - 소득: {income:,}만원
    - 결혼: {marriage}
    - 상태: {job_status}
    """)

# ========== 오른쪽: 버튼 + 결과 ==========
with col2:
    st.subheader("✅ 추천 결과")
    
    search_button = st.button(
        "🔍 나에게 맞는 지원금 찾기",
        use_container_width=True,
        type="primary"
    )
    
    st.markdown("---")
    
    if search_button:
        result = df.copy()
        
        # 1. 똑똑해진 나이 필터링 적용
        result = result[result.apply(lambda row: is_age_eligible(age, row['정책명' if '정책명' in row else 'S']), axis=1) if '정책명' not in df.columns else result.apply(lambda row: is_age_eligible(age, row['나이']), axis=1)]
        
        # 2. 지역 필터링 (무관/제한없음 자동 패스)
        if location != "상관없음":
            result = result[
                (result['지역'].isin(['제한 없음', '무관', '상관없음'])) |
                (result['지역'].str.contains(location, na=False))
            ]
        
        # 3. 결혼 필터링 (무관/제한없음 자동 패스)
        if marriage != "상관없음":
            result = result[
                (result['결혼'].isin(['제한 없음', '무관', '상관없음'])) |
                (result['결혼'].str.contains(marriage, na=False))
            ]
        
        # 4. 직업 필터링 (무관/제한없음 자동 패스)
        if job_status != "상관없음":
            result = result[
                (result['근로(직업)'].isin(['제한 없음', '무관', '상관없음'])) |
                (result['근로(직업)'].str.contains(job_status, na=False))
            ]
        
        # 결과 표시
        if len(result) > 0:
            st.success(f"✅ {len(result)}개의 지원금을 찾았습니다!")
            st.markdown("---")
            
            # 엑셀의 실제 컬럼명 가져오기 (A1 셀이 'S'든 '정책명'이든 대응)
            name_col = '정책명' if '정책명' in df.columns else 'S'
            
            for idx, row in result.iterrows():
                with st.expander(f"📌 {row[name_col]} ({row['분야']})"):
                    st.write(f"**분야:** {row['분야']}")
                    st.write(f"**나이:** {row['나이']}")
                    st.write(f"**지역:** {row['지역']}")
                    st.write(f"**소득:** {row['소득']}")
                    st.write(f"**결혼:** {row['결혼']}")
                    st.write(f"**학력:** {row['학력']}")
                    st.write(f"**직업/상태:** {row['근로(직업)']}")
                    st.markdown("---")
                    st.write("**📋 지원 내용:**")
                    st.info(row['정책 내용'])
        else:
            st.warning("❌ 조건에 맞는 지원금이 없습니다.")
            st.write("💡 다른 조건으로 다시 검색해보세요!")

st.markdown("---")
st.markdown("""
### 💡 팁
- **"상관없음"**을 선택하면 해당 조건은 무시됩니다
- 각 지원금의 자세한 내용은 확장(▼)을 클릭하세요

---
**📞 문의:** 제주시청 또는 서귀포시청
""")