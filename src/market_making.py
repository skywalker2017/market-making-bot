import time
import traceback
import random
from decimal import Decimal, ROUND_HALF_UP
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
        cancel_all_orders(SYMBOL)

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

                    target_price = get_target_price()
                    print(f"order_book: {order_book}, target_price: {target_price}")

                    # Use Decimal for precise rounding to 2 decimal places
                    ask_price_decimal = Decimal(str(ask_price))
                    bid_price_decimal = Decimal(str(bid_price))
                    
                    # Round to nearest 0.01 and add 0.01 for ask_pressure
                    ask_pressure = float((ask_price_decimal / Decimal('0.01')).quantize(Decimal('1'), rounding=ROUND_HALF_UP) * Decimal('0.01') + Decimal('0.01'))
                    # Round to nearest 0.01 for bid_pressure
                    bid_pressure = float((bid_price_decimal / Decimal('0.01')).quantize(Decimal('1'), rounding=ROUND_HALF_UP) * Decimal('0.01') - Decimal('0.01'))

                    cancel_list_of_orders(SYMBOL, shield_order_ids)
                    shield_order_ids.clear()
                    for i in range(10):
                        order_size = random.randint(15, 30)
                        buy_res = place_order(SYMBOL, "buy", order_size, bid_pressure)
                        sell_res = place_order(SYMBOL, "sell", order_size, ask_pressure)

                        if buy_res is not None and buy_res["msg"] == "Success":
                            shield_order_ids.append(buy_res["data"]["order_id"])
                        else:
                            print(buy_res)
                        if sell_res is not None and sell_res["msg"] == "Success":
                            shield_order_ids.append(sell_res["data"]["order_id"])
                        else:
                            print(sell_res)
                        ask_pressure = ask_pressure + 0.01
                        bid_pressure = bid_pressure - 0.01

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
                        base_buy_price = bid_price * (1 + gap_ratio/10)
                        base_sell_price = ask_price * (1 - gap_ratio/10)

                    if base_buy_price > ask_price:
                        base_buy_price = ask_price
                    if base_sell_price < bid_price:
                        base_sell_price = bid_price


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

                    if buy_res is not None and buy_res["msg"] == "Success":
                        buy_order_ids.append(buy_res["data"]["order_id"])
                    else:
                        print(buy_res)
                    if sell_res is not None and sell_res["msg"] == "Success":
                        sell_order_ids.append(sell_res["data"]["order_id"])
                    else:
                        print(sell_res)

                time.sleep(get_dynamic_sleep_time())

            except Exception as e:
                print(f"An error occurred: {e}")
                traceback.print_exc()
                time.sleep(get_dynamic_sleep_time())
    except KeyboardInterrupt:
        cancel_list_of_orders(SYMBOL, buy_order_ids)
        cancel_list_of_orders(SYMBOL, sell_order_ids)
