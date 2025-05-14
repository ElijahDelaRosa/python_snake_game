from typing import Dict, List, Any
from config import LEVEL_CONFIG, DEFAULT_DIFFICULTY

class LevelManager:
    def __init__(self, levels_data: Dict[str, List[Dict]] = LEVEL_CONFIG):
        self.levels_data = levels_data
        self.difficulty = DEFAULT_DIFFICULTY
        self.current_level_index = 0
        # self.completed_levels: Dict[str, List[bool]] = {
        #     diff: [False] * len(levels) for diff, levels in levels_data.items()
        # }

    def set_difficulty(self, difficulty: str):
        if difficulty in self.levels_data:
            self.difficulty = difficulty
            self.current_level_index = 0 # Reset level progress on difficulty change
        else:
            print(f"Warning: Difficulty '{difficulty}' not found in LEVEL_CONFIG. Using default.")
            self.difficulty = DEFAULT_DIFFICULTY
            self.current_level_index = 0


    def get_current_level_config(self) -> Dict:
        if self.difficulty not in self.levels_data:
             # Fallback to default difficulty if current is somehow invalid
            print(f"Error: Current difficulty '{self.difficulty}' not in levels_data. Falling back.")
            self.difficulty = DEFAULT_DIFFICULTY # Or handle error more gracefully

        difficulty_levels = self.levels_data[self.difficulty]
        if 0 <= self.current_level_index < len(difficulty_levels):
            return difficulty_levels[self.current_level_index]
        else:
            # This case should ideally not be reached if game completion is handled
            print(f"Warning: current_level_index {self.current_level_index} out of bounds for difficulty {self.difficulty}")
            # Return the last valid level config or a default
            return difficulty_levels[-1] if difficulty_levels else {}


    def get_level_number(self) -> int:
        return self.get_current_level_config().get("level", 1)

    def get_target_score(self) -> int:
        return self.get_current_level_config().get("target_score", 10)

    def get_num_apples(self) -> int:
        return self.get_current_level_config().get("num_apples", 1)

    def get_num_obstacles(self) -> int:
        return self.get_current_level_config().get("num_obstacles", 0)
    
    def get_apple_spawn_delay(self) -> int:
        return self.get_current_level_config().get("apple_spawn_delay", 500)

    def get_levels_for_difficulty(self, difficulty: str) -> List[Dict]:
        """Returns the list of level configurations for a given difficulty."""
        return self.levels_data.get(difficulty, [])

    def is_level_complete(self, score: int) -> bool:
        return score >= self.get_target_score()

    # def mark_level_complete(self):
    #     if self.difficulty in self.completed_levels and \
    #        0 <= self.current_level_index < len(self.completed_levels[self.difficulty]):
    #         self.completed_levels[self.difficulty][self.current_level_index] = True

    def advance_level(self) -> bool:
        difficulty_levels = self.levels_data.get(self.difficulty, [])
        if self.current_level_index < len(difficulty_levels) - 1:
            self.current_level_index += 1
            return True
        return False # Already at the last level for this difficulty

    def reset_progress(self):
        self.current_level_index = 0
        # for diff in self.completed_levels:
        #     self.completed_levels[diff] = [False] * len(self.levels_data.get(diff, []))

    def is_game_complete(self) -> bool: # Game complete for current difficulty
        difficulty_levels = self.levels_data.get(self.difficulty, [])
        return self.current_level_index >= len(difficulty_levels) -1 # Check if on the last level index