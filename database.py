import sqlite3
import os
from typing import Optional, List, Dict, Any
from config import DB_FILE, DATABASE_DIR, LEVEL_CONFIG, DEFAULT_VOLUME, DEFAULT_SNAKE_COLOR, SNAKE_COLORS_AVAILABLE

# Helper to get max levels for bounds checking
MAX_LEVELS_PER_DIFFICULTY = {
    diff: len(levels) for diff, levels in LEVEL_CONFIG.items()
}

class PlayerDatabase:
    def __init__(self, db_file=DB_FILE):
        self.db_file = db_file
        os.makedirs(os.path.dirname(db_file), exist_ok=True)
        self._initialize_db()

    def _execute(self, query: str, params: tuple = (),
                 fetch_one=False, fetch_all=False):
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                if fetch_one:
                    return cursor.fetchone()
                if fetch_all:
                    return cursor.fetchall()
                return cursor
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None

    def _initialize_db(self):
        # Drop existing table for schema change (BE CAREFUL WITH THIS IN PRODUCTION)
        # self._execute("DROP TABLE IF EXISTS players;") 
        # For development, it's often easier to drop and recreate.
        # In production, you'd use ALTER TABLE.

        create_table_query = f"""
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                high_score INTEGER DEFAULT 0,
                difficulty TEXT, 
                highest_level INTEGER DEFAULT 1, -- Highest level reached in last played difficulty
                games_played INTEGER DEFAULT 0,
                last_played TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                unlocked_easy INTEGER DEFAULT 1,    -- Highest level unlocked for Easy
                unlocked_moderate INTEGER DEFAULT 1, -- Highest level unlocked for Moderate
                unlocked_hard INTEGER DEFAULT 1,      -- Highest level unlocked for Hard
                volume REAL DEFAULT {DEFAULT_VOLUME},
                snake_color TEXT DEFAULT '{DEFAULT_SNAKE_COLOR}'
            )
        """
        self._execute(create_table_query)
        self._execute("CREATE INDEX IF NOT EXISTS idx_player_name ON players (name);")
        
        # Add new columns if they don't exist (safer for existing dbs)
        self._add_column_if_not_exists("players", "unlocked_easy", "INTEGER DEFAULT 1")
        self._add_column_if_not_exists("players", "unlocked_moderate", "INTEGER DEFAULT 1")
        self._add_column_if_not_exists("players", "unlocked_hard", "INTEGER DEFAULT 1")
        self._add_column_if_not_exists("players", "volume", f"REAL DEFAULT {DEFAULT_VOLUME}")
        self._add_column_if_not_exists("players", "snake_color", f"TEXT DEFAULT '{DEFAULT_SNAKE_COLOR}'")

    def _add_column_if_not_exists(self, table_name, column_name, column_definition):
        cursor = self._execute(f"PRAGMA table_info({table_name})")
        if cursor:
            columns = [row[1] for row in cursor.fetchall()]
            if column_name not in columns:
                self._execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")
                print(f"Added column '{column_name}' to table '{table_name}'.")

    def add_player(self, name: str) -> Optional[int]:
        name = name.strip()
        if not name:
            return None

        # Insert player or ignore if name exists, then select their ID.
        # Default unlocked levels are set by table schema.
        insert_query = "INSERT OR IGNORE INTO players (name) VALUES (?)"
        self._execute(insert_query, (name,))
        
        select_query = "SELECT id FROM players WHERE name = ?"
        result = self._execute(select_query, (name,), fetch_one=True)
        return result[0] if result else None

    def update_player_name(self, player_id: int, new_name: str) -> bool:
        new_name = new_name.strip()
        if not new_name or player_id is None:
            return False

        update_query = "UPDATE players SET name = ? WHERE id = ?"
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(update_query, (new_name, player_id))
                conn.commit()
                return conn.total_changes > 0
        except sqlite3.IntegrityError:
            print(f"Database IntegrityError: Name '{new_name}' might already exist.")
            return False
        except sqlite3.Error as e:
            print(f"Database error in update_player_name: {e}")
            return False

    def update_player_score(self, player_id: int, score: int, difficulty: str, level_reached: int):
        """Updates player's general game stats. Level unlocking is separate."""
        update_query = """
            UPDATE players SET
            games_played = games_played + 1,
            last_played = CURRENT_TIMESTAMP,
            difficulty = ?,
            highest_level = MAX(highest_level, ?), -- highest level reached in this game session
            high_score = MAX(high_score, ?)
            WHERE id = ?
        """
        self._execute(update_query, (difficulty, level_reached, score, player_id))

    def get_unlocked_level(self, player_id: int, difficulty: str) -> int:
        """Gets the highest unlocked level for a specific difficulty."""
        if player_id is None or difficulty not in ["Easy", "Moderate", "Hard"]:
            return 1 # Default to level 1 if invalid input
        
        column_name = f"unlocked_{difficulty.lower()}"
        query = f"SELECT {column_name} FROM players WHERE id = ?"
        result = self._execute(query, (player_id,), fetch_one=True)
        return result[0] if result and result[0] is not None else 1

    def unlock_next_level(self, player_id: int, difficulty: str, completed_level_number: int):
        """Unlocks the next level if the completed level was the highest unlocked so far."""
        if player_id is None or difficulty not in MAX_LEVELS_PER_DIFFICULTY:
            return

        current_unlocked = self.get_unlocked_level(player_id, difficulty)
        next_level_to_unlock = completed_level_number + 1
        max_levels_for_difficulty = MAX_LEVELS_PER_DIFFICULTY[difficulty]

        if completed_level_number == current_unlocked and next_level_to_unlock <= max_levels_for_difficulty:
            column_name = f"unlocked_{difficulty.lower()}"
            update_query = f"UPDATE players SET {column_name} = ? WHERE id = ?"
            self._execute(update_query, (next_level_to_unlock, player_id))
            print(f"Player {player_id} unlocked {difficulty} level {next_level_to_unlock}")

    def get_player_volume(self, player_id: int) -> float:
        """Gets the player's volume setting."""
        if player_id is None:
            return DEFAULT_VOLUME
            
        query = "SELECT volume FROM players WHERE id = ?"
        result = self._execute(query, (player_id,), fetch_one=True)
        return result[0] if result and result[0] is not None else DEFAULT_VOLUME
        
    def update_player_volume(self, player_id: int, volume: float) -> bool:
        """Updates the player's volume setting."""
        if player_id is None:
            return False
            
        # Ensure volume is between 0.0 and 1.0
        volume = max(0.0, min(1.0, volume))
        
        update_query = "UPDATE players SET volume = ? WHERE id = ?"
        self._execute(update_query, (volume, player_id))
        return True
        
    def update_player_difficulty(self, player_id: int, difficulty: str) -> bool:
        """Updates the player's preferred difficulty setting."""
        if player_id is None or difficulty not in ["Easy", "Moderate", "Hard"]:
            return False
            
        update_query = "UPDATE players SET difficulty = ? WHERE id = ?"
        self._execute(update_query, (difficulty, player_id))
        return True

    def update_player_snake_color(self, player_id: int, color: str) -> bool:
        """Updates the player's preferred snake color."""
        if player_id is None or color not in SNAKE_COLORS_AVAILABLE:
            print(f"Invalid snake color {color} or player_id {player_id} for update.")
            return False
        
        update_query = "UPDATE players SET snake_color = ? WHERE id = ?"
        self._execute(update_query, (color, player_id))
        return True

    def get_player_snake_color(self, player_id: int) -> str:
        """Gets the player's snake color setting."""
        if player_id is None:
            return DEFAULT_SNAKE_COLOR
            
        query = "SELECT snake_color FROM players WHERE id = ?"
        result = self._execute(query, (player_id,), fetch_one=True)
        return result[0] if result and result[0] else DEFAULT_SNAKE_COLOR

    def get_top_players(self, limit: int = 10) -> List[Dict[str, Any]]:
        select_query = """
            SELECT name, high_score, difficulty, highest_level
            FROM players
            ORDER BY high_score DESC
            LIMIT ?
        """
        cursor = self._execute(select_query, (limit,), fetch_all=True)
        if cursor:
            top_players = [
                {"name": row[0], "high_score": row[1], "difficulty": row[2], "highest_level": row[3]}
                for row in cursor
            ]
            return top_players
        return []

    def get_player_data(self, player_id: int) -> Optional[Dict[str, Any]]:
        if player_id is None:
            return None
        query = "SELECT name, high_score, difficulty, highest_level, unlocked_easy, unlocked_moderate, unlocked_hard, volume, snake_color FROM players WHERE id = ?"
        row = self._execute(query, (player_id,), fetch_one=True)
        if row:
            return {
                "name": row[0], "high_score": row[1], "difficulty": row[2],
                "highest_level": row[3],
                "unlocked_levels": {
                    "Easy": row[4],
                    "Moderate": row[5],
                    "Hard": row[6]
                },
                "volume": row[7],
                "snake_color": row[8] if row[8] else DEFAULT_SNAKE_COLOR
            }
        return None