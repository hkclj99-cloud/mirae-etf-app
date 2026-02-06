import streamlit as st
import FinanceDataReader as fdr
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(page_title="Mirae Asset TIGER ETF Chart", layout="wide")
st.title("📈 미래에셋 TIGER ETF 차트 분석기")


# 2. 데이터 캐싱 및 ETF 리스트 가져오기
@st.cache_data
def get_etf_list():
    df = fdr.StockListing('ETF/KR')
    # 미래에셋의 'TIGER' 브랜드만 필터링
    tiger_etfs = df[df['Name'].str.contains('TIGER')].copy()
    return tiger_etfs


etf_df = get_etf_list()

# 3. 사이드바 - 종목 선택
st.sidebar.header("🔍 종목 및 설정")
selected_name = st.sidebar.selectbox("TIGER ETF를 선택하세요", etf_df['Name'])
selected_code = etf_df[etf_df['Name'] == selected_name]['Symbol'].values[0]

period = st.sidebar.radio("조회 기간", ["1개월", "3개월", "6개월", "1년"], index=1)
period_map = {"1개월": 30, "3개월": 90, "6개월": 180, "1년": 365}

# 4. 데이터 로드
end_date = datetime.now()
start_date = end_date - timedelta(days=period_map[period])
df_chart = fdr.DataReader(selected_code, start_date, end_date)

# 5. 차트 생성 (Plotly)
fig = go.Figure()

# 캔들스틱 추가
fig.add_trace(go.Candlestick(
    x=df_chart.index,
    open=df_chart['Open'],
    high=df_chart['High'],
    low=df_chart['Low'],
    close=df_chart['Close'],
    name='주가'
))

# 이동평균선 추가 (20일)
df_chart['MA20'] = df_chart['Close'].rolling(window=20).mean()
fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['MA20'], line=dict(color='orange', width=1), name='20일 이평선'))

# 차트 레이아웃 설정
fig.update_layout(
    title=f"{selected_name} ({selected_code}) 차트",
    yaxis_title="가격 (KRW)",
    xaxis_rangeslider_visible=False,
    template="plotly_dark",  # 미래에셋의 다크모드 스타일
    height=600
)

# 6. 화면 출력
col1, col2 = st.columns([3, 1])
with col1:
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("📊 종목 정보")
    current_price = df_chart['Close'].iloc[-1]
    prev_price = df_chart['Close'].iloc[-2]
    change = current_price - prev_price
    change_pct = (change / prev_price) * 100

    st.metric("현재가", f"{current_price:,.0f}원", f"{change_pct:+.2f}%")
    st.dataframe(df_chart.tail(10)[['Open', 'High', 'Low', 'Close', 'Volume']].sort_index(ascending=False))

st.info("이 앱은 실시간 주식 데이터를 시각화하는 프로토타입입니다. 실제 매매는 미래에셋증권 m.Stock 앱을 이용하세요.")
