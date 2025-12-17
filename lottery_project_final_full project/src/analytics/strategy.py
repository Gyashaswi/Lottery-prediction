# src/analytics/strategy.py
"""
Strategy Exploration Module for NY Lottery.

Compares different number selection approaches through simulation.
This is purely for educational exploration.

IMPORTANT DISCLAIMER:
- No strategy can improve your odds of winning the lottery
- All lottery draws are random and independent
- Past results do not influence future outcomes
- The house edge is mathematically guaranteed
- This module is for entertainment and education only
"""

import random
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Callable
from collections import Counter
import sqlite3
from pathlib import Path

class StrategyExplorer:
    """Explore and compare different number selection strategies.
    
    DISCLAIMER: All strategies have identical mathematical odds.
    Differences in simulation results are due to random variance only.
    """
    
    def __init__(self, db_path: str = "data/lottery_star.db"):
        self.db_path = Path(db_path)
    
    def _get_connection(self) -> sqlite3.Connection:
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        return sqlite3.connect(self.db_path)
    
    def random_strategy(self, pool_size: int, pick_count: int) -> set:
        """Pure random selection (Quick Pick)."""
        return set(random.sample(range(1, pool_size + 1), pick_count))
    
    def hot_numbers_strategy(self, game_name: str, pool_size: int, 
                              pick_count: int, lookback_days: int = 90) -> set:
        """
        Select from most frequently drawn numbers.
        
        NOTE: This has no mathematical advantage over random selection.
        """
        conn = self._get_connection()
        
        query = """
        SELECT fsn.number, COUNT(*) as freq
        FROM fact_set_numbers fsn
        JOIN dim_game dg ON fsn.game_id = dg.game_id
        WHERE dg.game_name = ?
          AND fsn.draw_date >= date('now', '-' || ? || ' days')
        GROUP BY fsn.number
        ORDER BY freq DESC
        LIMIT ?
        """
        
        df = pd.read_sql_query(query, conn, params=[game_name, lookback_days, pick_count * 2])
        conn.close()
        
        if len(df) < pick_count:
            return self.random_strategy(pool_size, pick_count)
        
        hot_numbers = df['number'].tolist()
        return set(random.sample(hot_numbers[:pick_count * 2], pick_count))
    
    def cold_numbers_strategy(self, game_name: str, pool_size: int,
                               pick_count: int, lookback_days: int = 90) -> set:
        """
        Select from least frequently drawn numbers ("due" numbers).
        
        NOTE: This has no mathematical advantage. Numbers are not "due".
        """
        conn = self._get_connection()
        
        query = """
        SELECT fsn.number, COUNT(*) as freq
        FROM fact_set_numbers fsn
        JOIN dim_game dg ON fsn.game_id = dg.game_id
        WHERE dg.game_name = ?
          AND fsn.draw_date >= date('now', '-' || ? || ' days')
        GROUP BY fsn.number
        ORDER BY freq ASC
        LIMIT ?
        """
        
        df = pd.read_sql_query(query, conn, params=[game_name, lookback_days, pick_count * 2])
        conn.close()
        
        if len(df) < pick_count:
            return self.random_strategy(pool_size, pick_count)
        
        cold_numbers = df['number'].tolist()
        return set(random.sample(cold_numbers[:pick_count * 2], pick_count))
    
    def balanced_strategy(self, pool_size: int, pick_count: int) -> set:
        """
        Select balanced mix of low and high numbers.
        
        NOTE: This has no mathematical advantage over random selection.
        """
        mid = pool_size // 2
        low_count = pick_count // 2
        high_count = pick_count - low_count
        
        low_nums = random.sample(range(1, mid + 1), low_count)
        high_nums = random.sample(range(mid + 1, pool_size + 1), high_count)
        
        return set(low_nums + high_nums)
    
    def odd_even_balanced_strategy(self, pool_size: int, pick_count: int) -> set:
        """
        Select balanced mix of odd and even numbers.
        
        NOTE: This has no mathematical advantage over random selection.
        """
        odds = [n for n in range(1, pool_size + 1) if n % 2 == 1]
        evens = [n for n in range(1, pool_size + 1) if n % 2 == 0]
        
        odd_count = pick_count // 2
        even_count = pick_count - odd_count
        
        selected_odds = random.sample(odds, min(odd_count, len(odds)))
        selected_evens = random.sample(evens, min(even_count, len(evens)))
        
        return set(selected_odds + selected_evens)
    
    def spread_strategy(self, pool_size: int, pick_count: int) -> set:
        """
        Select numbers spread across the range.
        
        NOTE: This has no mathematical advantage over random selection.
        """
        segment_size = pool_size // pick_count
        numbers = []
        
        for i in range(pick_count):
            start = i * segment_size + 1
            end = min((i + 1) * segment_size, pool_size)
            numbers.append(random.randint(start, end))
        
        # Handle duplicates
        while len(set(numbers)) < pick_count:
            numbers = list(set(numbers))
            remaining = pick_count - len(numbers)
            available = [n for n in range(1, pool_size + 1) if n not in numbers]
            numbers.extend(random.sample(available, remaining))
        
        return set(numbers)
    
    def compare_strategies(self, game_name: str,
                           num_simulations: int = 10000,
                           pool_size: int = 70,
                           pick_count: int = 5) -> pd.DataFrame:
        """
        Compare multiple strategies through simulation.
        
        IMPORTANT: All strategies have identical expected outcomes.
        Any differences are due to random variance, not strategy effectiveness.
        
        Returns:
            DataFrame comparing strategy simulation results
        """
        strategies = {
            'random': lambda: self.random_strategy(pool_size, pick_count),
            'hot_numbers': lambda: self.hot_numbers_strategy(game_name, pool_size, pick_count),
            'cold_numbers': lambda: self.cold_numbers_strategy(game_name, pool_size, pick_count),
            'balanced': lambda: self.balanced_strategy(pool_size, pick_count),
            'odd_even': lambda: self.odd_even_balanced_strategy(pool_size, pick_count),
            'spread': lambda: self.spread_strategy(pool_size, pick_count),
        }
        
        results = []
        
        for strategy_name, strategy_func in strategies.items():
            matches_total = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            
            for _ in range(num_simulations):
                # Generate ticket using strategy
                ticket = strategy_func()
                
                # Simulate draw (random)
                drawn = set(random.sample(range(1, pool_size + 1), pick_count))
                
                # Count matches
                matches = len(ticket & drawn)
                matches_total[matches] += 1
            
            # Calculate match percentages
            result = {
                'strategy': strategy_name,
                'simulations': num_simulations,
            }
            
            for m in range(pick_count + 1):
                result[f'{m}_matches'] = matches_total.get(m, 0)
                result[f'{m}_matches_pct'] = round(matches_total.get(m, 0) / num_simulations * 100, 2)
            
            results.append(result)
        
        return pd.DataFrame(results)
    
    def wheel_system_demo(self, numbers: List[int], 
                          pick_count: int = 5) -> List[set]:
        """
        Demonstrate a wheeling system (abbreviated coverage).
        
        A wheel system generates multiple combinations to guarantee
        certain match levels if your chosen numbers are drawn.
        
        NOTE: Wheels cost more tickets but don't change overall odds.
        They redistribute wins, not improve expected value.
        
        Args:
            numbers: List of chosen numbers (e.g., 8 numbers)
            pick_count: Numbers per ticket
            
        Returns:
            List of ticket combinations
        """
        from itertools import combinations
        
        if len(numbers) < pick_count:
            return [set(numbers)]
        
        # For demonstration, create a reduced wheel
        # Full wheel would be all combinations
        all_combos = list(combinations(numbers, pick_count))
        
        # Abbreviated wheel - select representative combinations
        # This is a simplified demo; real wheels are carefully designed
        if len(all_combos) <= 10:
            return [set(c) for c in all_combos]
        
        # For larger sets, sample strategically
        step = max(1, len(all_combos) // 10)
        selected = [all_combos[i] for i in range(0, len(all_combos), step)][:10]
        
        return [set(c) for c in selected]
    
    def analyze_historical_strategy_backtest(self, game_name: str,
                                              strategy: str = 'hot',
                                              lookback: int = 30,
                                              test_draws: int = 100) -> pd.DataFrame:
        """
        Backtest a strategy against historical draws.
        
        NOTE: This shows what WOULD have happened, not what WILL happen.
        Past performance does not predict future results.
        
        Args:
            game_name: Game to backtest
            strategy: 'hot', 'cold', or 'random'
            lookback: Days to look back for hot/cold calculation
            test_draws: Number of draws to test
            
        Returns:
            DataFrame with backtest results
        """
        conn = self._get_connection()
        
        # Get historical draws
        query = """
        SELECT fsd.draw_date, GROUP_CONCAT(fsn.number) as numbers
        FROM fact_set_draws fsd
        JOIN fact_set_numbers fsn ON fsd.game_id = fsn.game_id AND fsd.draw_date = fsn.draw_date
        JOIN dim_game dg ON fsd.game_id = dg.game_id
        WHERE dg.game_name = ?
        GROUP BY fsd.draw_date
        ORDER BY fsd.draw_date DESC
        LIMIT ?
        """
        
        draws = pd.read_sql_query(query, conn, params=[game_name, test_draws + lookback])
        conn.close()
        
        if len(draws) < test_draws + lookback:
            return pd.DataFrame({'error': ['Insufficient historical data']})
        
        results = []
        
        for i in range(test_draws):
            test_draw = draws.iloc[i]
            history = draws.iloc[i + 1:i + 1 + lookback]
            
            # Parse actual drawn numbers
            actual_numbers = set(int(n) for n in test_draw['numbers'].split(','))
            pick_count = len(actual_numbers)
            
            # Calculate hot/cold from history
            all_historical = []
            for _, row in history.iterrows():
                all_historical.extend(int(n) for n in row['numbers'].split(','))
            
            freq = Counter(all_historical)
            
            # Generate strategy picks
            if strategy == 'hot':
                sorted_nums = sorted(freq.keys(), key=lambda x: freq[x], reverse=True)
                strategy_pick = set(sorted_nums[:pick_count])
            elif strategy == 'cold':
                sorted_nums = sorted(freq.keys(), key=lambda x: freq[x])
                strategy_pick = set(sorted_nums[:pick_count])
            else:  # random
                pool = max(freq.keys()) if freq else 70
                strategy_pick = set(random.sample(range(1, pool + 1), pick_count))
            
            matches = len(strategy_pick & actual_numbers)
            
            results.append({
                'draw_date': test_draw['draw_date'],
                'strategy': strategy,
                'matches': matches,
                'pick_count': pick_count
            })
        
        return pd.DataFrame(results)
    
    def get_strategy_summary(self) -> str:
        """
        Return educational summary about lottery strategies.
        """
        return """
        LOTTERY STRATEGY EXPLORATION - EDUCATIONAL SUMMARY
        ================================================
        
        IMPORTANT FACTS:
        
        1. ALL STRATEGIES HAVE IDENTICAL EXPECTED VALUE
           - The lottery is designed with a fixed house edge
           - No selection method can change mathematical odds
           - "Hot" and "cold" numbers are equally likely to appear
        
        2. THE GAMBLER'S FALLACY
           - Past results don't influence future draws
           - Numbers aren't "due" to appear
           - Each draw is independent
        
        3. WHAT STRATEGIES CAN DO:
           - Reduce likelihood of sharing jackpot (avoid popular numbers)
           - Provide structure for entertainment value
           - Help with budget management (fixed play patterns)
        
        4. WHAT STRATEGIES CANNOT DO:
           - Improve odds of winning
           - Predict future numbers
           - Create positive expected value
        
        5. RESPONSIBLE GAMING:
           - Only play what you can afford to lose
           - Lottery should be entertainment, not investment
           - The expected return is always negative
        
        This module is for educational exploration only.
        """
