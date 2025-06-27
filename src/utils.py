import logging
import numpy as np
from lbank.old_api import BlockHttpClient
from datetime import datetime, timedelta, timezone
import random
import os
from dotenv import load_dotenv

load_dotenv()

client = BlockHttpClient(
    sign_method="HMACSHA256",
    api_key=os.getenv("LBANK_API_KEY"),
    api_secret=os.getenv("LBANK_API_SECRET"),
    base_url="https://www.lbkex.net/",
    log_level=logging.ERROR,
)

pair = "itx_usdt"
token_symbol = "itx"


def get_order_book(symbol):
    """
    Fetch the order book for a given symbol.

    Parameters:
    - symbol: Trading pair symbol (e.g., pair)

    Returns:
    - dict: Order book data
    """
    api_url = "v2/supplement/ticker/bookTicker.do"
    payload = {"symbol": symbol}
    return client.http_request("get", api_url, payload=payload)


def get_buy_price_in_spread():
    order_book = get_order_book(pair)
    ask_price = float(order_book["data"]["askPrice"])
    # Calculate the maximum allowable ask price based on a 2% spread
    max_ask_price = ask_price * 0.98
    return max_ask_price


def get_sell_price_in_spread():
    order_book = get_order_book(pair)
    bid_price = float(order_book["data"]["bidPrice"])
    # Calculate the maximum allowable ask price based on a 2% spread
    max_ask_price = bid_price * 1.02
    return max_ask_price


def place_order(symbol, side, amount, price=None):
    """
    Place an order on the exchange.

    Parameters:
    - symbol: Trading pair symbol (e.g., pair)
    - side: Order side ("buy_maker" or "sell_maker")
    - price: Price at which to place the order
    - amount: Amount of the asset to trade

    Returns:
    - dict: Response from the exchange
    """

    path = "v2/create_order.do"

    payload = {
        "symbol": symbol,
        "type": side,
        "amount": amount,
    }

    if price is not None:
        payload["price"] = price

    print(f"payload: {payload}")

    return client.http_request("post", path, payload=payload)


def cancel_all_orders(symbol):
    """
    Cancel all orders for a given symbol.

    Parameters:
    - symbol: Trading pair symbol (e.g., pair)

    Returns:
    - dict: Response from the exchange
    """

    path = "v2/supplement/cancel_order_by_symbol.do"
    payload = {"symbol": symbol}
    return client.http_request("POST", path, payload=payload)


def cancel_one_order(symbol, order_id):
    """
    Cancel One order

    Parameters:
    - symbol: Trading pair symbol (e.g., pair)
    - order_id : Order of the id that you need to cancel

    Returns:
    - dict: Response from the exchange
    """
    path = "v2/supplement/cancel_order.do"
    payload = {"symbol": symbol, "orderId": order_id}
    return client.http_request("POST", path, payload=payload)


def cancel_list_of_orders(symbol, order_ids):
    """
    Cancel a List of orders used to not intrrupt the other orders

    Parameters:
    - symbol: Trading pair symbol (e.g., pair)
    - order_ids : List of Order ids that you need to cancel

    """
    if not order_ids:
        return
    for order_id in order_ids:
        print(f"cancel_one_order: {cancel_one_order(symbol, order_id)}")


def get_current_price(symbol):
    """
    Get the current price for a given symbol.

    Parameters:
    - symbol: Trading pair symbol (e.g., pair)

    Returns:
    - float: Current price of the trading pair
    """
    path = "v2/supplement/ticker/price.do"
    payload = {"symbol": symbol}
    res = client.http_request("GET", path, payload=payload)
    if res["result"] == True:
        current_price = res["data"][0]["price"]
        return float(current_price)
    else:
        raise Exception(
            "Failed to get current price: " + res.get("error", "Unknown error")
        )


def calculate_order_size(
    order_type, qty, max_order_size, min_order_size, risk_percentage=None
):
    """
    Calculate the order size based on risk management.

    Parameters:
    - order_type: The type of order ('buy' or 'sell').
    - volatility: The current market volatility.
    - max_order_size: The maximum allowed size for an order.
    - min_order_size: The minimum allowed size for an order.
    - risk_percentage: Optional risk percentage of the account balance to use per trade.

    Returns:
    - order_size: The calculated order size.
    """
    # current_price = get_current_price(pair)

    # # Fetch account balance
    # account_balances = fetch_account_balance()

    # if order_type == "sell":
    #     # Use the token_symbol balance for sell orders
    #     asset_balance = account_balances[token_symbol]["free"]
    # elif order_type == "buy":
    #     # Use the USDT balance for buy orders
    #     usdt_balance = account_balances["usdt"]["free"]
    #     # Convert USDT balance to token_symbol
    #     asset_balance = usdt_balance / current_price

    # # Optionally apply a risk percentage if provided
    # if risk_percentage is not None:
    #     risk_amount = asset_balance * risk_percentage
    # else:
    #     risk_amount = asset_balance  # Use the full balance without risk adjustment

    # # Ensure max_order_size does not exceed the available balance
    # if max_order_size > risk_amount:
    #     max_order_size = risk_amount

    # Adjust order size based on volatility
    # volatility_adjustment = 1 / (volatility + 1)

    # Calculate the raw order size
    random_multiplier = random.uniform(0.5, 1.5)
    raw_order_size = (
        qty * random_multiplier
    )

    # Ensure the order size is within defined limits
    order_size = max(min(raw_order_size, max_order_size), min_order_size)
    if order_size == max_order_size:
        order_size = order_size + random.uniform(-5, 5)
    if order_size == min_order_size:
        order_size = order_size + random.uniform(-0.5, 0.5)

    return order_size


def get_dynamic_sleep_time():
    return 20
    """
    Get dynamic sleep time based on market volatility.

    Parameters:
    - volatility: Current market volatility

    Returns:
    - int: Dynamic sleep time in seconds
    """

    # Initialize parameters
    base_sleep_time = 8  # Base sleep time in seconds
    max_sleep_time = 20  # Maximum sleep time in seconds
    min_sleep_time = 1  # Minimum sleep time in seconds

    # Adjust sleep time based on volatility
    if volatility > 0.05:  # High volatility threshold
        sleep_time = base_sleep_time / 2
    elif volatility < 0.02:  # Low volatility threshold
        sleep_time = base_sleep_time * 2
    else:
        sleep_time = base_sleep_time

    # Ensure sleep time is within limits
    sleep_time = max(min(sleep_time, max_sleep_time), min_sleep_time)

    return sleep_time


def calculate_percentage_change(initial_balance, current_balance):
    change = ((current_balance - initial_balance) / initial_balance) * 100
    return change


def fetch_historical_prices(period):
    """
    Fetch historical prices for a given period.

    Parameters:
    - period: Number of minutes of historical data to fetch

    Returns:
    - list: Historical price data
    """
    path = "v2/kline.do"
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(minutes=period)

    # Convert dates to timestamps in seconds
    end_timestamp = int(end_date.timestamp())
    start_timestamp = int(start_date.timestamp())

    payload = {
        "symbol": pair,
        "type": "minute1",
        "size": period,
        "time": start_timestamp,
    }


def calculate_price_changes(price_data):
    """
    Calculate price changes from historical price data.

    Parameters:
    - price_data: List of historical prices

    Returns:
    - numpy.array: Array of price changes
    """
    # Calculate price changes from historical price data
    prices = np.array(price_data)
    price_changes = np.diff(prices) / prices[:-1]
    return price_changes


def calculate_standard_deviation(price_changes):
    """
    Calculate the standard deviation of price changes.

    Parameters:
    - price_changes: Array of price changes

    Returns:
    - float: Standard deviation of price changes
    """
    return np.std(price_changes)

def calculate_target_price(btc_price):
    # Define the ranges
    btc_min = 0
    btc_max = 240000
    btc_mid = 120000
    
    # Define target price bounds
    target_min = 0
    target_max = 2
    
    # First, normalize BTC price to be between 0 and 1
    normalized_btc = btc_price / btc_max
    
    # Calculate how far we are from the center (0.5 when normalized)
    # This will be 0 at the center and approach 0.5 at the extremes
    distance_from_center = abs(normalized_btc - 0.5)
    
    # Calculate a fluctuation factor that's highest at the center (100,000)
    # and lowest at the extremes (0 and 200,000)
    # This creates a parabolic curve: 1.0 at center, 0.0 at extremes
    fluctuation_factor = 1.0 - (4 * distance_from_center * distance_from_center)
    
    # Calculate base target price - linear relationship that equals 1.0 at 100,000
    base_target_price = normalized_btc * 2.0
    
    # Apply a symmetric fluctuation that creates a curve
    # The fluctuation is applied as a deviation from the linear relationship
    # We use a sine-like curve: higher in the middle, lower at extremes
    max_deviation = 1.5  # Maximum deviation from linear relationship
    
    # Calculate the deviation amount based on position
    # This creates a curve that's 0 at 0, 0 at 100,000, and 0 at 200,000
    # With maximum effect at 50,000 and 150,000
    deviation = max_deviation * fluctuation_factor * (normalized_btc - 0.5)
    
    # Apply the deviation to create the final target price
    target_price = base_target_price + deviation
    
    # Ensure target price is exactly 1.0 at BTC price of 100,000
    if btc_price == btc_mid:
        target_price = 1.0
    
    # Ensure target price stays within bounds
    target_price = max(target_min, min(target_max, target_price))
    
    return target_price
    

def get_target_price():
    btc_price = get_current_price("btc_usdt")
    return calculate_target_price(btc_price)


def get_dynamic_volatilit(period):
    """
    Determain the volatilit of the pair through a period of time.
    Keeps increasing the period if the volatilit is too low.

    Parameters:
    - period: Number of minutes

    Returns:
    - float: volatilit
    """
    # Random between 0.1 and 0.5
    random_volatility = random.uniform(0.1, 0.5)
    return random_volatility
    # price_data = fetch_historical_prices(period)  # In minutes
    # price_changes = calculate_price_changes(price_data)
    # current_volatility = calculate_standard_deviation(price_changes)

    # if current_volatility == 0:
    #     period += 60
    #     get_dynamic_volatilit(period)

    # return current_volatility


def calculate_order_sizes(total_order_size, num_orders):
    order_sizes = []
    remaining_percentage = 0.70
    first_order_size = total_order_size * 0.30

    order_sizes.append(first_order_size)

    for i in range(1, num_orders):
        next_order_size = total_order_size * (remaining_percentage * 0.3)
        order_sizes.append(next_order_size)
        remaining_percentage *= 0.7

    # Return a list of order Sizes where the first size is the larges
    return order_sizes
    # Return a list of order Sizes where the last size is the larges
    # return order_sizes.reverse()


def get_price_step_percentage(order_num, base_price_step_percentage):
    if order_num < 9:
        return base_price_step_percentage
    elif order_num < 12:
        return base_price_step_percentage * 2.5
    else:
        return base_price_step_percentage * 4


def fetch_account_balance():
    """
    Fetch account balance for specified assets.

    Returns:
    - dict: Account balances for targeted assets
    """
    path = "v2/supplement/user_info_account.do"
    res = client.http_request("POST", path)
    if res["result"] == "true":
        balances = res["data"]["balances"]
        targeted_assets = {"usdt": None, token_symbol: None}
        for balance in balances:
            if balance["asset"] in targeted_assets:
                targeted_assets[balance["asset"]] = {
                    "free": float(balance["free"]),
                    "locked": float(balance["locked"]),
                }
            if all(value is not None for value in targeted_assets.values()):
                break
        return targeted_assets
    else:
        raise Exception(
            "Failed to fetch account balances: " + res.get("msg", "Unknown error")
        )


def calculate_percentage_change(initial_balance, current_balance):
    change = ((current_balance - initial_balance) / initial_balance) * 100
    return change


def get_current_orders():
    """
    Get the current pending orders

    Returns:
    -

    """
    path = "v2/supplement/orders_info_history.do"
    payload = {"symbol": "itx_usdt", "current_page": "1", "page_length": "200"}
    res = client.http_request("POST", path, payload=payload)
    return res


def get_num_of_orders():
    list_of_orders = get_current_orders()["data"]["orders"]
    return len(list_of_orders)
