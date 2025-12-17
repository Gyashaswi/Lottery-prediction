# src/analytics/frequency.py
"""
Frequency Analysis Module for NY Lottery Data.

Analyzes historical frequency of numbers across different lottery games.
This is purely exploratory analysis - not predictive.
"""

import sqlite3
from pathlib import Path
import pandas as pd
import numpy as np
from collections import Counter
from typing import Dict, List, Tuple, Optional

class FrequencyAnalyzer:
    """Analyze number frequencies across lottery games."""
    
    def __init__(self, db_path: str = "data/lottery_star.db"):
        self.db_path = Path(db_path)
        self._validate_db()
    
    def _validate_db(self):
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)
    
    def get_set_draw_frequencies(self, game_name: str, 
                                   start_date: Optional[str] = None,
                                   end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Get frequency of each number for a set-draw game.
        
        Args:
            game_name: mega_millions, powerball, take5, cash4life, ny_lotto
            start_date: Optional start date filter (YYYY-MM-DD)
            end_date: Optional end date filter (YYYY-MM-DD)
            
        Returns:
            DataFrame with columns: number, count, percentage
        """
        conn = self._get_connection()
        
        query = """
        SELECT fsn.number, COUNT(*) as count
        FROM fact_set_numbers fsn
        JOIN dim_game dg ON fsn.game_id = dg.game_id
        WHERE dg.game_name = ?
        """
        params = [game_name]
        
        if start_date:
            query += " AND fsn.draw_date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND fsn.draw_date <= ?"
            params.append(end_date)
            
        query += " GROUP BY fsn.number ORDER BY count DESC"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        if not df.empty:
            total = df['count'].sum()
            df['percentage'] = (df['count'] / total * 100).round(2)
        
        return df
    
    def get_bonus_frequencies(self, game_name: str,
                               start_date: Optional[str] = None,
                               end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Get frequency of bonus numbers (Mega Ball, Powerball, Cash Ball).
        
        Args:
            game_name: mega_millions, powerball, cash4life
            
        Returns:
            DataFrame with columns: bonus, count, percentage
        """
        conn = self._get_connection()
        
        query = """
        SELECT fsd.bonus, COUNT(*) as count
        FROM fact_set_draws fsd
        JOIN dim_game dg ON fsd.game_id = dg.game_id
        WHERE dg.game_name = ? AND fsd.bonus IS NOT NULL AND fsd.bonus != ''
        """
        params = [game_name]
        
        if start_date:
            query += " AND fsd.draw_date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND fsd.draw_date <= ?"
            params.append(end_date)
            
        query += " GROUP BY fsd.bonus ORDER BY count DESC"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        if not df.empty:
            df['bonus'] = pd.to_numeric(df['bonus'], errors='coerce')
            df = df.dropna(subset=['bonus'])
            df['bonus'] = df['bonus'].astype(int)
            total = df['count'].sum()
            df['percentage'] = (df['count'] / total * 100).round(2)
        
        return df.sort_values('count', ascending=False)
    
    def get_daily_digit_frequencies(self, game_name: str,
                                     position: Optional[int] = None) -> pd.DataFrame:
        """
        Get digit frequency for daily games (Numbers 3-digit, Win4 4-digit).
        
        Args:
            game_name: 'numbers' or 'win4'
            position: Optional position (1-3 for numbers, 1-4 for win4)
            
        Returns:
            DataFrame with digit frequencies
        """
        conn = self._get_connection()
        
        query = """
        SELECT fdd.pick
        FROM fact_daily_draws fdd
        JOIN dim_game dg ON fdd.game_id = dg.game_id
        WHERE dg.game_name = ?
        """
        
        df = pd.read_sql_query(query, conn, params=[game_name])
        conn.close()
        
        if df.empty:
            return pd.DataFrame()
        
        # Count digits by position
        num_positions = 3 if game_name == 'numbers' else 4
        
        results = []
        for pos in range(num_positions):
            if position is not None and pos + 1 != position:
                continue
            digits = df['pick'].str[pos].value_counts().reset_index()
            digits.columns = ['digit', 'count']
            digits['position'] = pos + 1
            digits['percentage'] = (digits['count'] / len(df) * 100).round(2)
            results.append(digits)
        
        return pd.concat(results, ignore_index=True) if results else pd.DataFrame()
    
    def get_pair_frequencies(self, game_name: str, top_n: int = 20) -> pd.DataFrame:
        """
        Get frequency of number pairs appearing together.
        
        Args:
            game_name: Set-draw game name
            top_n: Number of top pairs to return
            
        Returns:
            DataFrame with pair frequencies
        """
        conn = self._get_connection()
        
        query = """
        SELECT fsn1.number as num1, fsn2.number as num2, COUNT(*) as count
        FROM fact_set_numbers fsn1
        JOIN fact_set_numbers fsn2 
            ON fsn1.game_id = fsn2.game_id 
            AND fsn1.draw_date = fsn2.draw_date 
            AND fsn1.number < fsn2.number
        JOIN dim_game dg ON fsn1.game_id = dg.game_id
        WHERE dg.game_name = ?
        GROUP BY fsn1.number, fsn2.number
        ORDER BY count DESC
        LIMIT ?
        """
        
        df = pd.read_sql_query(query, conn, params=[game_name, top_n])
        conn.close()
        
        return df
    
    def get_sum_distribution(self, game_name: str) -> pd.DataFrame:
        """
        Get distribution of number sums for a set-draw game.
        
        Args:
            game_name: Set-draw game name
            
        Returns:
            DataFrame with sum distribution
        """
        conn = self._get_connection()
        
        query = """
        SELECT fsn.draw_date, SUM(fsn.number) as total_sum
        FROM fact_set_numbers fsn
        JOIN dim_game dg ON fsn.game_id = dg.game_id
        WHERE dg.game_name = ?
        GROUP BY fsn.game_id, fsn.draw_date
        """
        
        df = pd.read_sql_query(query, conn, params=[game_name])
        conn.close()
        
        if df.empty:
            return pd.DataFrame()
        
        # Create distribution
        dist = df['total_sum'].value_counts().reset_index()
        dist.columns = ['sum', 'count']
        dist['percentage'] = (dist['count'] / len(df) * 100).round(2)
        
        return dist.sort_values('sum')
    
    def get_odd_even_distribution(self, game_name: str) -> pd.DataFrame:
        """
        Analyze odd/even number distribution per draw.
        
        Returns:
            DataFrame with odd_count vs frequency
        """
        conn = self._get_connection()
        
        query = """
        SELECT fsn.draw_date, 
               SUM(CASE WHEN fsn.number % 2 = 1 THEN 1 ELSE 0 END) as odd_count,
               SUM(CASE WHEN fsn.number % 2 = 0 THEN 1 ELSE 0 END) as even_count
        FROM fact_set_numbers fsn
        JOIN dim_game dg ON fsn.game_id = dg.game_id
        WHERE dg.game_name = ?
        GROUP BY fsn.game_id, fsn.draw_date
        """
        
        df = pd.read_sql_query(query, conn, params=[game_name])
        conn.close()
        
        if df.empty:
            return pd.DataFrame()
        
        # Summarize distribution
        dist = df.groupby(['odd_count', 'even_count']).size().reset_index(name='frequency')
        dist['percentage'] = (dist['frequency'] / len(df) * 100).round(2)
        
        return dist.sort_values('frequency', ascending=False)
