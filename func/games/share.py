class GameStatus:
    def __init__(self):
        self.groups = {}

    def set_in_game(self, chat_id: int, game: str, msg_id: int = 1):
        self.groups[chat_id] = {
            'game': game,
            'msg_id': msg_id
        }

    def game_over(self, chat_id: int):
        del self.groups[chat_id]


game_status = GameStatus()
