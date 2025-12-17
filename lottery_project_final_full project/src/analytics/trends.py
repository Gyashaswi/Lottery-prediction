# src/analytics/trends.py
"""
Time Trend Analysis Module for NY Lottery Data.

Analyzes patterns and trends over time including:
- Seasonal patterns
- Day-of-week patterns
- Monthly/yearly trends
- Rolling statistics

DISCLAIMER: Historical patterns do not predict future outcomes.
Lottery draws are random and independent.
"""

import sqlite3
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict, List, Optional

class TrendAnalyzer:
    """Analyze time-based trends in lottery data."""
    
    def __init__(self, db_path: str = "data/lottery_star.db"):
        self.db_path = Path(db_path)
        self._validate_db()
    
    def _validate_db(self):
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)
    
    def get_weekday_distribution(self, game_name: str) -> pd.DataFrame:
        """
        Analyze number frequency by day of week.
        
        Args:
            game_name: Set-draw game name
            
        Returns:
            DataFrame with weekday distribution
        """
        conn = self._get_connection()
        
        query = """
        SELECT dd.weekday, fsn.number, COUNT(*) as count
        FROM fact_set_numbers fsn
        JOIN dim_game dg ON fsn.game_id = dg.game_id
        JOIN dim_date dd ON fsn.draw_date = dd.date
        WHERE dg.game_name = ?
        GROUP BY dd.weekday, fsn.number
        ORDER BY dd.weekday, count DESC
        """
        
        df = pd.read_sql_query(query, conn, params=[game_name])
        conn.close()
        
        return df
    
    def get_monthly_stats(self, game_name: str) -> pd.DataFrame:
        """
        Get monthly statistics for a game.
        
        Returns:
            DataFrame with monthly draw counts and number stats
        """
        conn = self._get_connection()
        
        query = """
        SELECT 
            dd.year,
            dd.month,
            COUNT(DISTINCT fsn.draw_date) as draw_count,
            AVG(fsn.number) as avg_number,
            MIN(fsn.number) as min_number,
            MAX(fsn.number) as max_number
        FROM fact_set_numbers fsn
        JOIN dim_game dg ON fsn.game_id = dg.game_id
        JOIN dim_date dd ON fsn.draw_date = dd.date
        WHERE dg.game_name = ?
        GROUP BY dd.year, dd.month
        ORDER BY dd.year, dd.month
        """
        
        df = pd.read_sql_query(query, conn, params=[game_name])
        conn.close()
        
        return df
    
    def get_yearly_comparison(self, game_name: str) -> pd.DataFrame:
        """
        Compare number frequencies across years.
        
        Returns:
            DataFrame with yearly number frequencies
        """
        conn = self._get_connection()
        
        query = """
        SELECT 
            dd.year,
            fsn.number,
            COUNT(*) as count
        FROM fact_set_numbers fsn
        JOIN dim_game dg ON fsn.game_id = dg.game_id
        JOIN dim_date dd ON fsn.draw_date = dd.date
        WHERE dg.game_name = ?
        GROUP BY dd.year, fsn.number
        ORDER BY dd.year, count DESC
        """
        
        df = pd.read_sql_query(query, conn, params=[game_name])
        conn.close()
        
        return df
    
    def get_rolling_frequency(self, game_name: str, 
                               number: int,
                               window: int = 30) -> pd.DataFrame:
        """
        Calculate rolling frequency for a specific number.
        
        Args:
            game_name: Set-draw game name
            number: Number to track
            window: Rolling window size in draws
            
        Returns:
            DataFrame with rolling frequency over time
        """
        conn = self._get_connection()
        
        # Get all draws and mark if number appeared
        query = """
        SELECT DISTINCT fsd.draw_date
        FROM fact_set_draws fsd
        JOIN dim_game dg ON fsd.game_id = dg.game_id
        WHERE dg.game_name = ?
        ORDER BY fsd.draw_date
        """
        
        all_draws = pd.read_sql_query(query, conn, params=[game_name])
        
        query2 = """
        SELECT fsn.draw_date
        FROM fact_set_numbers fsn
        JOIN dim_game dg ON fsn.game_id = dg.game_id
        WHERE dg.game_name = ? AND fsn.number = ?
        """
        
        num_draws = pd.read_sql_query(query2, conn, params=[game_name, number])
        conn.close()
        
        if all_draws.empty:
            return pd.DataFrame()
        
        # Create binary indicator
        all_draws['appeared'] = all_draws['draw_date'].isin(num_draws['draw_date']).astype(int)
        all_draws['rolling_freq'] = all_draws['appeared'].rolling(window=window, min_periods=1).mean() * 100
        
        return all_draws
    
    def get_gap_analysis(self, game_name: str) -> pd.DataFrame:
        """
        Analyze gaps between appearances for each number.
        
        Returns:
            DataFrame with gap statistics per number
        """
        conn = self._get_connection()
        
        query = """
        SELECT fsn.number, fsn.draw_date
        FROM fact_set_numbers fsn
        JOIN dim_game dg ON fsn.game_id = dg.game_id
        WHERE dg.game_name = ?
        ORDER BY fsn.number, fsn.draw_date
        """
        
        df = pd.read_sql_query(query, conn, params=[game_name])
        conn.close()
        
        if df.empty:
            return pd.DataFrame()
        
        df['draw_date'] = pd.to_datetime(df['draw_date'])
        
        # Calculate gaps per number
        gap_stats = []
        for num in df['number'].unique():
            num_df = df[df['number'] == num].sort_values('draw_date')
            gaps = num_df['draw_date'].diff().dt.days.dropna()
            
            if len(gaps) > 0:
                gap_stats.append({
                    'number': num,
                    'avg_gap': gaps.mean(),
                    'min_gap': gaps.min(),
                    'max_gap': gaps.max(),
                    'std_gap': gaps.std(),
                    'total_appearances': len(num_df)
                })
        
        return pd.DataFrame(gap_stats).sort_values('avg_gap')
    
    def get_draw_history(self, game_name: str, 
                          limit: int = 100) -> pd.DataFrame:
        """
        Get recent draw history for a game.
        
        Returns:
            DataFrame with recent draws and their numbers
        """
        conn = self._get_connection()
        
        query = """
        SELECT 
            fsd.draw_date,
            GROUP_CONCAT(fsn.number, ',') as numbers,
            fsd.bonus
        FROM fact_set_draws fsd
        JOIN fact_set_numbers fsn ON fsd.game_id = fsn.game_id AND fsd.draw_date = fsn.draw_date
        JOIN dim_game dg ON fsd.game_id = dg.game_id
        WHERE dg.game_name = ?
        GROUP BY fsd.draw_date, fsd.bonus
        ORDER BY fsd.draw_date DESC
        LIMIT ?
        """
        
        df = pd.read_sql_query(query, conn, params=[game_name, limit])
        conn.close()
        
        return df
    
    def get_sum_trend(self, game_name: str) -> pd.DataFrame:
        """
        Track the sum of drawn numbers over time.
        
        Returns:
            DataFrame with date and sum trend
        """
        conn = self._get_connection()
        
        query = """
        SELECT 
            fsn.draw_date,
            SUM(fsn.number) as total_sum
        FROM fact_set_numbers fsn
        JOIN dim_game dg ON fsn.game_id = dg.game_id
        WHERE dg.game_name = ?
        GROUP BY fsn.draw_date
        ORDER BY fsn.draw_date
        """
        
        df = pd.read_sql_query(query, conn, params=[game_name])
        conn.close()
        
        if not df.empty:
            df['draw_date'] = pd.to_datetime(df['draw_date'])
            df['rolling_avg'] = df['total_sum'].rolling(window=30, min_periods=1).mean()
        
        return df
