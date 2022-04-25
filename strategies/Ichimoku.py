import pandas
import pandas as pd
from blankly import StrategyState


class Ichimoku():

    @staticmethod
    def init(symbol, state: StrategyState):
        interface = state.interface
        resolution = state.resolution
        variables = state.variables

        variables['history'] = interface.history(symbol, 800, resolution)
        variables['has_bought'] = False

    @staticmethod
    def bar_event(bar, symbol, state: StrategyState):
        state.variables["history"].append(bar, ignore_index=True)
        print(state.variables["history"])
        df: pandas.DataFrame = state.variables["history"]
        print(df.tail())

        tenkanSen = Ichimoku.tenkanSen(df)
        kijunSen = Ichimoku.kijunSen(df)
        senkouSpanA = Ichimoku.senkouSpanA(df)
        senkouSpanB = Ichimoku.senkouSpanB(df)
        chikouSpan = Ichimoku.chikouSpan(df)
        # print(f"{tenkanSen}; {kijunSen}; {senkouSpanA}; {senkouSpanB}; {chikouSpan}")

        if state.variables["has_bought"]:
            if tenkanSen.iloc(-1) < kijunSen.iloc(-1) and df.close.iloc(-1) < kijunSen.iloc(-1):
                state.interface.market_order(symbol, 'sell', 1)
        else:
            if tenkanSen.iloc(-1) > kijunSen.iloc(-1) and df.close.iloc(-1) > kijunSen.iloc(-1) and df.low.iloc(-1) > kijunSen.iloc(-1):
                state.interface.market_order(symbol, 'buy', 1)

    @staticmethod
    def tenkanSen(df):
        period9High = pd.Series(df.high).rolling(9).max()
        perdiod9Low = pd.Series(df.low).rolling(9).min()

        return (period9High + perdiod9Low) / 2

    @staticmethod
    def kijunSen(df):
        period26High = pd.Series(df.high).rolling(26).max()
        period26Low = pd.Series(df.low).rolling(26).min()

        return (period26High + period26Low) / 2

    @staticmethod
    def senkouSpanA(df):
        return ((Ichimoku.tenkanSen(df) + Ichimoku.kijunSen(df)) / 2).shift(26)

    @staticmethod
    def senkouSpanB(df):
        period52High = pd.Series(df.high).rolling(52).max()
        period52Low = pd.Series(df.low).rolling(52).min()

        return ((period52High + period52Low) / 2).shift(26)

    @staticmethod
    def chikouSpan(df):
        return pd.Series(df.close).shift(-26)
