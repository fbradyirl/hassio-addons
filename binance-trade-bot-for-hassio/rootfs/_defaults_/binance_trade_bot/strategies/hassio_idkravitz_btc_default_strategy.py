import json
import logging
import os
import sys
import traceback
from datetime import datetime, timezone

from binance_trade_bot.models import Trade
from binance_trade_bot.strategies.default_strategy import Strategy


class Strategy(Strategy):
    def initialize(self):
        super().initialize()
        self.scount_loop_count = 0
        self.ha_update_loop_count = 0
        self.fetch_eur_balance = True
        self.fetch_usd_balance = False

    def scout(self):
        """
        Scout for potential jumps from the current coin to another coin
        """
        block_print()
        super().scout()
        enable_print()

        try:
            current_coin = self.db.get_current_coin()
            self.log_scout(current_coin)

            # Update HA sensor AFTER doing the bot functions so that any breakage in HA won't affect trading.
            # E.g. HA API changes, etc.
            self.update_ha_sensor(current_coin)
        except:  # pylint: disable=broad-except
            self.logger.error("Unexpected Error Updating HA sensor.")
            # Only log last line as that will fit in Telegram notification perhaps
            error_last_line = traceback.format_exc().split('\n')[-1]
            self.logger.error(error_last_line)

    def bridge_scout(self):
        super().bridge_scout()

    def log_scout(self, current_coin, wait_iterations=600, notification=False):
        """
        Log each scout every X times. This will prevent logs getting spammed.
        """

        if self.scount_loop_count in [0, wait_iterations]:
            # Log the current coin+Bridge, so users can see *some* activity and not think the bot has
            # stopped. Don't send to notification service
            self.logger.info(f"Scouting... current: {current_coin + self.config.BRIDGE}", notification=notification)
            self.scount_loop_count = 0
        # Log a dot per iteration to show some progress.
        print(". ", end='\r')

        self.scount_loop_count += 1

    def update_ha_sensor(self, current_coin, wait_iterations=30):
        """
        Update the Home Assistant sensor with new data every 30 seconds.
        """
        if self.ha_update_loop_count == wait_iterations:
            self.ha_update_loop_count = 0
            total_balance_usdt = 0
            total_coin_in_btc = 0
            total_balance_eur = 0
            attributes = {}
            attributes['bridge'] = self.config.BRIDGE_SYMBOL
            attributes['current_coin'] = str(current_coin).replace("<", "").replace(">", "")
            attributes['wallet'] = {}

            for asset in self.manager.binance_client.get_account()["balances"]:
                if float(asset['free']) > 0:
                    asset_value_usd = 0
                    asset_value_in_eur = 0
                    asset_entry = {'balance': float(asset['free'])}

                    if self.fetch_usd_balance:
                        if asset['asset'] not in ['BUSD', 'USDT']:
                            current_price = self.manager.get_ticker_price(asset['asset'] + self.config.BRIDGE_SYMBOL)
                            if isinstance(current_price, float):
                                asset_value_usd = float(asset['free']) * float(current_price)
                            else:
                                self.logger.warning("No price found for current asset={}".format(asset['asset']))
                        else:
                            asset_value_usd = float(asset['free'])

                        total_balance_usdt += asset_value_usd

                        asset_entry['current_price'] = round(current_price)
                        asset_entry['asset_value_us_dollar'] = round(asset_value_usd, 2)

                    # Get total amount in terms of BTC amount
                    asset_value_in_btc = self.get_btc_amount(coin_symbol=asset['asset'], coin_total=asset['free'])
                    total_coin_in_btc += asset_value_in_btc
                    asset_entry['asset_value_in_btc'] = round(asset_value_in_btc, 6)

                    if self.fetch_eur_balance:
                        # Get total amount in terms of BTC amount
                        asset_value_in_eur = self.get_btc_amount_in_euro(btc=asset_value_in_btc)
                        total_balance_eur += asset_value_in_eur
                        asset_entry['asset_value_in_eur'] = round(asset_value_in_eur, 2)

                    if asset_value_usd > 1 or asset_value_in_eur > 1:
                        # Only add this coin if it has value over a euro or dollar
                        attributes['wallet'][asset['asset']] = asset_entry

            with self.db.db_session() as session:
                try:
                    trade = session.query(Trade).order_by(Trade.datetime.desc()).limit(1).one().info()
                    if trade:
                        attributes['last_transaction_attempt'] = datetime.strptime(trade['datetime'],
                                                                                   "%Y-%m-%dT%H:%M:%S.%f").replace(
                            tzinfo=timezone.utc).astimezone(tz=None).strftime("%d/%m/%Y %H:%M:%S")
                except:
                    pass

            if self.fetch_usd_balance:
                attributes['total_balance_usdt'] = round(total_balance_usdt, 0)
            if self.fetch_eur_balance:
                attributes['total_balance_eur'] = round(total_balance_eur, 0)
                
            attributes['last_sensor_update'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            attributes['sensor_update_interval'] = wait_iterations
            attributes['unit_of_measurement'] = 'BTC'
            attributes['icon'] = 'mdi:bitcoin'
            data = {
                'state': round(total_coin_in_btc, 6),
                'attributes': attributes
            }
            os.system("/scripts/update_ha_sensor.sh '" + str(json.dumps(data)) + "'")

        self.ha_update_loop_count += 1

    def get_btc_amount(self, coin_symbol, coin_total):
        """
        Get amount of a coin in BTC terms
        """
        btc_coins = 0

        if coin_symbol not in ['BUSD', 'USDT']:
            # Only check value if not in bridge coin.
            try:
                current_coin_price_in_btc = self.manager.get_ticker_price(coin_symbol + "BTC")
                btc_coins = float(current_coin_price_in_btc) * float(coin_total)
            except:
                # Pretty unlikely since all coins trade with BTC
                self.logger.warning(
                    "No price found for current coin + BTC={}".format(coin_symbol + "BTC"),
                    notification=False)
                pass
        elif coin_symbol == 'USDT':
            btc_to_usdt_price = self.manager.get_ticker_price("BTCUSDT")
            btc_coins = float(coin_total) / float(btc_to_usdt_price)

        return btc_coins

    def get_btc_amount_in_euro(self, btc):
        """
        Convert BTC to Euro value
        """
        current_coin_price_in_eur = self.manager.get_ticker_price("BTCEUR")
        return float(current_coin_price_in_eur) * float(btc)


def block_print():
    """
    Block print command working.
    """
    sys.stdout = open(os.devnull, 'w')


def enable_print():
    """
    Restore print command working.
    """
    sys.stdout = sys.__stdout__
