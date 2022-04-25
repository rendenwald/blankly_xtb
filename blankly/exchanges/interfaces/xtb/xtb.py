from blankly.exchanges.exchange import Exchange
from blankly.exchanges.interfaces.xtb.xtb_api import XTBApi
from blankly.exchanges.interfaces.xtb.xtb_state import XTBState
from blankly.exchanges.auth.auth_constructor import AuthConstructor


class XTB(Exchange):
    def __init__(self, portfolio_name=None, keys_path="keys.json", settings_path=None):
        Exchange.__init__(self, "xtb", portfolio_name, settings_path)

        # Load the auth from the keys file
        auth = AuthConstructor(keys_path, portfolio_name, 'xtb', ['ACCOUNT_ID', 'PASSWORD', 'sandbox'])

        sandbox = super().evaluate_sandbox(auth)

        calls = XTBApi(account_id=auth.keys['ACCOUNT_ID'],
                       password=auth.keys['PASSWORD'],
                       sandbox=sandbox,
                       balanceFun=XTBState.balance)

        # Always finish the method with this function
        super().construct_interface_and_cache(calls)

    def get_exchange_state(self):
        return self.interface.products

    def get_asset_state(self, symbol):
        return self.interface.get_account(symbol)

    def get_direct_calls(self) -> XTBApi:
        return self.calls
