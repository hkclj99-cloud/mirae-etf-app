import streamlit as st
import FinanceDataReader as fdr
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="Mirae Asset TIGER ETF Pro", layout="wide")
st.title("📈 TIGER ETF 프로 분석기 (RSI & RMI 추가)")

# 2. 보조지표 계산 함수
def calculate_rsi(df, period=14):
    delta = df['Close'].diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    ema_up = up.ewm(com=period - 1, adjust=False).mean()
    ema_down = down.ewm(com=period - 1, adjust=False).mean()
    rs = ema_up / ema_down
    return 100 - (100 / (1 + rs))

def calculate_rmi(df, d=5, n=10):
    # RMI는 d일 전 가격과의 차이를 이용해 n일 평활화 수행
    delta = df['Close'].diff(d)
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    ema_up = up.ewm(com=n - 1, adjust=False).mean()
    ema_down = down.ewm(com=n - 1, adjust=False).mean()
    rs = ema_up / ema_down
    return 100 - (100 / (1 + rs))

# 3. 데이터 캐싱 및 ETF 리스트
@st.cache_data
def get_etf_list():
    df = fdr.StockListing('ETF/KR')
    return df[df['Name'].str.contains('TIGER')].copy()

etf_df = get_etf_list()

# 4. 사이드바 설정
st.sidebar.header("🔍 종목 및 설정")
selected_name = st.sidebar.selectbox("TIGER ETF 선택", etf_df['Name'])
selected_code = etf_df[etf_df['Name'] == selected_name]['Symbol'].values[0]
period_label = st.sidebar.radio("조회 기간", ["3개월", "6개월", "1년", "2년"], index=0)
period_map = {"3개월": 90, "6개월": 180, "1년": 365, "2년": 730}

# 5. 데이터 로드 및 계산
end_date = datetime.now()
start_date = end_date - timedelta(days=period_map[period_label] + 50) # 보조지표 계산을 위해 여유분 추가
df = fdr.DataReader(selected_code, start_date, end_date)

df['RSI'] = calculate_rsi(df, 14)
df['RMI'] = calculate_rmi(df, 5, 10)
df['MA20'] = df['Close'].rolling(window=20).mean()

# 실제 보여줄 기간만 슬라이싱
df = df.iloc[30:]

# 6. 차트 생성 (서브플롯: 주가, RSI, RMI)
fig = make_subplots(
    rows=3, cols=1,
    shared_xaxes=True,
    vertical_spacing=0.05,
    row_heights=[0.5, 0.25, 0.25],
    subplot_titles=("주가 및 이동평균선", "RSI (14)", "RMI (5, 10)")
)

# (1) 메인 차트: 캔들스틱
fig.add_trace(go.Candlestick(
    x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='주가'
), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='orange', width=1), name='20일선'), row=1, col=1)

# (2) RSI 차트
fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='yellow', width=1.5), name='RSI'), row=2, col=1)
fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

# (3) RMI 차트
fig.add_trace(go.Scatter(x=df.index, y=df['RMI'], line=dict(color='cyan', width=1.5), name='RMI'), row=3, col=1)
fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)

# 레이아웃 업데이트
fig.update_layout(height=800, template="plotly_dark", xaxis_rangeslider_visible=False, showlegend=False)
fig.update_yaxes(title_text="Price", row=1, col=1)
fig.update_yaxes(title_text="RSI", row=2, col=1)
fig.update_yaxes(title_text="RMI", row=3, col=1)

# 7. 화면 출력
col1, col2 = st.columns([4, 1])
with col1:
    st.plotly_chart(fig, use_container_width=True)
with col2:
    st.subheader("📊 정보")
    curr = df['Close'].iloc[-1]
    diff = curr - df['Close'].iloc[-2]
    st.metric("현재가", f"{curr:,.0f}원", f"{(diff/curr)*100:+.2f}%")
    st.write(f"**RSI**: {df['RSI'].iloc[-1]:.1f}")
    st.write(f"**RMI**: {df['RMI'].iloc[-1]:.1f}")

st.caption("RSI 70 이상: 과매수(빨간선), 30 이하: 과매도(초록선) 구간입니다.")