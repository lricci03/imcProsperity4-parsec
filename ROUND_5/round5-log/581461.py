from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List, Any
import json
import string
import numpy as np

from datamodel import Listing, Observation, Order, OrderDepth, ProsperityEncoder, Symbol, Trade, TradingState

class Trader:

    def __init__(self):
        self.position_limit =10
        # ============================================================
        # PEBBLES STRATEGY PARAMETERS
        # ============================================================
        self.pebbles          = ["PEBBLES_L", "PEBBLES_M", "PEBBLES_S", "PEBBLES_XL", "PEBBLES_XS"]
        self.pebbles_target   = 50000    # what the basket should sum to
        self.pebbles_threshold = 10      # minimum deviation before we act
        self.pebbles_prev_xl = None
        self.pebbles_counter=1

        # ============================================================
        # SNACKPACK STRATEGY PARAMETERS
        # ============================================================
        self.snackpack_prev_vc = None
        self.snackpack_prev_rs = None
        # For Lisa's vc algorithm
        self.history_v = []
        self.history_c = []
        self.window_size = 20 # Number of ticks for rolling beta


        # ======================
        # DOMESTIC ROBOTS
        # ======================
        self.prev_robot_ironing = None

        # ======================
        # ROBOT IRONING
        # ======================
        self.ironing_prices = []
        self.dishes_prices =[]
        self.Z_EXIT = 0.5
        self.Z_ENTRY = 2
        self.zscore_window = 100

        # ======================
        # OXYGEN SHAKES
        # ======================
        self.ox_c_prices = []
        self.ox_ev_prices = []
        # we also use the variables 
        # self.Z_EXIT = 0.5
        # self.Z_ENTRY = 2
        # self.zscore_window = 100

    # ========== SHAKES FUNCTIONS (Lisa) ==================================
    def get_rolling_beta(self):
        n = len(self.history_v)
        if n < self.window_size:
            return -1.0 # Default if not enough data
        
        sum_x = sum(self.history_c)
        sum_y = sum(self.history_v)
        sum_xy = sum(x * y for x, y in zip(self.history_c, self.history_v))
        sum_xx = sum(x * x for x in self.history_c)
        
        numerator = (n * sum_xy) - (sum_x * sum_y)
        denominator = (n * sum_xx) - (sum_x**2)
        
        return numerator / denominator if denominator != 0 else -1.0

    # ========== ROBOT IRONING & OXYGEN FUNCTIONS =========================
    def z_score(self,prices):
        if len(prices)<20:
            return 0
        
        prices_array =np.array(prices)
        moving_average = np.mean(prices_array)
        std_dev = np.std(prices_array)

        if std_dev < 1e-6:
            return 0
        return (prices_array[-1] - moving_average)/std_dev


    # ============================================================
    # PEBBLES STRATEGY
    #if deviation > self.pebbles_threshold:
    # expect XL to go down and XS,S,M,L to go up
    # buy XL at best_ask-1, sell rest at best_bid+1
    # ============================================================

    
    def trade_pebbles2(self, state: TradingState) -> dict:

        if not all(p in state.order_depths for p in self.pebbles):
            return {}

        # compute mid_price for each pebble
        mid_prices = {}
        for p in self.pebbles:
            depth    = state.order_depths[p]
            best_bid = max(depth.buy_orders.keys(),  default=None)
            best_ask = min(depth.sell_orders.keys(), default=None)
            if best_bid is None or best_ask is None:
                return {}
            mid_prices[p] = (best_bid + best_ask) / 2

        pebble_orders = {}


        # first tick: nothing to compare against
        if self.pebbles_prev_xl is None:
            self.pebbles_prev_xl = mid_prices["PEBBLES_XL"]
            return {}

        xl_variation = mid_prices["PEBBLES_XL"] - self.pebbles_prev_xl
        self.pebbles_prev_xl = mid_prices["PEBBLES_XL"]


        for p in self.pebbles:
            depth    = state.order_depths[p]
            position = state.position.get(p, 0)
            best_bid = max(depth.buy_orders.keys())
            best_ask = min(depth.sell_orders.keys())
            orders   = []

            ## next tick sell and buy accordingly
            if self.pebbles_counter == 1:# and xl_variation>0: ## sold xl timestamp before b/c went up
                if p == "PEBBLES_XL":
                    # buy xl passively (misteriously) at best_bid
                    qty = self.position_limit - position # room to buy
                    if qty > 0:
                        orders.append(Order(p, best_bid, qty)) #makes profit wtf
                        #orders.append(Order(p, best_ask, qty))
                else:
                    # sell others passively at best ask (wtf)
                    qty = self.position_limit + position # room to sell
                    if qty > 0:
                        orders.append(Order(p, best_ask, -qty)) #makes profit wtf
                        #orders.append(Order(p, best_bid, -qty))
            elif self.pebbles_counter==0:# and xl_variation<0: ## bought xl timestamp before b/c went down
                if p == "PEBBLES_XL":
                    # sell xl passsively at best ask (wtf)
                    qty = self.position_limit + position # room to sell
                    if qty > 0:
                        orders.append(Order(p, best_ask, -qty)) #makes profit wtf
                        #orders.append(Order(p, best_bid, -qty))
                else:
                    # buy others passively at best bid (wtf)
                    qty = self.position_limit - position # room to buy
                    if qty > 0:
                        orders.append(Order(p, best_bid, +qty)) #makes profit wtf
                        #orders.append(Order(p, best_ask, +qty))

                
            if xl_variation > 20:
                self.pebbles_counter=1
                # xl went up, it will go down
                if p == "PEBBLES_XL":
                    # XL went up → sell XL passively
                    qty = self.position_limit + position # room to sell
                    if qty > 0:
                        orders.append(Order(p, best_ask -1, -qty))
                else:
                    # others went down → buy others passively
                    qty = self.position_limit - position # room to buy
                    if qty > 0:
                        orders.append(Order(p, best_bid + 1, +qty))

            elif xl_variation<-20:
                self.pebbles_counter=0
                # basket too low
                if p == "PEBBLES_XL":
                    # XL went down → buy XL passively
                    qty = self.position_limit - position #room to buy
                    if qty > 0:
                        orders.append(Order(p, best_bid+1, +qty))
                else:
                    # others went up → sell others passively
                    qty = self.position_limit + position #room to sell
                    if qty > 0:
                        orders.append(Order(p, best_ask - 1, -qty))
            else:
                self.pebbles_counter=2

            pebble_orders[p] = orders

        return pebble_orders
    
    # ============================================================
    # SNACKPACK BASKET STRATEGY
    # Two baskets have strong tick-by-tick mean reversion:
    #   VANILLA + CHOCOLATE:      ac = -0.34 (strongest signal)
    #   RASPBERRY + STRAWBERRY:   ac = -0.27
    #
    # If the basket return was positive last tick → it tends to fall
    # → sell both legs passively
    # If the basket return was negative last tick → it tends to rise
    # → buy both legs passively
    # ============================================================
    # --- VANILLA + CHOCOLATE ---
    def trade_snackpacks_vc_lisa(self, state: TradingState) -> dict:
        basket = ["SNACKPACK_VANILLA", "SNACKPACK_CHOCOLATE"]
        
        # Early validation: check all products exist
        if not all(p in state.order_depths for p in basket):
            return {}
        
        # compute mid_price for each product - with safety checks
        mid = {}
        for p in basket:
            depth = state.order_depths[p]
            best_bid = max(depth.buy_orders.keys(), default=None)
            best_ask = min(depth.sell_orders.keys(), default=None)
            if best_bid is None or best_ask is None:
                return {}
            mid[p] = (best_bid + best_ask) / 2
        
        # Update History BEFORE any early returns
        self.history_v.append(mid["SNACKPACK_VANILLA"])
        self.history_c.append(mid["SNACKPACK_CHOCOLATE"])
        if len(self.history_v) > self.window_size:
            self.history_v.pop(0)
            self.history_c.pop(0)
        
        # Calculate Rolling Beta and Spread
        beta = self.get_rolling_beta()
        current_spread = mid["SNACKPACK_VANILLA"] - (beta * mid["SNACKPACK_CHOCOLATE"])
        
        # first tick: just store spread value, no orders
        if self.snackpack_prev_vc is None:
            self.snackpack_prev_vc = current_spread
            return {}
        
        # how much did the spread move?
        deviation = current_spread - self.snackpack_prev_vc
        
        # update stored value for next tick
        self.snackpack_prev_vc = current_spread
        
        # Initialize result dict with all products
        vc_orders = {}
        
        # Process each product in the basket
        for p in basket:
            depth = state.order_depths[p]
            position = state.position.get(p, 0)
            best_bid = max(depth.buy_orders.keys(), default=None)
            best_ask = min(depth.sell_orders.keys(), default=None)
            
            # Safety check - if market is illiquid, skip
            if best_bid is None or best_ask is None:
                vc_orders[p] = []
                continue
            
            orders = []
            threshold = 2
            
            if deviation > threshold:
                # Spread spiked up (Broken Mirror) -> Sell both
                qty = self.position_limit + position
                if qty > 0:
                    orders.append(Order(p, best_ask-1, -qty))
            
            elif deviation < -threshold:
                # Spread dropped (Broken Mirror) -> Buy both
                qty = self.position_limit - position
                if qty > 0:
                    orders.append(Order(p, best_bid+1, qty))
            
            vc_orders[p] = orders
        
        return vc_orders

    def trade_snackpacks_vanillachocolate(self, state: TradingState) -> dict:
        basket = ["SNACKPACK_VANILLA", "SNACKPACK_CHOCOLATE"]

        if not all(p in state.order_depths for p in basket):
            return {}


        # compute mid_price for each product
        mid = {}
        for p in basket:
            depth    = state.order_depths[p]
            best_bid = max(depth.buy_orders.keys(),  default=None)
            best_ask = min(depth.sell_orders.keys(), default=None)
            if best_bid is None or best_ask is None:
                return {}
            mid[p] = (best_bid + best_ask) / 2

        # first tick: just store basket values, no orders
        if self.snackpack_prev_vc is None:
            self.snackpack_prev_vc = mid["SNACKPACK_VANILLA"]  + mid["SNACKPACK_CHOCOLATE"]
            return {}

        # basket return last tick: how much did the sum move?
        vc_return = (mid["SNACKPACK_VANILLA"]  + mid["SNACKPACK_CHOCOLATE"])  - self.snackpack_prev_vc
        
        # update stored values for next tick
        self.snackpack_prev_vc = mid["SNACKPACK_VANILLA"]  + mid["SNACKPACK_CHOCOLATE"]


        vc_orders = {}

        for p in basket:
            depth    = state.order_depths[p]
            position = state.position.get(p, 0)
            best_bid = max(depth.buy_orders.keys())
            best_ask = min(depth.sell_orders.keys())
            orders   = []

            if vc_return > 0:
                # basket went up → expect it to fall → sell both 
                qty = self.position_limit + position  # room to sell
                if qty > 0:
                    orders.append(Order(p, best_ask-1, -qty))

            elif vc_return < 0:
                # basket went down → expect it to rise → buy both legs
                qty = self.position_limit - position  # room to buy
                if qty > 0:
                    orders.append(Order(p, best_bid+1, +qty))

            vc_orders[p] = orders

        return vc_orders

    # --- RASPBERRY + STRAWBERRY ---
    def trade_snackpacks_raspberrystrawberry(self, state: TradingState) -> dict:

        basket= ["SNACKPACK_RASPBERRY", "SNACKPACK_STRAWBERRY"]
        if not all(p in state.order_depths for p in basket):
            return {}
        
        # compute mid_price for each product
        mid = {}
        for p in basket:
            depth    = state.order_depths[p]
            best_bid = max(depth.buy_orders.keys(),  default=None)
            best_ask = min(depth.sell_orders.keys(), default=None)
            if best_bid is None or best_ask is None:
                return {}
            mid[p] = (best_bid + best_ask) / 2

        # first tick: just store basket values, no orders
        if self.snackpack_prev_rs is None:
            self.snackpack_prev_rs = mid["SNACKPACK_RASPBERRY"]  + mid["SNACKPACK_STRAWBERRY"]
            return {}
        
        # basket return last tick: how much did the sum move?
        rs_return = (mid["SNACKPACK_RASPBERRY"] + mid["SNACKPACK_STRAWBERRY"]) - self.snackpack_prev_rs
        
        # update stored values for next tick
        self.snackpack_prev_rs = mid["SNACKPACK_RASPBERRY"] + mid["SNACKPACK_STRAWBERRY"]


        rs_orders = {}
            
        for p in basket:
            depth    = state.order_depths[p]
            position = state.position.get(p, 0)
            best_bid = max(depth.buy_orders.keys())
            best_ask = min(depth.sell_orders.keys())
            orders        = []

            if rs_return > 0:
                # basket went up → expect it to fall → sell both legs
                qty = self.position_limit + position
                if qty > 0:
                    orders.append(Order(p, best_ask-1, -qty))

            elif rs_return < -0:
                # basket went down → expect it to rise → buy both legs
                qty = self.position_limit - position
                if qty > 0:
                    orders.append(Order(p, best_bid+1, +qty))

            rs_orders[p] = orders

        return rs_orders

    #================== ROBOTS =======================
    # For both robot ironing and robot dishes we use similar strategies
    #  NEED TO EXPAND ON THIS
    
    # --- ROBOT IRONING ---
    def trade_robot_ironing(self, state: TradingState) -> dict:
        ironing_orders={}
        ir_orders = []
        p = "ROBOT_IRONING"
        position = state.position.get(p, 0)
        current_position = position
        if p not in state.order_depths:
            return {}
        
        

        depth= state.order_depths[p]
        best_bid = max(depth.buy_orders.keys(),  default=None)
        best_ask = min(depth.sell_orders.keys(), default=None)
        if best_bid is None or best_ask is None:
            return {}
        mid_price = (best_bid + best_ask) / 2

        # first tick: just store the mid_price, no order
        if len(self.ironing_prices) < 1:
            self.ironing_prices.append(mid_price)
            return {}
        
        # how much did the price move?
        ironing_return = mid_price - self.ironing_prices[-1]
        # update stored value for next tick
        self.ironing_prices.append(mid_price)

        if len(self.ironing_prices)> self.zscore_window:
            self.ironing_prices.pop(0)

        # compute z_score
        z_score = self.z_score(self.ironing_prices)

        # If the last return was >50, we sell. 
        # If it was <-50 we buy.
        # We place orders at best bid and best sell bc we want to be filled.
        if abs(ironing_return)>50:
            room_to_buy = self.position_limit - position
            room_to_sell= self.position_limit + position
            if ironing_return >0:
                qty = room_to_sell
                if qty >0:
                    ir_orders.append(Order(p, best_bid, -qty))
            elif ironing_return <-50:
                qty = room_to_buy
                if qty >0:
                    ir_orders.append(Order(p,best_ask, qty))

        else:
            # 1. CLOSING: if price returned to the mean (Z is near 0), reduce the position
            if position !=0 and abs(z_score)<self.Z_EXIT:
                qty=min(position,4)
                if position > 0:
                    # Close Long: Sell at the best possible price to get out
                    ir_orders.append(Order(p, best_bid, -qty)) 
                    current_position = current_position - qty
                else:
                    # Close Short: Buy at the best possible price to get out
                    ir_orders.append(Order(p, best_ask, qty))
                    current_position = current_position + qty

            # 2. ENTRY: when extreme deviation from the mean.
            elif abs(z_score) >= self.Z_ENTRY:
                    if z_score >= self.Z_ENTRY and position > -self.position_limit:
                        # Overvalued: Sell
                        # MAYBE CHANGE BEST ASK  TO BEST ASK - 1?
                        room_to_sell = self.position_limit + position # >0 by assumption
                        qty = room_to_sell
                        ir_orders.append(Order(p, best_ask-1, -qty))
                        current_position = position - qty
                        
                    elif z_score <= -self.Z_ENTRY and position < self.position_limit:
                        # Undervalued: Buy
                        price = best_bid+1
                        room_to_buy = self.position_limit - position  #>0 by assumption
                        qty = room_to_buy 
                        ir_orders.append(Order(p, price, qty))
                        current_position = position + qty

            # 3. Take advantage of positive/negative returns
            room_to_buy = self.position_limit - current_position
            room_to_sell = self.position_limit + current_position
            # If the price went up from last tick, we sell at best ask -1???
            if ironing_return >0:
                qty = room_to_sell
                if qty >0:
                    ir_orders.append(Order(p,best_ask-1,-qty))
            elif ironing_return <0:
                qty = room_to_buy
                if qty >0:
                    ir_orders.append(Order(p,best_bid+1,qty))
            
        ironing_orders[p] = ir_orders
        
        return ironing_orders
    
    # --- ROBOT DISHES ---
    def trade_robot_dishes(self, state: TradingState) -> dict:
        orders = []
        p = "ROBOT_DISHES"
        position = state.position.get(p, 0)
        current_position = position
        if p not in state.order_depths:
            return {}
        

        depth= state.order_depths[p]
        best_bid = max(depth.buy_orders.keys(),  default=None)
        best_ask = min(depth.sell_orders.keys(), default=None)
        if best_bid is None or best_ask is None:
            return {}
        mid_price = (best_bid + best_ask) / 2

        # first tick: just store the mid_price, no order
        if self.dishes_prices ==[]:
            self.dishes_prices.append(mid_price)
            return {}
        
        # how much did the price move?
        dishes_return = mid_price - self.dishes_prices[-1]
        # update stored value for next tick
        self.dishes_prices.append(mid_price)

        if len(self.dishes_prices)> self.zscore_window:
            self.dishes_prices.pop(0)

        # compute z_score
        z_score = self.z_score(self.dishes_prices)

        # If the last return was >50, we sell. 
        # If it was <-50 we buy.
        # We place orders at best bid and best sell bc we want to be filled.
        if abs(dishes_return)>50:
            room_to_buy = self.position_limit - position
            room_to_sell= self.position_limit + position
            if dishes_return >0:
                qty = room_to_sell
                if qty >0:
                    orders.append(Order(p, best_bid, -qty))
            elif dishes_return <-50:
                qty = room_to_buy
                if qty >0:
                    orders.append(Order(p,best_ask, qty))

        else:
            # 1. MANAGE INVENTORY WHEN LONG/SHORT
            if abs(position) == self.position_limit:
                if (position > 0 and abs(z_score) < self.Z_EXIT):
                    orders.append(Order(p, best_bid, -4))
                    current_position = current_position -4
                elif (position < 0 and abs(z_score) < self.Z_EXIT):
                    orders.append(Order(p, best_ask, 4))
                    current_position = current_position +4

            # 2. ENTRY: when extreme deviation from the mean.
            elif abs(z_score) >= self.Z_ENTRY:
                    if z_score >= self.Z_ENTRY and position > -self.position_limit:
                        # Overvalued: Sell
                        # MAYBE CHANGE BEST ASK  TO BEST ASK - 1?
                        room_to_sell = self.position_limit + position # >0 by assumption
                        qty = room_to_sell
                        orders.append(Order(p, best_ask-1, -qty))
                        current_position = position - qty
                        
                    elif z_score <= -self.Z_ENTRY and position < self.position_limit:
                        # Undervalued: Buy
                        price = best_bid+1
                        room_to_buy = self.position_limit - position  #>0 by assumption
                        qty = room_to_buy 
                        orders.append(Order(p, price, qty))
                        current_position = position + qty

            # 3. Take advantage of positive/negative returns
            room_to_buy = self.position_limit - current_position
            room_to_sell = self.position_limit + current_position
            # If the price went up from last tick, we sell at best ask -1???
            if dishes_return >0:
                qty = room_to_sell
                if qty >0:
                    orders.append(Order(p,best_ask-1,-qty))
            elif dishes_return <0:
                qty = room_to_buy
                if qty >0:
                    orders.append(Order(p,best_bid+1,qty))
        
        return {p: orders}

    #================== OXYGEN SHAKES =======================
    # Strategy similar to ROBOTS

    # --- OXYGEN CHOCOLATE ----
    def trade_oxygen_chocolate(self, state: TradingState) -> dict:
        orders = []
        p = "OXYGEN_SHAKE_CHOCOLATE"
        position = state.position.get(p, 0)
        current_position = position
        if p not in state.order_depths:
            return {}

        depth= state.order_depths[p]
        best_bid = max(depth.buy_orders.keys(),  default=None)
        best_ask = min(depth.sell_orders.keys(), default=None)
        if best_bid is None or best_ask is None:
            return {}
        mid_price = (best_bid + best_ask) / 2

        # first tick: just store the mid_price, no order
        if self.ox_c_prices ==[]:
            self.ox_c_prices.append(mid_price)
            return {}
        
        # how much did the price move?
        ox_c_return = mid_price - self.ox_c_prices[-1]
        # update stored value for next tick
        self.ox_c_prices.append(mid_price)

        if len(self.ox_c_prices)> self.zscore_window:
            self.ox_c_prices.pop(0)

        # compute z_score
        z_score = self.z_score(self.ox_c_prices)

        # If the last return was >50, we sell. 
        # If it was <-50 we buy.
        # We place orders at best bid and best sell bc we want to be filled.
        if abs(ox_c_return)>50:
            room_to_buy = self.position_limit - position
            room_to_sell= self.position_limit + position
            if ox_c_return >0:
                qty = room_to_sell
                if qty >0:
                    orders.append(Order(p, best_bid, -qty))
            elif ox_c_return <-50:
                qty = room_to_buy
                if qty >0:
                    orders.append(Order(p,best_ask, qty))

        else:
            # 1. CLOSING: if price returned to the mean (Z is near 0), reduce the position
            if position !=0 and abs(z_score)<self.Z_EXIT:
                qty=min(position,4)
                if position > 0:
                    # Close Long: Sell at the best possible price to get out
                    orders.append(Order(p, best_bid, -qty)) 
                    current_position = current_position - qty
                else:
                    # Close Short: Buy at the best possible price to get out
                    orders.append(Order(p, best_ask, qty))
                    current_position = current_position + qty

            # 2. ENTRY: when extreme deviation from the mean.
            elif abs(z_score) >= self.Z_ENTRY:
                    if z_score >= self.Z_ENTRY and position > -self.position_limit:
                        # Overvalued: Sell
                        # MAYBE CHANGE BEST ASK  TO BEST ASK - 1?
                        room_to_sell = self.position_limit + position # >0 by assumption
                        qty = room_to_sell
                        orders.append(Order(p, best_ask-1, -qty))
                        current_position = position - qty
                        
                    elif z_score <= -self.Z_ENTRY and position < self.position_limit:
                        # Undervalued: Buy
                        price = best_bid+1
                        room_to_buy = self.position_limit - position  #>0 by assumption
                        qty = room_to_buy 
                        orders.append(Order(p, price, qty))
                        current_position = position + qty

            # 3. Take advantage of positive/negative returns
            room_to_buy = self.position_limit - current_position
            room_to_sell = self.position_limit + current_position
            # If the price went up from last tick, we sell at best ask -1???
            if ox_c_return >0:
                qty = room_to_sell
                if qty >0:
                    orders.append(Order(p,best_ask-1,-qty))
            elif ox_c_return <0:
                qty = room_to_buy
                if qty >0:
                    orders.append(Order(p,best_bid+1,qty))
        
        return {p: orders}
    

    # --- OXYGEN EVENING ---
    def trade_oxygen_evening(self, state: TradingState) -> dict:
        orders = []
        p = "OXYGEN_SHAKE_EVENING_BREATH"
        position = state.position.get(p, 0)
        current_position = position
        if p not in state.order_depths:
            return {}

        depth= state.order_depths[p]
        best_bid = max(depth.buy_orders.keys(),  default=None)
        best_ask = min(depth.sell_orders.keys(), default=None)
        if best_bid is None or best_ask is None:
            return {}
        mid_price = (best_bid + best_ask) / 2

        # first tick: just store the mid_price, no order
        if self.ox_ev_prices ==[]:
            self.ox_ev_prices.append(mid_price)
            return {}
        
        # how much did the price move?
        ox_ev_return = mid_price - self.ox_ev_prices[-1]
        # update stored value for next tick
        self.ox_ev_prices.append(mid_price)

        if len(self.ox_ev_prices)> self.zscore_window:
            self.ox_ev_prices.pop(0)

        # compute z_score
        z_score = self.z_score(self.ox_ev_prices)

        # If the last return was >50, we sell. 
        # If it was <-50 we buy.
        # We place orders at best bid and best sell bc we want to be filled.
        if abs(ox_ev_return)>50:
            room_to_buy = self.position_limit - position
            room_to_sell= self.position_limit + position
            if ox_ev_return >0:
                qty = room_to_sell
                if qty >0:
                    orders.append(Order(p, best_bid, -qty))
            elif ox_ev_return <-50:
                qty = room_to_buy
                if qty >0:
                    orders.append(Order(p,best_ask, qty))

        else:
            # 1. MANAGE INVENTORY WHEN LONG/SHORT
            if abs(position) == self.position_limit:
                if (position > 0 and abs(z_score) < self.Z_EXIT):
                    orders.append(Order(p, best_bid, -4))
                    current_position = current_position -4
                elif (position < 0 and abs(z_score) < self.Z_EXIT):
                    orders.append(Order(p, best_ask, 4))
                    current_position = current_position +4

            # 2. ENTRY: when extreme deviation from the mean.
            elif abs(z_score) >= self.Z_ENTRY:
                    if z_score >= self.Z_ENTRY and position > -self.position_limit:
                        # Overvalued: Sell
                        # MAYBE CHANGE BEST ASK  TO BEST ASK - 1?
                        room_to_sell = self.position_limit + position # >0 by assumption
                        qty = room_to_sell
                        orders.append(Order(p, best_ask-1, -qty))
                        current_position = position - qty
                        
                    elif z_score <= -self.Z_ENTRY and position < self.position_limit:
                        # Undervalued: Buy
                        price = best_bid+1
                        room_to_buy = self.position_limit - position  #>0 by assumption
                        qty = room_to_buy 
                        orders.append(Order(p, price, qty))
                        current_position = position + qty

            # 3. Take advantage of positive/negative returns
            room_to_buy = self.position_limit - current_position
            room_to_sell = self.position_limit + current_position
            # If the price went up from last tick, we sell at best ask -1???
            if ox_ev_return >0:
                qty = room_to_sell
                if qty >0:
                    orders.append(Order(p,best_ask-1,-qty))
            elif ox_ev_return <0:
                qty = room_to_buy
                if qty >0:
                    orders.append(Order(p,best_bid+1,qty))
        
        return {p: orders}
    
    ### -------- PANELS
    
    def trade_construction_panels_new(self, state: TradingState) -> dict:
        thresholds = {
            "PANEL_1X2": 0,
            "PANEL_2X2": 4,
            "PANEL_1X4": 9,
            "PANEL_2X4": 7,
        }

        panel_orders = {}

        for p, threshold in thresholds.items():
            if p not in state.order_depths:
                continue

            depth    = state.order_depths[p]
            position = state.position.get(p, 0)
            orders   = []

            best_bid = max(depth.buy_orders.keys(),  default=None)
            best_ask = min(depth.sell_orders.keys(), default=None)

            if best_bid is None or best_ask is None:
                continue

            buy_price  = best_bid + 1
            sell_price = best_ask - 1

            if position > threshold:
                # too long: only sell
                sell_qty = self.position_limit + position
                if sell_qty > 0:
                    orders.append(Order(p, sell_price, -sell_qty))

            elif position < -threshold:
                # too short: only buy
                buy_qty = self.position_limit - position
                if buy_qty > 0:
                    orders.append(Order(p, buy_price, +buy_qty))

            else:
                # near flat: post both sides
                buy_qty  = self.position_limit - position
                sell_qty = self.position_limit + position
                if buy_qty > 0:
                    orders.append(Order(p, buy_price,  +buy_qty))
                if sell_qty > 0:
                    orders.append(Order(p, sell_price, -sell_qty))

            panel_orders[p] = orders

        return panel_orders
    
    # ============================================================
    # MAIN RUN — one entry point, calls each strategy separately
    # Each strategy returns its own dict and we merge them all.
    # An early return inside trade_pebbles never kills the run.
    # ============================================================
    def run(self, state: TradingState):
            # --- restore state ---
        if state.traderData:
            data = json.loads(state.traderData)
            self.pebbles_prev_xl   = data.get("pebbles_prev_xl")
            self.pebbles_counter   = data.get("pebbles_counter", 1)
            self.snackpack_prev_vc = data.get("snackpack_prev_vc")
            self.snackpack_prev_rs = data.get("snackpack_prev_rs")
            self.history_v         = data.get("history_v", [])
            self.history_c         = data.get("history_c", [])
            self.ironing_prices    = data.get("ironing_prices", [])
            self.dishes_prices     = data.get("dishes_prices", [])
            self.ox_c_prices       = data.get("ox_c_prices", [])
            self.ox_ev_prices      = data.get("ox_ev_prices", [])

        result = {}

        # --- pebbles ---
        result.update(self.trade_pebbles2(state))


        # --- snackpacks
        #result.update(self.trade_snackpacks_vanillachocolate(state))
        result.update(self.trade_snackpacks_vc_lisa(state)) # it performs better
        result.update(self.trade_snackpacks_raspberrystrawberry(state))
        

        # --- robots
        result.update(self.trade_robot_ironing(state))
        result.update(self.trade_robot_dishes(state))

        # --- oxygen shakes
        result.update(self.trade_oxygen_chocolate(state))
        result.update(self.trade_oxygen_evening(state))

        # --- panels
        result.update(self.trade_construction_panels_new(state))

            # --- save state ---
        trader_data = json.dumps({
            "pebbles_prev_xl"   : self.pebbles_prev_xl,
            "pebbles_counter"   : self.pebbles_counter,
            "snackpack_prev_vc" : self.snackpack_prev_vc,
            "snackpack_prev_rs" : self.snackpack_prev_rs,
            "history_v"         : self.history_v,
            "history_c"         : self.history_c,
            "ironing_prices"    : self.ironing_prices,
            "dishes_prices"     : self.dishes_prices,
            "ox_c_prices"       : self.ox_c_prices,
            "ox_ev_prices"      : self.ox_ev_prices,
        })

        return result, 0, trader_data