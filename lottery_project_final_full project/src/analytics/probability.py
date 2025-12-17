# src/analytics/probability.py
"""
Probability Calculations Module for NY Lottery Games.

Calculates theoretical probabilities and expected values.
These are mathematical calculations based on game rules.

DISCLAIMER: Understanding probability helps set realistic expectations.
The house always has an edge in lottery games.
"""

import math
from typing import Dict, Tuple
from dataclasses import dataclass

@dataclass
class GameConfig:
    """Configuration for a lottery game."""
    name: str
    main_pool: int      # Numbers to choose from (e.g., 1-70)
    main_pick: int      # Numbers to pick (e.g., 5)
    bonus_pool: int     # Bonus ball pool (e.g., 1-25)
    bonus_pick: int     # Bonus balls to pick (usually 1)
    jackpot_typical: float  # Typical jackpot in millions
    ticket_cost: float  # Cost per ticket

class ProbabilityCalculator:
    """Calculate lottery probabilities and expected values."""
    
    # Game configurations
    GAMES = {
        'mega_millions': GameConfig(
            name='Mega Millions',
            main_pool=70, main_pick=5,
            bonus_pool=25, bonus_pick=1,
            jackpot_typical=300.0,
            ticket_cost=2.0
        ),
        'powerball': GameConfig(
            name='Powerball',
            main_pool=69, main_pick=5,
            bonus_pool=26, bonus_pick=1,
            jackpot_typical=300.0,
            ticket_cost=2.0
        ),
        'take5': GameConfig(
            name='Take 5',
            main_pool=39, main_pick=5,
            bonus_pool=0, bonus_pick=0,
            jackpot_typical=0.5,  # Rolling jackpot
            ticket_cost=1.0
        ),
        'cash4life': GameConfig(
            name='Cash4Life',
            main_pool=60, main_pick=5,
            bonus_pool=4, bonus_pick=1,
            jackpot_typical=7.0,  # $1000/day for life ≈ $7M present value
            ticket_cost=2.0
        ),
        'ny_lotto': GameConfig(
            name='NY Lotto',
            main_pool=59, main_pick=6,
            bonus_pool=0, bonus_pick=0,
            jackpot_typical=2.0,
            ticket_cost=1.0
        ),
        'numbers': GameConfig(
            name='Numbers (Pick 3)',
            main_pool=10, main_pick=3,
            bonus_pool=0, bonus_pick=0,
            jackpot_typical=0.0005,  # $500 for straight
            ticket_cost=0.5
        ),
        'win4': GameConfig(
            name='Win 4 (Pick 4)',
            main_pool=10, main_pick=4,
            bonus_pool=0, bonus_pick=0,
            jackpot_typical=0.005,  # $5000 for straight
            ticket_cost=0.5
        )
    }
    
    @staticmethod
    def combinations(n: int, k: int) -> int:
        """Calculate C(n, k) = n! / (k! * (n-k)!)"""
        if k > n or k < 0:
            return 0
        return math.comb(n, k)
    
    def get_jackpot_odds(self, game_name: str) -> Tuple[int, str]:
        """
        Calculate odds of winning the jackpot.
        
        Args:
            game_name: Name of the game
            
        Returns:
            Tuple of (odds, formatted string)
        """
        if game_name not in self.GAMES:
            raise ValueError(f"Unknown game: {game_name}")
        
        config = self.GAMES[game_name]
        
        # Main number combinations
        main_combos = self.combinations(config.main_pool, config.main_pick)
        
        # Bonus number combinations (if applicable)
        if config.bonus_pool > 0:
            bonus_combos = config.bonus_pool
            total_odds = main_combos * bonus_combos
        else:
            total_odds = main_combos
        
        formatted = f"1 in {total_odds:,}"
        return total_odds, formatted
    
    def get_all_prize_odds(self, game_name: str) -> Dict[str, Dict]:
        """
        Get odds for all prize tiers (simplified for major games).
        
        Returns:
            Dict with prize tier info
        """
        if game_name == 'mega_millions':
            return self._mega_millions_odds()
        elif game_name == 'powerball':
            return self._powerball_odds()
        elif game_name == 'take5':
            return self._take5_odds()
        elif game_name in ['numbers', 'win4']:
            return self._daily_game_odds(game_name)
        else:
            jackpot_odds, _ = self.get_jackpot_odds(game_name)
            return {'jackpot': {'odds': jackpot_odds, 'prize': 'Jackpot'}}
    
    def _mega_millions_odds(self) -> Dict:
        """Mega Millions prize tiers."""
        return {
            '5+1': {'odds': 302575350, 'prize': 'Jackpot', 'match': '5 + Mega Ball'},
            '5+0': {'odds': 12607306, 'prize': '$1,000,000', 'match': '5 only'},
            '4+1': {'odds': 931001, 'prize': '$10,000', 'match': '4 + Mega Ball'},
            '4+0': {'odds': 38792, 'prize': '$500', 'match': '4 only'},
            '3+1': {'odds': 14547, 'prize': '$200', 'match': '3 + Mega Ball'},
            '3+0': {'odds': 606, 'prize': '$10', 'match': '3 only'},
            '2+1': {'odds': 693, 'prize': '$10', 'match': '2 + Mega Ball'},
            '1+1': {'odds': 89, 'prize': '$4', 'match': '1 + Mega Ball'},
            '0+1': {'odds': 37, 'prize': '$2', 'match': 'Mega Ball only'},
        }
    
    def _powerball_odds(self) -> Dict:
        """Powerball prize tiers."""
        return {
            '5+1': {'odds': 292201338, 'prize': 'Jackpot', 'match': '5 + Powerball'},
            '5+0': {'odds': 11688054, 'prize': '$1,000,000', 'match': '5 only'},
            '4+1': {'odds': 913129, 'prize': '$50,000', 'match': '4 + Powerball'},
            '4+0': {'odds': 36525, 'prize': '$100', 'match': '4 only'},
            '3+1': {'odds': 14494, 'prize': '$100', 'match': '3 + Powerball'},
            '3+0': {'odds': 580, 'prize': '$7', 'match': '3 only'},
            '2+1': {'odds': 701, 'prize': '$7', 'match': '2 + Powerball'},
            '1+1': {'odds': 92, 'prize': '$4', 'match': '1 + Powerball'},
            '0+1': {'odds': 38, 'prize': '$4', 'match': 'Powerball only'},
        }
    
    def _take5_odds(self) -> Dict:
        """Take 5 prize tiers."""
        return {
            '5': {'odds': 575757, 'prize': 'Jackpot', 'match': '5 of 5'},
            '4': {'odds': 3387, 'prize': '~$500', 'match': '4 of 5'},
            '3': {'odds': 102, 'prize': '~$25', 'match': '3 of 5'},
            '2': {'odds': 10, 'prize': 'Free Play', 'match': '2 of 5'},
        }
    
    def _daily_game_odds(self, game_name: str) -> Dict:
        """Daily game (Numbers/Win4) odds."""
        digits = 3 if game_name == 'numbers' else 4
        straight_odds = 10 ** digits
        
        return {
            'straight': {'odds': straight_odds, 'prize': f'${500 if digits == 3 else 5000}', 'match': 'Exact order'},
            'box_all_diff': {'odds': straight_odds // math.factorial(digits), 'prize': f'${80 if digits == 3 else 200}', 'match': 'Any order (all different)'},
            'front_pair': {'odds': 100, 'prize': '$50', 'match': 'First 2 digits'},
            'back_pair': {'odds': 100, 'prize': '$50', 'match': 'Last 2 digits'},
        }
    
    def calculate_expected_value(self, game_name: str, 
                                   jackpot_millions: float = None) -> Dict:
        """
        Calculate expected value per ticket.
        
        Args:
            game_name: Name of the game
            jackpot_millions: Current jackpot in millions (or use typical)
            
        Returns:
            Dict with EV analysis
        """
        if game_name not in self.GAMES:
            raise ValueError(f"Unknown game: {game_name}")
        
        config = self.GAMES[game_name]
        jackpot = jackpot_millions if jackpot_millions else config.jackpot_typical
        
        # Get prize odds
        prizes = self.get_all_prize_odds(game_name)
        
        # Calculate EV (simplified - doesn't account for split jackpots)
        ev = 0
        for tier, info in prizes.items():
            if 'Jackpot' in str(info['prize']):
                prize_value = jackpot * 1_000_000
            else:
                # Parse prize string
                prize_str = str(info['prize']).replace('$', '').replace(',', '').replace('~', '')
                try:
                    prize_value = float(prize_str)
                except ValueError:
                    prize_value = 0
            
            ev += prize_value / info['odds']
        
        return {
            'ticket_cost': config.ticket_cost,
            'expected_value': round(ev, 4),
            'expected_loss': round(config.ticket_cost - ev, 4),
            'return_percentage': round((ev / config.ticket_cost) * 100, 2),
            'jackpot_used': jackpot,
            'note': 'EV calculation is simplified. Actual EV is lower due to taxes and jackpot splits.'
        }
    
    def compare_games(self) -> Dict:
        """
        Compare all games by their odds and expected values.
        
        Returns:
            Dict with comparison data
        """
        comparison = []
        
        for game_name, config in self.GAMES.items():
            odds, odds_str = self.get_jackpot_odds(game_name)
            ev = self.calculate_expected_value(game_name)
            
            comparison.append({
                'game': config.name,
                'jackpot_odds': odds,
                'jackpot_odds_str': odds_str,
                'ticket_cost': config.ticket_cost,
                'expected_value': ev['expected_value'],
                'return_pct': ev['return_percentage']
            })
        
        return sorted(comparison, key=lambda x: x['jackpot_odds'])
