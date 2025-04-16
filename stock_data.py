import yfinance as yf

def get_ohlc_for_stock(symbol):
    if not symbol.endswith(".NS"):
        symbol = symbol + ".NS"

    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="5d")

        if hist.empty or len(hist) < 2:
            return None

        last_two = hist.tail(2)

        ohlc_list = []
        for index, row in last_two.iterrows():
            ohlc_list.append({
                "Date": index.strftime("%Y-%m-%d"),
                "High": round(row["High"], 2),
                "Low": round(row["Low"], 2),
                "Close": round(row["Close"], 2)
            })

        return ohlc_list
    except Exception as e:
        print(f"❌ Error fetching OHLC for {symbol}: {e}")
        return None
