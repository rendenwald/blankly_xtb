import sys
import pandas as pd

from blankly.exchanges.interfaces.exchange_interface import ExchangeInterface
from blankly.exchanges.interfaces.xtb.xtb_api import XTBApi
from blankly.exchanges.interfaces.xtb.xtb_state import XTBState
from blankly.exchanges.orders.limit_order import LimitOrder
from blankly.exchanges.orders.market_order import MarketOrder
from blankly.utils import utils as utils
from blankly.utils.exceptions import APIException, InvalidOrder


class XTBInterface(ExchangeInterface):
    def __init__(self, exchange_name: str, authenticated_api: XTBApi):
        self.products = None
        self.state = XTBState()
        super().__init__(exchange_name, authenticated_api,
                         valid_resolutions=[60, 300, 900, 1800, 3600, 14400, 86400, 604800, 2592000])

        self.products = self.get_products()
        current_user_data = self.calls.getCurrentUserDataCommand()["returnData"]
        self.currency = current_user_data["currency"]

    def init_exchange(self):
        """Collect info about possible symbols"""
        self.state.balance = self.calls.getMarginLevelCommand()["returnData"]

    @property
    def cash(self):
        # return self.state.balance
        return self.state.balance["margin_free"]

    @utils.enforce_base_asset
    def get_account(self, symbol=None) -> utils.AttributeDict:
        """
        {
            "balance": 995800269.43,
            "credit": 1000.00,
            "currency": "PLN",
            "equity": 995985397.56,
            "margin": 572634.43,
            "margin_free": 995227635.00,
            "margin_level": 173930.41
        }
        """
        account = utils.AttributeDict({})
        symbol = super().get_account(symbol=symbol)

        # generate dict for all possible instruments
        for product in self.products:
            account[product["symbol"]] = utils.AttributeDict({
                'available': 0.0,
                'hold': 0.0
            })

        # generate dict for account currency
        account[self.state.balance["currency"]] = utils.AttributeDict({
            'available': float(self.state.balance["margin_free"]),
            'hold': float(self.state.balance["equity"]) - float(self.state.balance["margin_free"])
        })

        # don't know why this should be added
        if "USD" not in account:
            account["USD"] = utils.AttributeDict({
                'available': 0.0,
                'hold': 0.0
            })

        if symbol is not None:
            try:
                return account[symbol]
            except KeyError as error:
                raise KeyError("Symbol not found") from error

        return account

    def get_products(self):
        """
        This is a section of the symbols array
        [
            {
                "ask": 4000.0,
                "bid": 4000.0,
                "categoryName": "Forex",
                "contractSize": 100000,
                "currency": "USD",
                "currencyPair": true,
                "currencyProfit": "SEK",
                "description": "USD/PLN",
                "expiration": null,
                "groupName": "Minor",
                "high": 4000.0,
                "initialMargin": 0,
                "instantMaxVolume": 0,
                "leverage": 1.5,
                "longOnly": false,
                "lotMax": 10.0,
                "lotMin": 0.1,
                "lotStep": 0.1,
                "low": 3500.0,
                "marginHedged": 0,
                "marginHedgedStrong": false,
                "marginMaintenance": null,
                "marginMode": 101,
                "percentage": 100.0,
                "precision": 2,
                "profitMode": 5,
                "quoteId": 1,
                "shortSelling": true,
                "spreadRaw": 0.000003,
                "spreadTable": 0.00042,
                "starting": null,
                "stepRuleId": 1,
                "stopsLevel": 0,
                "swap_rollover3days": 0,
                "swapEnable": true,
                "swapLong": -2.55929,
                "swapShort": 0.131,
                "swapType": 0,
                "symbol": "USDPLN",
                "tickSize": 1.0,
                "tickValue": 1.0,
                "time": 1272446136891,
                "timeString": "Thu May 23 12:23:44 EDT 2013",
                "trailingEnabled": true,
                "type": 21
            }
        ]
        """
        self.products_full = self.calls.getAllSymbolsCommand()["returnData"]
        products = list()
        for idx, product in enumerate(self.products_full):
            # Rename needed
            dictionary = dict()
            dictionary["symbol"] = product["symbol"]
            dictionary["base_asset"] = product["description"]
            dictionary["quote_asset"] = product["description"]
            dictionary["base_min_size"] = product["lotMin"]
            dictionary["base_max_size"] = product["lotMax"]
            dictionary["base_increment"] = product["lotStep"]
            products.append(dict(dictionary))
        return products

    def get_product_history(self, symbol, epoch_start, epoch_stop, resolution):
        """
        {
            "close": 1.0,
            "ctm": 1389362640000,
            "ctmString": "Jan 10, 2014 3:04:00 PM",
            "high": 6.0,
            "low": 0.0,
            "open": 41848.0,
            "vol": 0.0
        }
        """
        product_history = self.calls.getChartRangeRequestCommand(
            symbol=symbol, start=epoch_start * 1000, end=epoch_stop * 1000, period=int(resolution / 60))["returnData"][
            "rateInfos"]

        df_product_history = pd.DataFrame.from_records(product_history)
        df_product_history.rename(columns={'ctm': 'time', 'vol': 'volume'}, inplace=True)
        df_product_history["time"] = df_product_history["time"] * 0.001
        df_product_history["close"] = df_product_history["open"] + df_product_history["close"]
        df_product_history["high"] = df_product_history["open"] + df_product_history["high"]
        df_product_history["low"] = df_product_history["open"] + df_product_history["low"]
        df_product_history[['time']] = df_product_history[['time']].astype(int)
        df_product_history[['low', 'high', 'open', 'close', 'volume']] = df_product_history[['low', 'high', 'open', 'close', 'volume']].astype(float)

        print(df_product_history.tail())
        return df_product_history

    def market_order(self,
                     symbol: str,
                     side: str,
                     size: float) -> MarketOrder:
        """
        Used for buying or selling market orders
        Args:
            symbol: asset to buy
            side: buy/sell
            size: desired amount of base asset to use
        """
        raise NotImplementedError

    def limit_order(self,
                    symbol: str,
                    side: str,
                    price: float,
                    size: float) -> LimitOrder:
        """
        Used for buying or selling limit orders
        Args:
            symbol: asset to buy
            side: buy/sell
            price: price to set limit order
            size: amount of asset (like BTC) for the limit to be valued
        """
        raise NotImplementedError

    def cancel_order(self,
                     symbol: str,
                     order_id: str) -> dict:
        """
        Cancel an order on a particular symbol & order id

        Args:
            symbol: This is the asset id that the order is under
            order_id: The unique ID of the order.

        TODO add return example
        """
        raise NotImplementedError

    def get_open_orders(self,
                        symbol: str = None) -> list:
        """
        List open orders.
        Args:
            symbol (optional) (str): Asset such as BTC-USD
        TODO add return example
        """
        raise NotImplementedError

    def get_order(self,
                  symbol: str,
                  order_id: str) -> dict:
        """
        Get a certain order
        Args:
            symbol: Asset that the order is under
            order_id: The unique ID of the order.
        TODO add return example
        """
        raise NotImplementedError

    def get_fees(self, symbol: str) -> dict:
        """
        Get market fees
        """
        return {
            'maker_fee_rate': 0.002,
            'taker_fee_rate': 0.002
        }

    def get_order_filter(self, symbol: str):
        """
        Find order limits for the exchange
        Args:
            symbol: The asset such as (BTC-USD, or MSFT)
        """
        product = next((product for product in self.products_full if product["symbol"] == symbol), None)
        if not product:
            raise KeyError(f"Not found: {symbol}")
        price = product["ask"]

        resp = dict()
        resp['symbol'] = product["symbol"]
        resp['base_asset'] = product["symbol"]
        resp['quote_asset'] = product["currency"]
        resp['max_orders'] = product["instantMaxVolume"]
        resp['limit_order'] = {
            "base_min_size": float(product['lotMin']),
            "base_max_size": float(product['lotMax']),
            "base_increment": float(product['lotStep']),
            "price_increment": float(product["tickSize"]),
            "min_price": float(product["tickSize"]),
            "max_price": sys.maxsize
        }
        resp['market_order'] = {
            "fractionable": False,
            "base_min_size": float(product['lotMin']),
            "base_max_size": float(product['lotMax']),
            "base_increment": float(product['lotStep']),
            "quote_increment": float(product["tickSize"]),
            "buy": {
                "min_funds": float(product['lotMin']) * price,
                "max_funds": float(product['lotMax']) * price
            },
            "sell": {
                "min_funds": float(product['lotMin']) * price,
                "max_funds": float(product['lotMax']) * price
            }
        }
        return resp

    def get_price(self, symbol: str) -> float:
        """
        Returns just the price of a symbol.
        """
        symbol_data = self.calls.getSymbolCommand(symbol=symbol)["returnData"]
        return float(symbol_data["ask"])
