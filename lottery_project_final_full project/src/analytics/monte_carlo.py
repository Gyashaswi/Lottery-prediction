# src/analytics/monte_carlo.py
"""
Monte Carlo Simulation Module for Lottery Strategy Exploration.

Simulates lottery outcomes to understand variance and long-term expectations.
This is for educational/exploratory purposes only.

DISCLAIMER: Simulations demonstrate mathematical expectations.
They do not provide any advantage in actual lottery play.
The only guaranteed outcome is the house edge.
"""

import random
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import Counter
import math

@dataclass
class SimulationResult:
    """Results from a Monte Carlo simulation."""
    total_spent: float
    total_won: float
    net_result: float
    roi_percentage: float
    wins_by_tier: Dict[str, int]
    jackpot_wins: int
    simulations: int

class MonteCarloSimulator:
    """Monte Carlo simulations for lottery strategy exploration."""
    
    # Game configurations
    GAME_CONFIGS = {
        'mega_millions': {
            'main_pool': 70, 'main_pick': 5,
            'bonus_pool': 25, 'ticket_cost': 2.0,
            'prizes': {
                (5, 1): 20_000_000,  # Jackpot (use fixed for simulation)
                (5, 0): 1_000_000,
                (4, 1): 10_000,
                (4, 0): 500,
                (3, 1): 200,
                (3, 0): 10,
                (2, 1): 10,
                (1, 1): 4,
                (0, 1): 2,
            }
        },
        'powerball': {
            'main_pool': 69, 'main_pick': 5,
            'bonus_pool': 26, 'ticket_cost': 2.0,
            'prizes': {
                (5, 1): 20_000_000,
                (5, 0): 1_000_000,
                (4, 1): 50_000,
                (4, 0): 100,
                (3, 1): 100,
                (3, 0): 7,
                (2, 1): 7,
                (1, 1): 4,
                (0, 1): 4,
            }
        },
        'take5': {
            'main_pool': 39, 'main_pick': 5,
            'bonus_pool': 0, 'ticket_cost': 1.0,
            'prizes': {
                (5, 0): 50_000,  # Typical jackpot
                (4, 0): 500,
                (3, 0): 25,
                (2, 0): 1,  # Free play
            }
        },
        'numbers': {
            'main_pool': 10, 'main_pick': 3,
            'bonus_pool': 0, 'ticket_cost': 0.5,
            'prizes': {
                (3, 0): 500,  # Straight
            }
        },
        'win4': {
            'main_pool': 10, 'main_pick': 4,
            'bonus_pool': 0, 'ticket_cost': 0.5,
            'prizes': {
                (4, 0): 5000,  # Straight
            }
        }
    }
    
    def __init__(self, seed: Optional[int] = None):
        if seed:
            random.seed(seed)
            np.random.seed(seed)
    
    def simulate_draw(self, game_name: str) -> Tuple[set, int]:
        """
        Simulate a single lottery draw.
        
        Returns:
            Tuple of (main_numbers set, bonus_number)
        """
        config = self.GAME_CONFIGS[game_name]
        main_numbers = set(random.sample(range(1, config['main_pool'] + 1), config['main_pick']))
        bonus = random.randint(1, config['bonus_pool']) if config['bonus_pool'] > 0 else 0
        return main_numbers, bonus
    
    def check_ticket(self, game_name: str, 
                     ticket_main: set, ticket_bonus: int,
                     drawn_main: set, drawn_bonus: int) -> Tuple[int, int]:
        """
        Check how many matches a ticket has.
        
        Returns:
            Tuple of (main_matches, bonus_match)
        """
        main_matches = len(ticket_main & drawn_main)
        bonus_match = 1 if ticket_bonus == drawn_bonus else 0
        return main_matches, bonus_match
    
    def get_prize(self, game_name: str, main_matches: int, bonus_match: int) -> float:
        """
        Get prize amount for given matches.
        """
        config = self.GAME_CONFIGS[game_name]
        return config['prizes'].get((main_matches, bonus_match), 0)
    
    def simulate_plays(self, game_name: str, 
                       num_tickets: int,
                       num_simulations: int = 10000,
                       strategy: str = 'random') -> SimulationResult:
        """
        Simulate playing the lottery multiple times.
        
        Args:
            game_name: Name of the game
            num_tickets: Number of tickets per simulation
            num_simulations: Number of simulation runs
            strategy: 'random' or 'quick_pick' (both are random, naming for clarity)
            
        Returns:
            SimulationResult with aggregated stats
        """
        if game_name not in self.GAME_CONFIGS:
            raise ValueError(f"Unknown game: {game_name}")
        
        config = self.GAME_CONFIGS[game_name]
        total_spent = 0
        total_won = 0
        wins_by_tier = Counter()
        jackpot_wins = 0
        
        for _ in range(num_simulations):
            # Draw winning numbers
            drawn_main, drawn_bonus = self.simulate_draw(game_name)
            
            # Generate and check tickets
            for _ in range(num_tickets):
                ticket_main = set(random.sample(range(1, config['main_pool'] + 1), config['main_pick']))
                ticket_bonus = random.randint(1, config['bonus_pool']) if config['bonus_pool'] > 0 else 0
                
                main_matches, bonus_match = self.check_ticket(
                    game_name, ticket_main, ticket_bonus, drawn_main, drawn_bonus
                )
                
                prize = self.get_prize(game_name, main_matches, bonus_match)
                total_won += prize
                total_spent += config['ticket_cost']
                
                if prize > 0:
                    tier = f"{main_matches}+{bonus_match}"
                    wins_by_tier[tier] += 1
                    if main_matches == config['main_pick'] and (config['bonus_pool'] == 0 or bonus_match == 1):
                        jackpot_wins += 1
        
        net_result = total_won - total_spent
        roi = (net_result / total_spent * 100) if total_spent > 0 else 0
        
        return SimulationResult(
            total_spent=total_spent,
            total_won=total_won,
            net_result=net_result,
            roi_percentage=round(roi, 2),
            wins_by_tier=dict(wins_by_tier),
            jackpot_wins=jackpot_wins,
            simulations=num_simulations * num_tickets
        )
    
    def simulate_weekly_play(self, game_name: str,
                              tickets_per_week: int,
                              years: int = 10) -> pd.DataFrame:
        """
        Simulate weekly play over multiple years.
        
        Returns:
            DataFrame with weekly results over time
        """
        config = self.GAME_CONFIGS[game_name]
        weeks = years * 52
        
        results = []
        cumulative_spent = 0
        cumulative_won = 0
        
        for week in range(weeks):
            weekly_spent = tickets_per_week * config['ticket_cost']
            weekly_won = 0
            
            # Simulate week's draws (assume 2 draws per week for major games)
            draws_per_week = 2 if game_name in ['mega_millions', 'powerball'] else 7
            
            for _ in range(draws_per_week):
                drawn_main, drawn_bonus = self.simulate_draw(game_name)
                
                tickets_this_draw = tickets_per_week // draws_per_week
                for _ in range(max(1, tickets_this_draw)):
                    ticket_main = set(random.sample(range(1, config['main_pool'] + 1), config['main_pick']))
                    ticket_bonus = random.randint(1, config['bonus_pool']) if config['bonus_pool'] > 0 else 0
                    
                    main_matches, bonus_match = self.check_ticket(
                        game_name, ticket_main, ticket_bonus, drawn_main, drawn_bonus
                    )
                    weekly_won += self.get_prize(game_name, main_matches, bonus_match)
            
            cumulative_spent += weekly_spent
            cumulative_won += weekly_won
            
            results.append({
                'week': week + 1,
                'year': week // 52 + 1,
                'weekly_spent': weekly_spent,
                'weekly_won': weekly_won,
                'weekly_net': weekly_won - weekly_spent,
                'cumulative_spent': cumulative_spent,
                'cumulative_won': cumulative_won,
                'cumulative_net': cumulative_won - cumulative_spent,
                'roi_pct': (cumulative_won - cumulative_spent) / cumulative_spent * 100 if cumulative_spent > 0 else 0
            })
        
        return pd.DataFrame(results)
    
    def run_convergence_test(self, game_name: str,
                              max_simulations: int = 100000,
                              check_points: int = 20) -> pd.DataFrame:
        """
        Show how ROI converges to expected value over many simulations.
        
        Returns:
            DataFrame showing convergence over simulation count
        """
        config = self.GAME_CONFIGS[game_name]
        
        checkpoints = np.linspace(1000, max_simulations, check_points, dtype=int)
        results = []
        
        total_spent = 0
        total_won = 0
        
        sim_count = 0
        checkpoint_idx = 0
        
        while sim_count < max_simulations:
            drawn_main, drawn_bonus = self.simulate_draw(game_name)
            ticket_main = set(random.sample(range(1, config['main_pool'] + 1), config['main_pick']))
            ticket_bonus = random.randint(1, config['bonus_pool']) if config['bonus_pool'] > 0 else 0
            
            main_matches, bonus_match = self.check_ticket(
                game_name, ticket_main, ticket_bonus, drawn_main, drawn_bonus
            )
            
            total_spent += config['ticket_cost']
            total_won += self.get_prize(game_name, main_matches, bonus_match)
            sim_count += 1
            
            if checkpoint_idx < len(checkpoints) and sim_count >= checkpoints[checkpoint_idx]:
                roi = (total_won - total_spent) / total_spent * 100
                results.append({
                    'simulations': sim_count,
                    'total_spent': total_spent,
                    'total_won': total_won,
                    'roi_pct': round(roi, 4)
                })
                checkpoint_idx += 1
        
        return pd.DataFrame(results)
