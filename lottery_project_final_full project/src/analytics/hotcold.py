# src/analytics/hotcold.py
"""
Hot/Cold Number Analysis Module.

Identifies "hot" (frequently drawn) and "cold" (rarely drawn) numbers
over various time periods. This is exploratory analysis only.

DISCLAIMER: Past frequency does not predict future draws.
Lottery draws are random and independent events.
"""

import sqlite3
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

class HotColdAnalyzer:
    """Analyze hot and cold numbers across time windows."""
    
    def __init__(self, db_path: str = "data/lottery_star.db"):
        self.db_path = Path(db_path)
        self._validate_db()
    
    def _validate_db(self):
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)
    
    def get_hot_cold_numbers(self, game_name: str, 
                              days: int = 30,
                              top_n: int = 10) -> Dict[str, pd.DataFrame]:
        """
        Get hot and cold numbers for a specific time window.
        
        Args:
            game_name: Set-draw game name
            days: Number of days to look back
            top_n: Number of hot/cold numbers to return
            
        Returns:
            Dict with 'hot' and 'cold' DataFrames
        """
        conn = self._get_connection()
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        query = """
        SELECT fsn.number, COUNT(*) as count
        FROM fact_set_numbers fsn
        JOIN dim_game dg ON fsn.game_id = dg.game_id
        WHERE dg.game_name = ?
          AND fsn.draw_date >= ?
          AND fsn.draw_date <= ?
        GROUP BY fsn.number
        ORDER BY count DESC
        """
        
        df = pd.read_sql_query(query, conn, params=[game_name, start_date, end_date])
        conn.close()
        
        if df.empty:
            return {'hot': pd.DataFrame(), 'cold': pd.DataFrame()}
        
        total = df['count'].sum()
        df['percentage'] = (df['count'] / total * 100).round(2)
        
        hot = df.head(top_n).copy()
        hot['status'] = 'hot'
        
        cold = df.tail(top_n).copy()
        cold['status'] = 'cold'
        
        return {'hot': hot, 'cold': cold}
    
    def get_overdue_numbers(self, game_name: str, 
                            top_n: int = 10) -> pd.DataFrame:
        """
        Find numbers that haven't appeared in the longest time.
        
        Args:
            game_name: Set-draw game name
            top_n: Number of overdue numbers to return
            
        Returns:
            DataFrame with overdue numbers and days since last appearance
        """
        conn = self._get_connection()
        
        query = """
        SELECT fsn.number, MAX(fsn.draw_date) as last_drawn
        FROM fact_set_numbers fsn
        JOIN dim_game dg ON fsn.game_id = dg.game_id
        WHERE dg.game_name = ?
        GROUP BY fsn.number
        ORDER BY last_drawn ASC
        LIMIT ?
        """
        
        df = pd.read_sql_query(query, conn, params=[game_name, top_n])
        conn.close()
        
        if not df.empty:
            df['last_drawn'] = pd.to_datetime(df['last_drawn'])
            df['days_overdue'] = (datetime.now() - df['last_drawn']).dt.days
        
        return df
    
    def get_recent_appearances(self, game_name: str,
                                number: int,
                                limit: int = 20) -> pd.DataFrame:
        """
        Get recent appearances of a specific number.
        
        Args:
            game_name: Set-draw game name
            number: The number to track
            limit: Max number of appearances to return
            
        Returns:
            DataFrame with draw dates where number appeared
        """
        conn = self._get_connection()
        
        query = """
        SELECT fsn.draw_date, fsn.position
        FROM fact_set_numbers fsn
        JOIN dim_game dg ON fsn.game_id = dg.game_id
        WHERE dg.game_name = ?
          AND fsn.number = ?
        ORDER BY fsn.draw_date DESC
        LIMIT ?
        """
        
        df = pd.read_sql_query(query, conn, params=[game_name, number, limit])
        conn.close()
        
        return df
    
    def get_streak_analysis(self, game_name: str) -> pd.DataFrame:
        """
        Analyze consecutive appearance/absence streaks for all numbers.
        
        Returns:
            DataFrame with current streak info for each number
        """
        conn = self._get_connection()
        
        # Get all draws ordered by date
        query = """
        SELECT DISTINCT fsn.draw_date, fsn.number
        FROM fact_set_numbers fsn
        JOIN dim_game dg ON fsn.game_id = dg.game_id
        WHERE dg.game_name = ?
        ORDER BY fsn.draw_date DESC
        """
        
        df = pd.read_sql_query(query, conn, params=[game_name])
        conn.close()
        
        if df.empty:
            return pd.DataFrame()
        
        # Get unique draws and numbers
        all_draws = df['draw_date'].unique()
        all_numbers = df['number'].unique()
        
        # Calculate current streak (consecutive draws with/without number)
        streaks = []
        for num in all_numbers:
            num_draws = set(df[df['number'] == num]['draw_date'])
            current_streak = 0
            streak_type = None
            
            for draw in all_draws:
                if streak_type is None:
                    streak_type = 'appearing' if draw in num_draws else 'absent'
                    current_streak = 1
                elif (draw in num_draws and streak_type == 'appearing') or \
                     (draw not in num_draws and streak_type == 'absent'):
                    current_streak += 1
                else:
                    break
            
            streaks.append({
                'number': num,
                'streak_type': streak_type,
                'streak_length': current_streak
            })
        
        return pd.DataFrame(streaks).sort_values('streak_length', ascending=False)
    
    def get_hot_cold_trend(self, game_name: str, 
                           windows: List[int] = [7, 30, 90, 365]) -> pd.DataFrame:
        """
        Compare hot/cold status across multiple time windows.
        
        Args:
            game_name: Set-draw game name
            windows: List of day windows to compare
            
        Returns:
            DataFrame showing number frequency across windows
        """
        results = []
        
        for days in windows:
            data = self.get_hot_cold_numbers(game_name, days=days, top_n=999)
            combined = pd.concat([data['hot'], data['cold']])
            combined['window_days'] = days
            results.append(combined)
        
        if not results:
            return pd.DataFrame()
        
        df = pd.concat(results, ignore_index=True)
        
        # Pivot to show numbers across windows
        pivot = df.pivot_table(
            index='number', 
            columns='window_days', 
            values='count',
            aggfunc='first'
        ).reset_index()
        
        return pivot
