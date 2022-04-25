import time

from blankly.exchanges.interfaces.xtb.xAPI_XTB import APIClient, APIStreamClient
from blankly.exchanges.interfaces.xtb.xAPI_XTB import DEMO_XAPI_PORT, DEMO_XAPI_STREAMING_PORT
from blankly.exchanges.interfaces.xtb.xAPI_XTB import REAL_XAPI_PORT, REAL_XAPI_STREAMING_PORT
from blankly.exchanges.interfaces.xtb.xAPI_XTB import logger


class XTBApi:
    def __init__(self, account_id: str, password: str, sandbox: bool = False, **stream_kwargs):
        self.account_id = account_id
        self.password = password
        self.client = None

        if not sandbox:
            self.DEFAULT_XAPI_PORT = REAL_XAPI_PORT
            self.DEFAULT_XAPI_STREAMING_PORT = REAL_XAPI_STREAMING_PORT
        else:
            self.DEFAULT_XAPI_PORT = DEMO_XAPI_PORT
            self.DEFAULT_XAPI_STREAMING_PORT = DEMO_XAPI_STREAMING_PORT

        self.stream_client = self._init_session(**stream_kwargs)

    def _init_session(self, tickFun=None, tradeFun=None, profitFun=None,
                      tradeStatusFun=None, balanceFun=None, newsFun=None):
        self.client = APIClient(port=self.DEFAULT_XAPI_PORT)

        # connect to RR socket, login
        response = self.loginCommand(account_id=self.account_id, password=self.password)
        logger.info(str(response))

        # check if user logged in correctly
        if not response['status']:
            print('Login failed. Error code: {0}'.format(response['errorCode']))
            return

        # get ssId from login response
        ssid = response['streamSessionId']

        # create & connect to Streaming socket with given ssID
        # and functions for processing ticks, trades, profit and tradeStatus
        stream_client = APIStreamClient(ssId=ssid, port=self.DEFAULT_XAPI_STREAMING_PORT,
                                        tickFun=tickFun, tradeFun=tradeFun,
                                        profitFun=profitFun, tradeStatusFun=tradeStatusFun,
                                        balanceFun=balanceFun, newsFun=newsFun)
        return stream_client

    def loginCommand(self, account_id, password, appName=''):
        return self.client.commandExecute('login', dict(userId=account_id, password=password, appName=appName))

    def getChartRangeRequestCommand(self, symbol, period, start, end):
        return self.client.commandExecute(
            'getChartRangeRequest', dict(info=dict(
                symbol=symbol, period=period, start=start, end=end))
        )

    def getMarginLevelCommand(self):
        return self.client.commandExecute('getMarginLevel')

    def getAllSymbolsCommand(self):
        return self.client.commandExecute('getAllSymbols')

    def getSymbolCommand(self, symbol):
        return self.client.commandExecute("getSymbol", {"symbol": symbol})

    def getCommissionDefCommand(self, symbol, volume):
        return self.client.commandExecute("getCommissionDef", {"symbol": symbol, "volume": volume})

    def getTickPricesCommand(self, symbol, timestamp=time.time() * 1000):
        response = self.client.commandExecute(
            'getTickPrices', dict(symbols=[symbol], timestamp=timestamp, level=0)
        )
        if not response['returnData']['quotations']:
            logger.error(f"Data was not found for {symbol}")
        return response

    def getBalanceCommand(self):
        return self.client.commandExecute('getBalance')

    def getCurrentUserDataCommand(self):
        return self.client.commandExecute('getCurrentUserData')

    def tradeTransactionStatus(self, order: int):
        return self.client.commandExecute("tradeTransactionStatus", {"order": order})

    def tradeTransaction(self, symbol, price, volume, cmd, type, expiration, order=0,
                         take_profit=0, stop_loss=0, comment='', offset=0):
        return self.client.commandExecute("tradeTransaction", dict(tradeTransInfo={
            'cmd': cmd,
            'customComment': comment,
            'expiration': expiration,
            'offset': offset,
            'order': order,
            'price': price,
            'sl': stop_loss,
            'symbol': symbol,
            'tp': take_profit,
            'type': type,
            'volume': volume
        }))