import ccxt
import pandas as pd

def main():
    # 바이낸스 거래소 객체 생성
    binance = ccxt.binance()

    # 비트코인(BTC/USDT)의 최근 1000일(1d timeframe) OHLCV 데이터 가져오기
    print("데이터를 불러오는 중입니다...\n")
    btc_ohlcv = binance.fetch_ohlcv('BTC/USDT', timeframe='1d', limit=1000)

    # Pandas DataFrame으로 변환하여 표(Table) 형태로 만들기
    df = pd.DataFrame(btc_ohlcv, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])

    # Date 컬럼(밀리초 타임스탬프)을 날짜 포맷으로 변환
    df['Date'] = pd.to_datetime(df['Date'], unit='ms').dt.strftime('%Y-%m-%d')
    df.set_index('Date', inplace=True)

    # 20일 이동평균선(MA20) 계산
    df['MA20'] = df['Close'].rolling(window=20).mean()

    # 출력 포맷 맞추기
    print("========== 비트코인(BTC/USDT) 최근 1000일 가격 데이터 ==========\n")
    print(df.to_string())
    print("\n================================================================")
    
    # 추세 분석 (오늘 가격 vs 20일 이동평균)
    latest_close = df['Close'].iloc[-1]
    latest_ma20 = df['MA20'].iloc[-1]
    
    if latest_close > latest_ma20:
        trend = "상승세 🚀"
    elif latest_close < latest_ma20:
        trend = "하락세 📉"
    else:
        trend = "보합세 ➖"
        
    print(f"오늘의 종가: {latest_close:,.2f}")
    print(f"20일 이동평균: {latest_ma20:,.2f}")
    print(f"현재 추세: {trend}")
    print("================================================================\n")
    
    # 백테스팅(모의투자) 로직 추가
    print("========== 1000일 백테스팅(모의투자) 결과 ==========")
    initial_balance = 10000.0  # 초기 자본금 $10,000 (약 1300만 원)
    balance = initial_balance
    btc_amount = 0.0
    position = 0 # 0: 현금 보유, 1: 비트코인 보유
    
    print("[거래 내역]")
    trade_count = 0
    fee_rate = 0.001  # 매수/매도 시 바이낸스 현물 수수료(0.1%) 차감
    
    # 각 날짜별로 종가를 확인하며 매수/매도 진행
    for date, row in df.iterrows():
        close = row['Close']
        ma20 = row['MA20']
        
        # 20일 이동평균 데이터가 없는 초반 19일은 거래 불가이므로 패스
        if pd.isna(ma20):
            continue 
            
        # 종가가 20일 이동평균선보다 높고(상승세), 현재 비트코인을 보유하고 있지 않다면 '전량 매수'
        if position == 0 and close > ma20:
            # 수수료를 뺀 만큼만 BTC를 획득
            btc_amount = (balance / close) * (1 - fee_rate)
            balance = 0.0
            position = 1
            trade_count += 1
            print(f"{date} | 🔴 매수 | 체결가: {close:,.2f} | 획득 BTC: {btc_amount:.4f}")
            
        # 종가가 20일 이동평균선보다 낮고(하락세), 현재 비트코인을 보유하고 있다면 '전량 매도'
        elif position == 1 and close < ma20:
            # 수수료를 뺀 만큼만 달러(USDT)로 획득
            balance = (btc_amount * close) * (1 - fee_rate)
            btc_amount = 0.0
            position = 0
            trade_count += 1
            print(f"{date} | 🔵 매도 | 체결가: {close:,.2f} | 획득 USDT: {balance:,.2f}")

    if trade_count == 0:
        print("조건에 맞는 거래 내역이 없습니다.")
        
    # 최종 자산 가치 계산 (마지막 날까지 코인을 들고 있다면 현재 종가로 매도했다고 가정, 수수료 반영)
    if position == 0:
        final_balance = balance
    else:
        final_balance = (btc_amount * df['Close'].iloc[-1]) * (1 - fee_rate)
    
    # 수익률 계산
    return_rate = ((final_balance - initial_balance) / initial_balance) * 100
    
    print(f"\n초기 원금: ${initial_balance:,.2f}")
    print(f"최종 원금: ${final_balance:,.2f}")
    
    # 수익률 양수/음수에 따른 색상/기호 표시
    if return_rate > 0:
        print(f"총 수익률: +{return_rate:.2f}% 📈 (수익 발생!)")
    elif return_rate < 0:
        print(f"총 수익률: {return_rate:.2f}% 📉 (손실 발생!)")
    else:
        print(f"총 수익률: {return_rate:.2f}% ➖")
    print("================================================================")

if __name__ == "__main__":
    main()
