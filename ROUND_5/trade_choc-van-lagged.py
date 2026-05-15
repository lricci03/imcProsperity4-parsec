'''import json
import numpy as np
from datamodel import Listing, Observation, Order, OrderDepth, ProsperityEncoder, Symbol, Trade, TradingState

class Trader:
    def __init__(self):
        self.position_limit = 10
        self.window_size = 100
        self.history_vanilla = []
        self.history_chocolate = []
        self.history_strawberry = []
        self.history_raspberry = []
        # Regression coefficients
        self.slope_vc = -0.973
        self.slope_cv = -0.973

    def get_mid(self, state, symbol):
        depth = state.order_depths.get(symbol)
        if not depth: return None
        best_bid = max(depth.buy_orders.keys(), default=None)
        best_ask = min(depth.sell_orders.keys(), default=None)
        return (best_bid + best_ask) / 2 if best_bid and best_ask else None

    def execute_basic(self, state, symbol, signal):
        orders = []

        pos = state.position.get(symbol, 0)
        depth = state.order_depths[symbol]
        if signal > 0: # BUY
            qty = self.position_limit - pos
            if qty > 0:
                price = min(depth.sell_orders.keys())
                orders.append(Order(symbol, price, qty))
        elif signal < 0: # SELL
            qty = self.position_limit + pos
            if qty > 0:
                price = max(depth.buy_orders.keys())
                orders.append(Order(symbol, price, -qty))
        return orders

    def update_history(self, v_mid, c_mid):
        if v_mid is not None and c_mid is not None:
            self.history_vanilla.append(v_mid)
            self.history_chocolate.append(c_mid)
            if len(self.history_vanilla) > self.window_size:
                self.history_vanilla.pop(0)
                self.history_chocolate.pop(0)

    # ============================================================
    # STRATEGY 1: Statistical Prediction (Pred > Act -> Buy)
    # ============================================================
    """ Use lagged correlation to predict future prices
        
        CHOCOLATE(t-1) predicts VANILLA(t) with R²=0.946
        VANILLA(t-1) predicts CHOCOLATE(t) with R²=0.946
        
        Strategy:
        - If actual price is HIGHER than predicted → Sell (overvalued)
        - If actual price is LOWER than predicted → Buy (undervalued)
        """
    def trade_snackpacks_vc_lagged_1(self, state: TradingState):
        res = {}
        v_mid = self.get_mid(state, "SNACKPACK_VANILLA")
        c_mid = self.get_mid(state, "SNACKPACK_CHOCOLATE")
        
        if v_mid and c_mid and len(self.history_chocolate) >= self.window_size:
            # Predict Van(t) from Choc(t-1)
            int_van = np.mean(self.history_vanilla) - (self.slope_vc * np.mean(self.history_chocolate))
            pred_van = (self.slope_vc * self.history_chocolate[-1]) + int_van
            # Predict Choc(t) from Van(t-1)
            int_choc = np.mean(self.history_chocolate) - (self.slope_cv * np.mean(self.history_vanilla))
            pred_choc = (self.slope_cv * self.history_vanilla[-1]) + int_choc

            # Logic: Prediction > Actual -> Undervalued -> Buy
            if pred_van - v_mid > 5.0: res["SNACKPACK_VANILLA"] = self.execute_basic(state, "SNACKPACK_VANILLA", 1)
            elif v_mid - pred_van > 5.0: res["SNACKPACK_VANILLA"] = self.execute_basic(state, "SNACKPACK_VANILLA", -1)

            if pred_choc - c_mid > 5.0: res["SNACKPACK_CHOCOLATE"] = self.execute_basic(state, "SNACKPACK_CHOCOLATE", 1)
            elif c_mid - pred_choc > 5.0: res["SNACKPACK_CHOCOLATE"] = self.execute_basic(state, "SNACKPACK_CHOCOLATE", -1)

        self.update_history(v_mid, c_mid)
        return res

    # ============================================================
    # STRATEGY 2: Directional Fading (Choc UP -> Van SELL)
    # ============================================================
    """Use lagged correlation to predict future prices
        
        CHOCOLATE(t-1) predicts VANILLA(t) with R²=0.946
        VANILLA(t-1) predicts CHOCOLATE(t) with R²=0.946
        
        Strategy:
        - If from the last timestamp chocolate went UP → Vanilla will go UP, so SELL vanilla
        - If from the last timestamp chocolate went DOWN → Vanilla will go DOWN, so BUY vanilla
        Since the correlation goes in both direction:
        - If from the last timestamp vanilla went UP → Chocolate will go UP, so SELL chocolate
        - If from the last timestamp vanilla went DOWN → Chocolate will go DOWN, so BUY chocolate
        """
    def trade_snackpacks_vc_lagged_2(self, state: TradingState):
        res = {}
        v_mid = self.get_mid(state, "SNACKPACK_VANILLA")
        c_mid = self.get_mid(state, "SNACKPACK_CHOCOLATE")

        if v_mid and c_mid and len(self.history_chocolate) >= 1:
            # Choc move -> Van trade (Opposite direction due to negative correlation)
            if c_mid > self.history_chocolate[-1]: res["SNACKPACK_VANILLA"] = self.execute_basic(state, "SNACKPACK_VANILLA", -1)
            elif c_mid < self.history_chocolate[-1]: res["SNACKPACK_VANILLA"] = self.execute_basic(state, "SNACKPACK_VANILLA", 1)
            # Van move -> Choc trade
            if v_mid > self.history_vanilla[-1]: res["SNACKPACK_CHOCOLATE"] = self.execute_basic(state, "SNACKPACK_CHOCOLATE", -1)
            elif v_mid < self.history_vanilla[-1]: res["SNACKPACK_CHOCOLATE"] = self.execute_basic(state, "SNACKPACK_CHOCOLATE", 1)

        self.update_history(v_mid, c_mid)
        return res

    def run(self, state: TradingState):
        # --- restore state ---
        if state.traderData:
            data = json.loads(state.traderData)
            self.history_vanilla   = data.get("history_vanilla", [])
            self.history_chocolate = data.get("history_chocolate", [])
            self.history_strawberry = data.get("history_strawberry", [])
            self.history_raspberry  = data.get("history_raspberry", [])

        result = {}

        # --- snackpacks vanilla and choc ---
        # NEVER run them simultaneously
        result.update(self.trade_snackpacks_vc_lagged_1(state))
        #result.update(self.trade_snackpacks_vc_lagged_2(state))

        # --- save state ---
        trader_data = json.dumps({
            "history_vanilla": self.history_vanilla,
            "history_chocolate": self.history_chocolate,
            "history_strawberry": self.history_strawberry,
            "history_raspberry": self.history_raspberry,
        })

        return result, 0, trader_data
'''

import json
import numpy as np
from datamodel import Listing, Observation, Order, OrderDepth, ProsperityEncoder, Symbol, Trade, TradingState

class Trader:
    def __init__(self):
        self.position_limit = 10
        self.window_size = 100
        self.history_vanilla = []
        self.history_chocolate = []
        self.history_strawberry = []
        self.history_raspberry = []
        # Regression coefficients
        self.slope_vc = -0.973
        self.slope_cv = -0.973

    def get_prices(self, state, symbol):
        depth = state.order_depths.get(symbol)
        if not depth: return None, None, None
        best_bid = max(depth.buy_orders.keys(), default=None)
        best_ask = min(depth.sell_orders.keys(), default=None)
        if best_bid is None or best_ask is None: return None, None, None
        mid = (best_bid + best_ask) / 2
        return mid, best_bid, best_ask

    def update_history(self, v_mid, c_mid):
        if v_mid is not None and c_mid is not None:
            self.history_vanilla.append(v_mid)
            self.history_chocolate.append(c_mid)
            if len(self.history_vanilla) > self.window_size:
                self.history_vanilla.pop(0)
                self.history_chocolate.pop(0)

    # ============================================================
    # STRATEGY 1: Statistical Prediction (Market Making)
    # ============================================================
    """ Use lagged correlation to predict future prices
        
        CHOCOLATE(t-1) predicts VANILLA(t) with R²=0.946
        VANILLA(t-1) predicts CHOCOLATE(t) with R²=0.946
        
        Strategy:
        - If actual price is HIGHER than predicted → Sell (overvalued)
        - If actual price is LOWER than predicted → Buy (undervalued)
        """
    def trade_snackpacks_vc_lagged_1(self, state: TradingState):
        res = {}
        v_mid, best_bid_v, best_ask_v = self.get_prices(state, "SNACKPACK_VANILLA")
        c_mid, best_bid_c, best_ask_c = self.get_prices(state, "SNACKPACK_CHOCOLATE")
        
        if v_mid and c_mid and len(self.history_chocolate) >= self.window_size:
            # Intercepts and Predictions
            int_van = np.mean(self.history_vanilla) - (self.slope_vc * np.mean(self.history_chocolate))
            pred_van = (self.slope_vc * self.history_chocolate[-1]) + int_van
            
            int_choc = np.mean(self.history_chocolate) - (self.slope_cv * np.mean(self.history_vanilla))
            pred_choc = (self.slope_cv * self.history_vanilla[-1]) + int_choc

            # VANILLA - Market Making
            pos_v = state.position.get("SNACKPACK_VANILLA", 0)
            if pred_van - v_mid > 5.0: # Undervalued -> Buy
                res["SNACKPACK_VANILLA"] = [Order("SNACKPACK_VANILLA", best_bid_v + 1, self.position_limit - pos_v)]
            elif v_mid - pred_van > 5.0: # Overvalued -> Sell
                res["SNACKPACK_VANILLA"] = [Order("SNACKPACK_VANILLA", best_ask_v - 1, -(self.position_limit + pos_v))]

            # CHOCOLATE - Market Making
            pos_c = state.position.get("SNACKPACK_CHOCOLATE", 0)
            if pred_choc - c_mid > 5.0: # Undervalued -> Buy
                res["SNACKPACK_CHOCOLATE"] = [Order("SNACKPACK_CHOCOLATE", best_bid_c + 1, self.position_limit - pos_c)]
            elif c_mid - pred_choc > 5.0: # Overvalued -> Sell
                res["SNACKPACK_CHOCOLATE"] = [Order("SNACKPACK_CHOCOLATE", best_ask_c - 1, -(self.position_limit + pos_c))]

        self.update_history(v_mid, c_mid)
        return res

    # ============================================================
    # STRATEGY 2: Directional Fading (Market Taking)
    # ============================================================
    def trade_snackpacks_vc_lagged_2(self, state: TradingState):
        res = {}
        v_mid, best_bid_v, best_ask_v = self.get_prices(state, "SNACKPACK_VANILLA")
        c_mid, best_bid_c, best_ask_c = self.get_prices(state, "SNACKPACK_CHOCOLATE")

        if v_mid and c_mid and len(self.history_chocolate) >= 1:
            # VANILLA - Market Making
            pos_v = state.position.get("SNACKPACK_VANILLA", 0)
            choc_move = c_mid - self.history_chocolate[-1]
            if choc_move > 0:   # Choc Up -> Van Sell
                room_to_sell_v = self.position_limit + pos_v
                res["SNACKPACK_VANILLA"] = [Order("SNACKPACK_VANILLA", best_ask_v-1, -room_to_sell_v)]
            elif choc_move < 0: # Choc Down -> Van Buy
                room_to_buy_v = self.position_limit - pos_v
                res["SNACKPACK_VANILLA"] = [Order("SNACKPACK_VANILLA", best_bid_v+1,room_to_buy_v)]

            # CHOCOLATE - Aggressive
            pos_c = state.position.get("SNACKPACK_CHOCOLATE", 0)
            van_move = v_mid - self.history_vanilla[-1]
            if van_move > 0:   # Van Up -> Choc Sell
                room_to_sell_c = self.position_limit + pos_c
                res["SNACKPACK_CHOCOLATE"] = [Order("SNACKPACK_CHOCOLATE", best_ask_c-1, -room_to_sell_c)]
            elif van_move < 0: # Van Down -> Choc Buy
                room_to_buy_c = self.position_limit - pos_c
                res["SNACKPACK_CHOCOLATE"] = [Order("SNACKPACK_CHOCOLATE", best_bid_c+1, room_to_buy_c)]

        self.update_history(v_mid, c_mid)
        return res

    def run(self, state: TradingState):
        if state.traderData:
            data = json.loads(state.traderData)
            self.history_vanilla = data.get("history_vanilla", [])
            self.history_chocolate = data.get("history_chocolate", [])
            self.history_strawberry = data.get("history_strawberry", [])
            self.history_raspberry = data.get("history_raspberry", [])

        result = {}
        
        #result.update(self.trade_snackpacks_vc_lagged_1(state))
        result.update(self.trade_snackpacks_vc_lagged_2(state))

        trader_data = json.dumps({
            "history_vanilla": self.history_vanilla,
            "history_chocolate": self.history_chocolate,
            "history_strawberry": self.history_strawberry,
            "history_raspberry": self.history_raspberry,
        })

        return result, 0, trader_data
