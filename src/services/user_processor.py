"""
Module for fetching, processing, and saving chess user data from an online source.

This module defines a UserProcessor class that orchestrates the entire data workflow:
1. Fetch user data via API
2. Process the user stats
3. Save processed data to database
"""

import logging
from typing import Optional
import pandas as pd
import os
import psycopg2

from src.api.api import collect_user_data
from src.services.data_io import save_processed_user_data
import src.services.post_process as post_process

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("database_url")

class UserProcessor:
    """
    Orchestrates the fetching, processing, and saving of chess user data.

    Attributes:
        username (str): The username of the chess player.
        raw_data (Optional[dict]): Raw user data from the API.
        df_processed (Optional[DataFrame]): Post-processed user data.
    """

    def __init__(self, username: str) -> None:
        """
        Initialize the UserProcessor with the target username.

        Args:
            username (str): Player username to fetch user data for.
        """
        self.username = username
        self.raw_data: Optional[dict] = None
        self.df_processed: Optional[pd.DataFrame] = None

    def fetch_user_data(self) -> None:
        """
        Fetch raw user data from the Lichess API.
        """
        logger.info("Fetching user data for '%s'", self.username)
        self.raw_data = collect_user_data(self.username)
        if self.raw_data:
            logger.info("Successfully fetched user data for '%s'", self.username)
        else:
            logger.warning("No user data found for '%s'", self.username)

    def process_user_data(self) -> None:
        """
        Process the raw user data into a structured DataFrame.
        """
        if self.raw_data is None:
            logger.warning("No raw data to process for '%s'", self.username)
            return
        self.df_processed = post_process.process_user_data(self.raw_data)
        logger.info("Processed user data for '%s'", self.username)

    def save_user_data(self) -> None:
        """
        Save the processed user data to the database.
        """
        if self.df_processed is None:
            logger.warning("No processed data to save for '%s'", self.username)
            return
        save_processed_user_data(self.df_processed)
        logger.info("Saved processed user data for '%s' to database", self.username)

        # Save the data to CSV
        folder = "data/processed"
        filepath = os.path.join(folder, "IgorSReis_user_data.csv")
        self.df_processed.to_csv(filepath, index=False)

    def get_dataframe(self) -> Optional[pd.DataFrame]:
        """
        Get the final processed user DataFrame.

        Returns:
            Optional[DataFrame]: Processed DataFrame or None if not available.
        """
        return self.df_processed

    def get_user_data(self) -> pd.Series:
        """
        Retrieve the row of user data with the highest ID for the current username
        from the database.

        Returns:
            pd.Series: A row from the database representing the latest user data.
        """
        username = self.username

        query = """
            SELECT * FROM user_processed_data
            WHERE username = %s
            ORDER BY id DESC
            LIMIT 1;
        """

        try:
            with psycopg2.connect(DATABASE_URL) as conn:
                df = pd.read_sql(query, conn, params=(username,)) # TODO Change to SQLAlchemy
        except Exception as e:
            raise RuntimeError(f"Database error: {e}")

        if df.empty:
            raise ValueError(f"No data found for username: {username}")

        return df.iloc[0].to_dict()

    def run_all(self) -> None:
        """
        Run the full user data pipeline: fetch, process, and save.
        """
        self.fetch_user_data()
        self.process_user_data()
        self.save_user_data()
        self.get_user_data()
