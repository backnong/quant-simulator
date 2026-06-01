import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- 기본 페이지 설정 ---
st.set_page_config(page_title="미국 지수 장기 투자 시뮬레이터", page_icon="📈", layout="wide")
st.title("📈 미국 지수 장기 투자 시뮬레이터 (S&P 500 / 나스닥)")
st.markdown("복리의 마법을 시각적으로 확인해보세요. 거치식/적립식 투자와 물가 상승률(인플레이션)을 모두 고려한 결과를 보여줍니다.")

# --- 사이드바: 입력 패널 ---
st.sidebar.header("⚙️ 투자 설정")

# 1. 즉각 반응해야 하는 통화 선택 (폼 외부에 배치하여 바로 단위가 바뀌도록 함)
currency_choice = st.sidebar.radio("기준 통화 선택", ("USD ($)", "KRW (₩)"))

if currency_choice == "KRW (₩)":
    init_val = 10000000
    init_step = 1000000
    month_val = 500000
    month_step = 100000
    prefix = "₩"
    conv_prefix = "$"
else:
    init_val = 10000
    init_step = 1000
    month_val = 500
    month_step = 100
    prefix = "$"
    conv_prefix = "₩"

# 2. '적용하기' 버튼으로 한 번에 제출되는 폼(Form) 생성
with st.sidebar.form("setting_form"):
    index_choice = st.radio("투자할 지수를 선택하세요", ("S&P 500 (VOO / SPY)", "나스닥 100 (QQQ)"))
    default_return = 10.0 if index_choice == "S&P 500 (VOO / SPY)" else 13.0
    
    st.subheader("💱 환율 설정")
    exchange_rate = st.number_input("적용 환율 (1$ = ?원)", min_value=800, max_value=2000, value=1350, step=10, help="결과를 다른 통화로 환산해서 볼 때 사용됩니다.")
    
    st.subheader("💰 금액 설정")
    initial_investment = st.number_input(f"초기 투자 금액 ({prefix})", min_value=0, value=init_val, step=init_step)
    monthly_contribution = st.number_input(f"매월 적립 금액 ({prefix})", min_value=0, value=month_val, step=month_step)
    
    st.subheader("📅 기간 및 이율")
    years = st.slider("투자 기간 (년)", min_value=1, max_value=100, value=30, step=1)
    annual_return_rate = st.slider("예상 연평균 수익률 (%)", min_value=1.0, max_value=25.0, value=default_return, step=0.5)
    inflation_rate = st.slider("예상 연평균 물가 상승률 (%)", min_value=0.0, max_value=10.0, value=3.0, step=0.1)
    
    # 이 버튼을 눌러야만 위의 모든 설정이 한 번에 앱에 반영됩니다.
    submitted = st.form_submit_button("적용하기 🚀")

# --- 계산 로직 ---
def calculate_investment(initial, monthly, years, annual_return, inflation):
    records = []
    
    # 이자율 소수점 변환
    r = annual_return / 100.0
    inf = inflation / 100.0
    
    nominal_balance = initial
    total_invested = initial
    
    records.append({
        "Year": 0,
        "Total Invested": total_invested,
        "Nominal Value": nominal_balance,
        "Real Value": nominal_balance
    })
    
    for year in range(1, years + 1):
        yearly_contribution = monthly * 12
        nominal_balance = nominal_balance * (1 + r) + yearly_contribution
        total_invested += yearly_contribution
        real_balance = nominal_balance / ((1 + inf) ** year)
        
        records.append({
            "Year": year,
            "Total Invested": total_invested,
            "Nominal Value": nominal_balance,
            "Real Value": real_balance
        })
        
    return pd.DataFrame(records)

# 데이터프레임 생성
df = calculate_investment(initial_investment, monthly_contribution, years, annual_return_rate, inflation_rate)

# --- 결과 요약 표시 (Metrics) ---
st.subheader("📊 시뮬레이션 결과 요약")

final_year_data = df.iloc[-1]

# 환산 가치 계산 로직
if currency_choice == "USD ($)":
    conv_total = final_year_data['Total Invested'] * exchange_rate
    conv_nominal = final_year_data['Nominal Value'] * exchange_rate
    conv_real = final_year_data['Real Value'] * exchange_rate
else:
    conv_total = final_year_data['Total Invested'] / exchange_rate
    conv_nominal = final_year_data['Nominal Value'] / exchange_rate
    conv_real = final_year_data['Real Value'] / exchange_rate

col1, col2, col3 = st.columns(3)

# 메트릭(숫자) 표시부에 환율 변동 결과를 훨씬 크고 직관적으로 보여주도록 수정
with col1:
    st.metric("총 투자 원금", f"{prefix}{final_year_data['Total Invested']:,.0f}")
    st.markdown(f"**환산 금액: {conv_prefix}{conv_total:,.0f}**")
with col2:
    st.metric("명목상 최종 자산 (액면가)", f"{prefix}{final_year_data['Nominal Value']:,.0f}")
    st.markdown(f"**환산 금액: {conv_prefix}{conv_nominal:,.0f}**")
with col3:
    st.metric("실질 최종 자산 (물가 반영)", f"{prefix}{final_year_data['Real Value']:,.0f}", help="인플레이션을 감안했을 때, 현재 시점의 돈 가치로 환산한 금액입니다.")
    st.markdown(f"**환산 금액: {conv_prefix}{conv_real:,.0f}**")

# --- 차트 그리기 (Plotly) ---
st.subheader("📈 자산 성장 그래프")

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df['Year'], y=df['Total Invested'],
    mode='lines',
    name='총 투자 원금',
    line=dict(color='gray', width=2, dash='dash')
))

fig.add_trace(go.Scatter(
    x=df['Year'], y=df['Nominal Value'],
    mode='lines',
    name='명목 자산 (Nominal)',
    line=dict(color='#00CC96', width=3)
))

fig.add_trace(go.Scatter(
    x=df['Year'], y=df['Real Value'],
    mode='lines',
    name='실질 자산 (Real - 물가반영)',
    line=dict(color='#EF553B', width=3)
))

fig.update_layout(
    xaxis_title="투자 기간 (년)",
    yaxis_title=f"자산 가치 ({prefix})",
    hovermode="x unified",
    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
    margin=dict(l=0, r=0, t=30, b=0)
)

st.plotly_chart(fig, use_container_width=True)

# --- 데이터 표 ---
with st.expander("자세한 연도별 데이터 보기"):
    st.dataframe(df.style.format({
        "Total Invested": prefix + "{:,.0f}",
        "Nominal Value": prefix + "{:,.0f}",
        "Real Value": prefix + "{:,.0f}"
    }))

st.markdown("---")
st.caption("※ 본 시뮬레이터는 입력된 연평균 수익률이 매년 일정하게 발생한다는 가정하에 계산된 결과이며, 실제 투자 수익을 보장하지 않습니다. 세금 및 거래 수수료는 포함되지 않았습니다.")
