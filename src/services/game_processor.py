"""
Module for fetching, saving, flattening, and processing chess game data from an online source.

This module defines a GameProcessor class that orchestrates the entire data workflow:
1. Fetch raw games via API
2. Save raw JSON data
3. Flatten nested JSON into tabular format
4. Post-process data for analysis
5. Save processed data as CSV
"""

import logging
from typing import Optional
from pandas import DataFrame
from src.api.api import get_games
from src.services.flatten import flatten_game_data
from src.services.post_process import post_process
from src.services.chess_engine import run_evaluation_pipeline

logger = logging.getLogger(__name__)

class GameProcessor:
    """
    Orchestrates the fetching, processing, and saving of chess game data for a player.

    Attributes:
        username (str): Player username to fetch games for.
        max_games (int): Maximum number of games to fetch.
        perf_type (str): Performance type filter (e.g., 'rapid', 'blitz').
        games (Optional[list]): Raw game data fetched from API.
        df_flat (Optional[DataFrame]): Flattened game data as DataFrame.
        df_processed (Optional[DataFrame]): Post-processed game DataFrame.
    """

    def __init__(self, username: str, max_games: int, perf_type: str, platform: str) -> None:
        """
        Initialize the GameProcessor with user parameters.

        Args:
            username (str): Player username.
            max_games (int): Max games to fetch.
            perf_type (str): Performance type.
        """
        self.username = username
        self.max_games = max_games
        self.perf_type = perf_type
        self.platform = platform
        self.games: Optional[list] = None
        self.df_flat: Optional[DataFrame] = None
        self.df_processed: Optional[DataFrame] = None

    def fetch_games(self) -> None:
        """
        Fetch games from API for the player with given filters.

        Raises:
            Exception: Propagates exceptions from get_games.
        """
        logger.info("Fetching up to %d games for user '%s', perf_type='%s'",
                    self.max_games, self.username, self.perf_type)
        self.games = get_games(self.username, self.max_games, self.perf_type, self.platform)
        logger.info("Fetched %d games for user '%s'", len(self.games), self.username)

    def flatten_games(self) -> None:
        """
        Flatten raw game data into a DataFrame.
        """
        if not self.games:
            logger.warning("No games to flatten for user '%s'", self.username)
            return
        self.df_flat = flatten_game_data(self.games)
        logger.info("Flattened games into DataFrame with %d rows for user '%s'",
                    len(self.df_flat), self.username)

    def post_process_games(self) -> None:
        """
        Post-process the flattened DataFrame and save it as CSV and to the postgres database.
        """
        if self.df_flat is None:
            logger.warning("No flattened data to process for user '%s'", self.username)
            return
        self.df_processed = post_process(self.df_flat, self.username)
        logger.info("Post-processed and saved CSV for user '%s'", self.username)

    def get_dataframe(self) -> Optional[DataFrame]:
        """
        Get the final processed DataFrame.

        Returns:
            Optional[DataFrame]: The post-processed DataFrame or None if not available.
        """
        return self.df_processed

    def run_all(self) -> None:
        """
        Run the full pipeline: fetch, save raw, flatten, post-process, and save processed data.
        """
        self.fetch_games()
        self.flatten_games()
        self.df_flat = run_evaluation_pipeline(self.df_flat)
        self.post_process_games()
