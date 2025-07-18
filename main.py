import traceback
from src.market_making import market_making

if __name__ == "__main__":
    try:

        market_making(10, 5, 10, 5, 20, 0.00009)

    except KeyboardInterrupt:
        print("Main process interrupted")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        traceback.print_exc()
