from typing import Dict, Optional
from collections import defaultdict


class BettingState:
    """Manages betting state for active games"""
    def __init__(self):
        # chat_id -> {user_id: {'bet_type': 'player'|'banker'|'tie', 'amount': int}}
        self.active_bets: Dict[int, Dict[int, Dict[str, any]]] = {}
        # chat_id -> game result data
        self.game_data: Dict[int, Dict[str, any]] = {}

    def start_betting(self, chat_id: int, msg_id: int):
        """Start a new betting phase for a chat"""
        self.active_bets[chat_id] = {}
        self.game_data[chat_id] = {'msg_id': msg_id}

    def place_bet(self, chat_id: int, user_id: int, bet_type: str, amount: int) -> bool:
        """Place a bet. Returns True if successful, False if betting is closed"""
        if chat_id not in self.active_bets:
            return False
        
        # Update or add bet
        if user_id in self.active_bets[chat_id]:
            # User already has a bet, update it
            self.active_bets[chat_id][user_id]['bet_type'] = bet_type
            self.active_bets[chat_id][user_id]['amount'] = amount
        else:
            # New bet
            self.active_bets[chat_id][user_id] = {
                'bet_type': bet_type,
                'amount': amount
            }
        return True

    def get_bets(self, chat_id: int) -> Dict[int, Dict[str, any]]:
        """Get all bets for a chat"""
        return self.active_bets.get(chat_id, {})

    def close_betting(self, chat_id: int):
        """Close betting and store game data"""
        if chat_id in self.active_bets:
            # Keep bets for processing results
            pass

    def set_game_result(self, chat_id: int, result: str, player_value: int, banker_value: int):
        """Store game result"""
        if chat_id not in self.game_data:
            self.game_data[chat_id] = {}
        self.game_data[chat_id].update({
            'result': result,  # 'player', 'banker', 'tie'
            'player_value': player_value,
            'banker_value': banker_value
        })

    def get_game_result(self, chat_id: int) -> Optional[Dict[str, any]]:
        """Get game result data"""
        return self.game_data.get(chat_id)

    def clear_game(self, chat_id: int):
        """Clear all data for a finished game"""
        if chat_id in self.active_bets:
            del self.active_bets[chat_id]
        if chat_id in self.game_data:
            del self.game_data[chat_id]

    def is_betting_open(self, chat_id: int) -> bool:
        """Check if betting is still open"""
        return chat_id in self.active_bets


betting_state = BettingState()
