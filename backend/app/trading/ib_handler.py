from ib_insync import *
import asyncio
from datetime import datetime, timedelta, time
import pytz
import zoneinfo
from zoneinfo import ZoneInfo
import math
import random
class IBHandler:
    def __init__(self, settings):
        self.ib = IB()
        self.settings = settings
        self.market_data_tickers = {}
        self.pnl = None
        self.current_pnl = {
            'dailyPnL': 0.0,
            'unrealizedPnL': 0.0,
            'realizedPnL': 0.0,
            'totalPnL': 0.0
        }
        self.open_orders = {}
        self.positions = {}  # Store positions with conId as key
        self.current_spy_price = 598.0  # Set default price to 598
        
    async def connect(self):
        try:
            await self.ib.connectAsync('ib-gateway', 4001, clientId=1)
            # Try to connect with a fixed client ID first
            try:
                await self.ib.connectAsync('127.0.0.1', 7497, clientId=1)
            except Exception as e:
                if "already in use" in str(e).lower():
                    # If client ID is in use, try with a random one
                    client_id = random.randint(100, 999)
                    print(f"Client ID 1 in use, trying with {client_id}")
                    await self.ib.connectAsync('127.0.0.1', 7497, clientId=client_id)
                else:
                    raise

            # Set delayed market data type BEFORE any market data requests
            self.ib.reqMarketDataType(4)  # 4 = Delayed, 1 = Live
            await asyncio.sleep(1)  # Give time for the market data type to be set
            print("Successfully connected to IB and set to delayed market data")
            
            # Register all callbacks
            self.ib.openOrderEvent += self.order_status_monitor
            self.ib.positionEvent += self.position_monitor
            self.ib.updatePortfolioEvent += self.portfolio_monitor
            self.ib.pendingTickersEvent += self.market_data_monitor
            
            # Initialize SPY market data
            await self.initialize_spy_market_data()
            
            # Get initial positions
            print("Getting initial positions...")
            positions = self.ib.positions()
            for position in positions:
                self.position_monitor(position)
                
            # Get initial open orders
            print("Getting initial orders...")
            trades = self.ib.trades()
            for trade in trades:
                self.order_status_monitor(trade)
                
            # Get initial portfolio updates for positions
            print("Getting initial portfolio data...")
            portfolio = self.ib.portfolio()
            for item in portfolio:
                self.portfolio_monitor(item)
                
            # Subscribe to PnL
            await self.subscribe_to_pnl()
            
            print("Initial data sync complete")
            
        except Exception as e:
            print(f"Failed to connect to IB: {e}")
            raise

    async def initialize_spy_market_data(self):
        """Initialize SPY market data subscription"""
        try:
            if 'SPY' not in self.market_data_tickers:  # Only initialize if not already done
                self.ib.reqMarketDataType(4)  # Ensure delayed data
                await asyncio.sleep(0.1)
                
                spy = Stock(symbol='SPY', exchange='SMART', currency='USD')
                qualified = await self.ib.qualifyContractsAsync(spy)
                if qualified:
                    self.market_data_tickers['SPY'] = self.ib.reqMktData(qualified[0])
                    print("Successfully subscribed to SPY delayed market data")
                    await asyncio.sleep(1)  # Give time for initial data
        except Exception as e:
            print(f"Error initializing SPY market data: {e}")

    def market_data_monitor(self, tickers):
        """Monitor market data updates"""
        try:
            for ticker in tickers:
                if ticker.contract.symbol == 'SPY':
                    price = ticker.marketPrice() or ticker.last or ticker.close or 598.0
                    if price and price > 0:
                        self.current_spy_price = float(price)
                        print(f"Updated SPY price: {self.current_spy_price}")
        except Exception as e:
            print(f"Error in market data monitor: {e}")

    def order_status_monitor(self, trade):
        try:
            order = trade.order
            status = trade.orderStatus
            contract = trade.contract
            
            # Track all orders initially, remove only when fully processed
            self.open_orders[order.orderId] = {
                'orderId': order.orderId,
                'contract': {
                    'localSymbol': contract.localSymbol,
                    'secType': contract.secType,
                },
                'action': order.action,
                'totalQuantity': order.totalQuantity,
                'orderType': order.orderType,
                'status': status.status,
                'filled': status.filled,
                'remaining': status.remaining,
                'avgFillPrice': status.avgFillPrice or 0.0,
                'errorMessage': getattr(trade, 'errorMessage', '')  # Add error message if exists
            }
            
            # Only remove orders that are fully processed and complete
            if status.status in ['Filled', 'Cancelled', 'Inactive'] and status.remaining == 0:
                self.open_orders.pop(order.orderId, None)
                
            print(f'\nOrder Update - {contract.symbol}:')
            print(f'Order ID: {order.orderId}, Status: {status.status}')
            print(f'Filled: {status.filled}, Remaining: {status.remaining}')
            if hasattr(trade, 'log'):
                for entry in trade.log:
                    if entry.errorCode:
                        print(f'Error {entry.errorCode}: {entry.message}')
            
        except Exception as e:
            print(f"Error in order status monitor: {e}")

    def position_monitor(self, position):
        try:
            if position.position != 0:  # Only track non-zero positions
                self.positions[position.contract.conId] = {
                    'contract': {
                        'conId': position.contract.conId,
                        'localSymbol': position.contract.localSymbol,
                        'secType': position.contract.secType,
                        'exchange': position.contract.exchange,
                    },
                    'position': position.position,
                    'avgCost': float(position.avgCost),
                    'marketPrice': 0.0,  # Will be updated by portfolio_monitor
                    'unrealizedPNL': 0.0  # Will be updated by portfolio_monitor
                }
            else:
                # Remove closed positions
                self.positions.pop(position.contract.conId, None)
                
            print(f'\nPosition Update - {position.contract.localSymbol}:')
            print(f'Position: {position.position}, Avg Cost: {position.avgCost}')
            
        except Exception as e:
            print(f"Error in position monitor: {e}")

    def portfolio_monitor(self, item):
        try:
            if item.contract.conId in self.positions:
                self.positions[item.contract.conId].update({
                    'marketPrice': float(item.marketPrice),
                    'unrealizedPNL': float(item.unrealizedPNL)
                })
                
            print(f'\nPortfolio Update - {item.contract.localSymbol}:')
            print(f'Market Price: {item.marketPrice}, Unrealized PNL: {item.unrealizedPNL}')
            
        except Exception as e:
            print(f"Error in portfolio monitor: {e}")

    async def get_orders(self):
        """Return only open orders"""
        return list(self.open_orders.values())

    async def disconnect(self):
        """Async disconnect to handle cleanup properly"""
        try:
            # Only attempt cleanup if still connected
            if not self.ib.isConnected():
                return

            # First unregister all callbacks
            try:
                self.ib.openOrderEvent -= self.order_status_monitor
                self.ib.positionEvent -= self.position_monitor
                self.ib.updatePortfolioEvent -= self.portfolio_monitor
                if self.pnl:
                    self.ib.pnlEvent -= self.pnl_callback
            except Exception as e:
                print(f"Error unregistering callbacks: {e}")

            # Then cancel PnL subscription
            try:
                if self.pnl:
                    self.ib.cancelPnL(self.pnl.account, self.pnl.modelCode)
                    self.pnl = None
            except Exception as e:
                print(f"Error canceling PnL subscription: {e}")

            # Cancel market data subscriptions if any exist
            try:
                for ticker in list(self.market_data_tickers.values()):
                    if hasattr(ticker, 'contract'):
                        self.ib.cancelMktData(ticker.contract)
                        await asyncio.sleep(0.1)  # Give time for cancellation to process
                self.market_data_tickers.clear()
            except Exception as e:
                print(f"Error clearing market data tickers: {e}")

            # Finally disconnect
            self.ib.disconnect()

        except Exception as e:
            print(f"Error during disconnect: {e}")

    async def subscribe_to_pnl(self):
        try:
            # Get the first account
            account = self.ib.managedAccounts()[0]
            # Subscribe to PnL updates
            self.pnl = self.ib.reqPnL(account)
            # Register callback using pnlEvent instead of updateEvent
            self.ib.pnlEvent += self.pnl_callback
            print(f"Successfully subscribed to PnL for account {account}")
        except Exception as e:
            print(f"Error subscribing to PnL: {e}")

    def pnl_callback(self, pnl):
        try:
            self.current_pnl = {
                'dailyPnL': float(pnl.dailyPnL or 0),
                'unrealizedPnL': float(pnl.unrealizedPnL or 0),
                'realizedPnL': float(pnl.realizedPnL or 0),
                'totalPnL': float((pnl.unrealizedPnL or 0) + (pnl.realizedPnL or 0))
            }
        except Exception as e:
            print(f"Error in PnL callback: {e}")

    async def get_pnl(self):
        return self.current_pnl

    async def get_spy_price(self):
        """Return current SPY price"""
        try:
            if 'SPY' not in self.market_data_tickers:
                await self.initialize_spy_market_data()
            
            ticker = self.market_data_tickers.get('SPY')
            if ticker:
                price = ticker.marketPrice() or ticker.last or ticker.close or 598.0
                if price and price > 0:
                    self.current_spy_price = float(price)
            
            return self.current_spy_price  # Will return 598.0 if no other price is available
        except Exception as e:
            print(f"Error getting SPY price: {e}")
            return 598.0  # Return 598 on error

    async def get_mes_contract(self):
        try:
            # Specify MES future contract
            contract = Future('MES', exchange='CME', currency='USD')
            # contracts = await self.ib.qualifyContractsAsync(contract)
            contracts = await self.ib.reqContractDetailsAsync(contract)
            # print(contracts)
            # if not contracts:
            #     print("No MES contracts found")
            #     return None
                
            # Simply take the first contract (front month)
            mes_contract = contracts[0].contract
            # print(mes_contract)
            # print(f"Selected MES contract: {mes_contract.localSymbol} (Expiry: {mes_contract.lastTradeDateOrContractMonth})")
            mes_contract = await self.ib.qualifyContractsAsync(mes_contract)
            # print(mes_contract)
            return mes_contract
        except Exception as e:
            print(f"Error getting MES contract: {e}")
            return None

    async def get_spy_option(self, action=None, expiry=None):
        try:
            if 'Buy' in action:
                right = 'C'
                strike = self.settings.call_strike
            else:
                right = 'P'
                strike = self.settings.put_strike

            if not expiry:
                today = datetime.now()
                expiry = today if self.settings.dte == 0 else today + timedelta(days=1)
                expiry = expiry.strftime('%Y%m%d')

            print(f"Creating SPY option: Strike={strike}, Right={right}, Expiry={expiry}")
            
            # Properly specify the option contract
            contract = Option(
                symbol='SPY',
                lastTradeDateOrContractMonth=expiry,
                strike=strike,
                right=right,
                exchange='SMART',
                currency='USD',
                multiplier='100'
            )
            
            # First get contract details to ensure we have the correct contract
            details = await self.ib.reqContractDetailsAsync(contract)
            if not details:
                print("No contract details found")
                return None
                
            # Use the first contract from details
            contract = details[0].contract
            print(f"Using contract: {contract}")
            return contract
            
        except Exception as e:
            print(f"Error getting SPY option: {e}")
            return None

    async def get_positions(self):
        """Return list of current positions"""
        return list(self.positions.values())

    async def process_signal(self, signal):
        try:
            symbol = signal['symbol']
            action = signal['action']
            print(f"Processing signal: {symbol} {action}")
            
            # Handle exit orders
            if 'Exit' in action:
                positions = self.ib.positions()
                print("Current positions:", positions)
                position_found = None
                
                # Find matching position
                for pos in positions:
                    if 'MES' in symbol and pos.contract.symbol == 'MES':
                        position_found = pos
                        break
                    elif 'SPY' in symbol and pos.contract.symbol == 'SPY':
                        # For SPY, only look for option positions
                        if pos.contract.secType == 'OPT':
                            is_long = pos.position > 0
                            is_call = pos.contract.right == 'C'
                            if ('Buy' in action and is_long and is_call) or \
                               ('Sell' in action and is_long and not is_call):
                                position_found = pos
                                break
                
                if not position_found:
                    return {
                        "status": "error", 
                        "message": f"No matching open position found for {symbol}"
                    }
                
                print(f"Closing position: {position_found.contract}")
                # Place exit order with exchange specified
                exit_action = 'SELL' if position_found.position > 0 else 'BUY'
                order = MarketOrder(
                    action=exit_action,
                    totalQuantity=abs(position_found.position)
                )
                trade = self.ib.placeOrder(position_found.contract, order)
                
                return {"status": "success", "order_id": trade.order.orderId}
            
            # Handle new position orders
            if 'MES' in symbol:
                # For futures, we can directly use Buy/Sell as given
                contracts = await self.get_mes_contract()
                if not contracts or len(contracts) == 0:
                    return {"status": "error", "message": "Could not qualify MES contract"}
                contract = contracts[0]
                order_action = 'BUY' if 'Buy' in action else 'SELL'
            elif 'SPY' in symbol:
                # For SPY, we only trade options:
                # If action is "Buy" -> Buy Call option
                # If action is "Sell" -> Buy Put option
                is_buy_signal = 'Buy' in action
                contract = await self.get_spy_option(
                    action='Buy' if is_buy_signal else 'Sell'  # This determines call/put selection
                )
                if not contract:
                    return {"status": "error", "message": "Could not qualify SPY option contract"}
                
                # Verify it's an option contract
                if contract.secType != 'OPT':
                    return {"status": "error", "message": "SPY signals must be for options only"}
                
                order_action = 'BUY'  # Always buy options, we use calls/puts for direction
            else:
                return {"status": "error", "message": "Unsupported symbol"}
            
            if not contract:
                return {"status": "error", "message": "Could not qualify contract"}
            
            print(f"Placing order: {order_action} {contract.localSymbol}")    
            order = MarketOrder(order_action, self.settings.quantity)
            trade = self.ib.placeOrder(contract, order)
            
            return {"status": "success", "order_id": trade.order.orderId}
            
        except Exception as e:
            print(f"Error processing signal: {e}")
            return {"status": "error", "message": str(e)}

    def _clean_message(self, message):
        """Clean numeric values in message"""
        def clean_value(v):
            if isinstance(v, (int, float)):
                if math.isnan(v) or math.isinf(v):
                    return 0.0
                return float(v)
            elif isinstance(v, dict):
                return {k: clean_value(val) for k, val in v.items()}
            elif isinstance(v, list):
                return [clean_value(item) for item in v]
            return v
            
        return clean_value(message)

    async def auto_square_off_task(self):
        while True:
            try:
                est = pytz.timezone('US/Eastern')
                current_time = datetime.now(est).time()
                cutoff_time = time(15, 55)
                
                if current_time >= cutoff_time:
                    positions = await self.get_positions()
                    for pos in positions:
                        await self.close_position(pos['contract']['conId'])
                    await asyncio.sleep(3600 * 8)  # Sleep for 8 hours
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                print(f"Error in auto square off: {e}")
                await asyncio.sleep(60)

    async def close_position(self, position_id: int):
        try:
            positions = self.ib.positions()
            for pos in positions:
                if pos.contract.conId == position_id:
                    action = 'SELL' if pos.position > 0 else 'BUY'
                    order = MarketOrder(action, abs(pos.position))
                    trade = self.ib.placeOrder(pos.contract, order)
                    await asyncio.sleep(0.5)  # Give some time for the order to process
                    await self.resync_data()  # Resync all data
                    return {"status": "success", "message": "Position close order placed"}
            return {"status": "error", "message": "Position not found"}
        except Exception as e:
            print(f"Error closing position: {e}")
            return {"status": "error", "message": str(e)}

    async def cancel_order(self, order_id):
        try:
            trades = self.ib.trades()
            for trade in trades:
                if trade.order.orderId == int(order_id):
                    self.ib.cancelOrder(trade.order)
                    await asyncio.sleep(0.5)  # Give some time for the cancel to process
                    await self.resync_data()  # Resync all data
                    return {"status": "success", "message": "Order cancelled"}
            return {"status": "error", "message": "Order not found"}
        except Exception as e:
            print(f"Error canceling order: {e}")
            return {"status": "error", "message": str(e)}

    # Add error handling for market data subscription errors
    # async def ensure_market_data(self, contract):
    #     """Ensure we're in the event loop when requesting market data"""
    #     try:
    #         # If it's SPY, use the existing subscription
    #         if contract.symbol == 'SPY':
    #             return self.market_data_tickers.get('SPY')
                
    #         loop = asyncio.get_event_loop()
    #         if loop.is_running():
    #             self.ib.reqMarketDataType(4)
    #             await asyncio.sleep(0.1)
                
    #             ticker = self.ib.reqMktData(contract)
    #             await asyncio.sleep(1)
    #             return ticker
    #         else:
    #             print("Event loop is not running")
    #             return None
    #     except Exception as e:
    #         print(f"Error requesting market data: {e}")
    #         return None

    async def resync_data(self):
        """Resync all data from IB"""
        try:
            print("Resyncing data from IB...")
            
            # Resync positions
            positions = self.ib.positions()
            self.positions.clear()  # Clear existing positions
            for position in positions:
                self.position_monitor(position)
                
            # Resync orders
            trades = self.ib.trades()
            self.open_orders.clear()  # Clear existing orders
            for trade in trades:
                self.order_status_monitor(trade)
                
            # Resync portfolio data
            portfolio = self.ib.portfolio()
            for item in portfolio:
                self.portfolio_monitor(item)
                
            print("Data resync complete")
            
        except Exception as e:
            print(f"Error during data resync: {e}")

    def __del__(self):
        """Cleanup resources on object destruction"""
        try:
            if hasattr(self, 'ib') and self.ib.isConnected():
                # Create a new event loop for cleanup if needed
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                # Run disconnect asynchronously
                if loop.is_running():
                    loop.create_task(self.disconnect())
                else:
                    loop.run_until_complete(self.disconnect())
        except Exception as e:
            print(f"Error during cleanup: {e}")