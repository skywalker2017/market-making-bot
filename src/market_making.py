import time
import traceback
from src.utils import (
    place_order,
    cancel_all_orders,
    cancel_list_of_orders,
    calculate_order_size,
    get_dynamic_sleep_time,
    get_dynamic_volatilit,
    calculate_order_sizes,
    get_price_step_percentage,
    fetch_account_balance,
    calculate_percentage_change,
    get_num_of_orders,
    get_order_book,
    get_buy_price_in_spread,
    get_sell_price_in_spread,
    get_target_price,
)

buy_order_ids = []
sell_order_ids = []
SYMBOL = "itx_usdt"
BTC_SYMBOL = "btc_usdt"


def market_making(
    max_order_size,
    min_order_size,
    num_orders=10,
    base_price_step_percentage=0.00009,
):
    try:
        initial_balance = fetch_account_balance()
        print("initial_balance", initial_balance)
        initial_usdt_balance = (
            initial_balance["usdt"]["free"] + initial_balance["usdt"]["locked"]
        )
        initial_safi_balance = (
            initial_balance["itx"]["free"] + initial_balance["itx"]["locked"]
        )

        while True:
            try:
                order_book = get_order_book(SYMBOL)
                print("order_book", order_book)

                balance = fetch_account_balance()

                usdt_balance = balance["usdt"]["free"] + balance["usdt"]["locked"]
                safi_balance = balance["itx"]["free"] + balance["itx"]["locked"]

                usdt_change = calculate_percentage_change(
                    initial_usdt_balance, usdt_balance
                )
                safi_change = calculate_percentage_change(
                    initial_safi_balance, safi_balance
                )

                # Check if changes exceed the pause thresholds
                # if usdt_change < -10:
                #     usdt_pause = True
                # if safi_change < -10:
                #     safi_pause = True

                # Check if changes have recovered
                if usdt_change > -1:
                    usdt_pause = False
                if safi_change > -1:
                    safi_pause = False

                if order_book["result"] == "true":
                    # Example of data: {'symbol': 'safi_usdt', 'askPrice': '0.055', 'askQty': '78.43', 'bidQty': '724.1', 'bidPrice': '0.054761'
                    data = order_book["data"]
                    # The price a buyer is willing to pay
                    bid_price = float(data["bidPrice"])
                    # The price a seller is willing to accept
                    ask_price = float(data["askPrice"])

                    target_price = get_target_price()
                    spread = 0.01

                    if target_price < bid_price:
                        base_buy_price = bid_price * (1 - spread)
                        base_sell_price = ask_price * (1 - spread)
                    elif target_price > ask_price:
                        base_buy_price = bid_price * (1 + spread)
                        base_sell_price = ask_price * (1 + spread)
                    else:
                        base_buy_price = bid_price * (1 + spread)
                        base_sell_price = ask_price * (1 - spread)

                    # Calculate market volatility
                    current_volatility = get_dynamic_volatilit(60)

                    # Dynamic Spread: More sophisticated and responsive strategy that adapts to market volatility.
                    # spread = calculate_dynamic_spread(current_volatility)

                    # Check if there is other self made orders
                    current_orders_number = get_num_of_orders()
                    # if So cancel only the orders in the list
                    if current_orders_number > num_orders:
                        cancel_list_of_orders(SYMBOL, sell_order_ids)
                        cancel_list_of_orders(SYMBOL, buy_order_ids)
                    # if Not Cancel All Orders for fast exwcution
                    elif current_orders_number <= num_orders:
                        cancel_all_orders(SYMBOL)
                        sell_order_ids.clear()
                        buy_order_ids.clear()

                    # best_prices = get_best_price()
                    # best_sell_price = best_prices["best_sell"]
                    # best_buy_price = best_prices["best_buy"]
                    # best_sell_price = base_sell_price

                    # Get the best prices for selling and buying for a low market
                    best_buy_price = get_buy_price_in_spread()
                    best_sell_price = get_sell_price_in_spread()

                    # Get the best prices for selling and buying for a low market
                    best_buy_price = get_buy_price_in_spread()
                    best_sell_price = base_sell_price

                    buy_total_order_size = calculate_order_size(
                        "buy",
                        current_volatility,
                        max_order_size,
                        min_order_size,
                    )

                    buy_order_sizes = calculate_order_sizes(
                        buy_total_order_size, num_orders
                    )

                    sell_total_order_size = calculate_order_size(
                        "sell",
                        current_volatility,
                        max_order_size,
                        min_order_size,
                    )

                    sell_order_sizes = calculate_order_sizes(
                        sell_total_order_size, num_orders
                    )

                    # A loop for placing multiple orders
                    for i in range(num_orders):
                        price_step_percentage = get_price_step_percentage(
                            i, base_price_step_percentage
                        )

                        # BUY Orders
                        if not usdt_pause:
                            if safi_pause:
                                best_buy_price = get_buy_price_in_spread()
                            else:
                                best_buy_price = base_buy_price

                            if i == 0:
                                buy_price = best_buy_price
                            else:
                                buy_price = best_buy_price * (
                                    1 - i * price_step_percentage
                                )

                            res = place_order(
                                SYMBOL,
                                "buy_maker",
                                buy_order_sizes[i],
                                buy_price,
                            )
                            if res["msg"] == "Success":
                                buy_order_ids.append(res["data"]["order_id"])

                        # SEll Orders
                        if not safi_pause:

                            if i == 0:
                                sell_price = best_sell_price
                                print(f"Best Sell Order: {best_sell_price}")
                            else:
                                sell_price = base_sell_price * (
                                    1 + i * price_step_percentage
                                )
                            res = place_order(
                                SYMBOL, "sell_maker", sell_order_sizes[i], sell_price
                            )
                            if res["msg"] == "Success":
                                sell_order_ids.append(res["data"]["order_id"])

                time.sleep(get_dynamic_sleep_time(current_volatility))

            except Exception as e:
                print(f"An error occurred: {e}")
                traceback.print_exc()
                time.sleep(10)
    except KeyboardInterrupt:
        cancel_list_of_orders(SYMBOL, buy_order_ids)
        cancel_list_of_orders(SYMBOL, sell_order_ids)
