import time
import traceback
import random
from src.utils import (
    cancel_one_order,
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
        shield_high_price = 1
        shield_low_price = 0.9
        shield_order_ids = []


        while True:
            try:
                order_book = get_order_book(SYMBOL)

                balance = fetch_account_balance()

                usdt_balance = balance["usdt"]["free"] + balance["usdt"]["locked"]
                safi_balance = balance["itx"]["free"] + balance["itx"]["locked"]

                usdt_change = calculate_percentage_change(
                    initial_usdt_balance, usdt_balance
                )
                safi_change = calculate_percentage_change(
                    initial_safi_balance, safi_balance
                )


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
                    bid_qty = float(data["bidQty"])
                    # The price a seller is willing to accept
                    ask_price = float(data["askPrice"])
                    ask_qty = float(data["askQty"])

                    if bid_price > shield_high_price:
                        shield_high_price += 0.1
                        shield_low_price += 0.1
                        cancel_list_of_orders(SYMBOL, shield_order_ids)
                        shield_order_ids = []
                        buy_res = place_order(
                            SYMBOL,
                            "buy",
                            100,
                            shield_low_price,
                        )
                        sell_res = place_order(
                            SYMBOL,
                            "sell",
                            100,
                            shield_high_price,
                        )
                        if sell_res["msg"] == "Success":
                            shield_order_ids.append(sell_res["data"]["order_id"])

                    if bid_price < shield_low_price:
                        shield_high_price -= 0.1
                        shield_low_price -= 0.1
                        cancel_list_of_orders(SYMBOL, shield_order_ids)
                        shield_order_ids = []
                        buy_res = place_order(
                            SYMBOL,
                            "buy",
                            100,
                            shield_low_price,
                        )
                        sell_res = place_order(
                            SYMBOL,
                            "sell",
                            100,
                            shield_high_price,
                        )
                        if sell_res["msg"] == "Success":
                            shield_order_ids.append(sell_res["data"]["order_id"])


                    target_price = get_target_price()
                    print(f"order_book: {order_book}, target_price: {target_price}")

                    spread = random.uniform(0.01, 0.012)
                    gap_ratio = abs(bid_price - ask_price) / ((ask_price + bid_price) / 2)

                    if target_price < bid_price:
                        base_buy_price = bid_price * (1 - spread)
                        base_sell_price = ask_price * (1 - (spread * (1 + gap_ratio)))                            
                        
                        ask_qty = ask_qty / 2
                        bid_qty = bid_qty * 2
                    elif target_price > ask_price:
                        base_buy_price = bid_price * (1 + (spread * (1 + gap_ratio)))
                        base_sell_price = ask_price * (1 + spread)
                        bid_qty = bid_qty / 2
                        ask_qty = ask_qty * 2
                    else:
                        base_buy_price = bid_price * (1 + spread)
                        base_sell_price = ask_price * (1 - spread)

                    if base_buy_price > ask_price:
                        base_buy_price = ask_price
                    if base_sell_price < bid_price:
                        base_sell_price = bid_price

                    # Calculate market volatility
                    current_volatility = get_dynamic_volatilit(60)

                    current_orders_number = get_num_of_orders()

                    buy_total_order_size = calculate_order_size(
                        "buy",
                        ask_qty,
                        max_order_size,
                        min_order_size,
                    )

                    # buy_order_sizes = calculate_order_sizes(
                    #     buy_total_order_size, num_orders
                    # )

                    sell_total_order_size = calculate_order_size(
                        "sell",
                        bid_qty,
                        max_order_size,
                        min_order_size,
                    )

                    # sell_order_sizes = calculate_order_sizes(
                    #     sell_total_order_size, num_orders
                    # )
                    buy_res = place_order(
                        SYMBOL,
                        "buy",
                        buy_total_order_size,
                        base_buy_price,
                    )


                    sell_res = place_order(
                        SYMBOL,
                        "sell",
                        sell_total_order_size,
                        base_sell_price,
                    )
                    if sell_order_ids.__len__() > num_orders:
                        cancel_one_order(SYMBOL, sell_order_ids[0])
                        sell_order_ids.remove(sell_order_ids[0])
                    if buy_order_ids.__len__() > num_orders:
                        cancel_one_order(SYMBOL, buy_order_ids[0])
                        buy_order_ids.remove(buy_order_ids[0])

                    if buy_res["msg"] == "Success":
                        buy_order_ids.append(buy_res["data"]["order_id"])
                    else:
                        print(buy_res)
                    if sell_res["msg"] == "Success":
                        sell_order_ids.append(sell_res["data"]["order_id"])
                    else:
                        print(sell_res)

                    # A loop for placing multiple orders
                    # for i in range(num_orders):
                    #     price_step_percentage = get_price_step_percentage(
                    #         i, base_price_step_percentage
                    #     )

                    #     # BUY Orders
                    #     if not usdt_pause:
                    #         if safi_pause:
                    #             best_buy_price = get_buy_price_in_spread()
                    #         else:
                    #             best_buy_price = base_buy_price

                    #         if i == 0:
                    #             buy_price = best_buy_price
                    #         else:
                    #             buy_price = best_buy_price * (
                    #                 1 - i * price_step_percentage
                    #             )

                    #         res = place_order(
                    #             SYMBOL,
                    #             "buy_maker",
                    #             buy_order_sizes[i],
                    #             buy_price,
                    #         )
                    #         # if res["msg"] == "Success":
                    #         #     buy_order_ids.append(res["data"]["order_id"])

                    #     # SEll Orders
                    #     if not safi_pause:

                    #         if i == 0:
                    #             sell_price = best_sell_price
                    #             print(f"Best Sell Order: {best_sell_price}")
                    #         else:
                    #             sell_price = base_sell_price * (
                    #                 1 + i * price_step_percentage
                    #             )
                    #         res = place_order(
                    #             SYMBOL, "sell_maker", sell_order_sizes[i], sell_price
                    #         )
                    #         if res["msg"] == "Success":
                    #             sell_order_ids.append(res["data"]["order_id"])

                time.sleep(get_dynamic_sleep_time())

            except Exception as e:
                print(f"An error occurred: {e}")
                traceback.print_exc()
                time.sleep(get_dynamic_sleep_time())
    except KeyboardInterrupt:
        cancel_list_of_orders(SYMBOL, buy_order_ids)
        cancel_list_of_orders(SYMBOL, sell_order_ids)
