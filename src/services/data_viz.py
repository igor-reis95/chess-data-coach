"""
This module provides utility functions to generate base64-encoded visualizations 
from chess match data.

Functions:
- winrate_bar_graph: Generates a stacked bar chart of win/draw/loss percentages by color.
- plot_game_status_distribution: Generates a donut chart showing game outcome distributions.

These functions are designed for integration in data pipelines or web apps where
image output needs to be embedded or transmitted via text (e.g., HTML or JSON).
"""

import io
import base64
import logging
from typing import Dict
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt # pylint: disable=wrong-import-position

# Create logger
logger = logging.getLogger(__name__)

def winrate_bar_graph(data: Dict[str, Dict[str, float]]) -> str:
    """
    Generate a base64-encoded stacked bar chart for win/draw/loss percentages by color.

    Args:
        data (Dict[str, Dict[str, float]]): Nested dictionary with win, draw, and loss
                                            percentages for each color ("White", "Black", "Both").

    Returns:
        str: Base64-encoded PNG image of the generated chart.
    """
    logger.debug("Generating winrate bar graph for data: %s", data)

    labels = list(data.keys())
    wins = [data[color]['win'] for color in labels]
    draws = [data[color]['draw'] for color in labels]
    losses = [data[color]['loss'] for color in labels]

    x = np.arange(len(labels))
    bar_width = 0.5

    _, ax = plt.subplots()

    ax.bar(x, wins, bar_width, label='win', color='#92b76f')
    ax.bar(x, draws, bar_width, bottom=wins, label='draw', color='#d59c4d')
    ax.bar(
        x,
        losses,
        bar_width,
        bottom=[i + j for i, j in zip(wins, draws)],
        label='loss',
        color='#db6f72'
    )

    ax.set_ylabel('Percentage')
    ax.set_title('Win Rates by Color')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 100)
    ax.legend()

    for idx, (w, d, l) in enumerate(zip(wins, draws, losses)):
        ax.text(idx, w / 2, f'{w:.0f}%', ha='center', va='center', color='white')
        ax.text(idx, w + d / 2, f'{d:.0f}%', ha='center', va='center', color='black')
        ax.text(idx, w + d + l / 2, f'{l:.0f}%', ha='center', va='center', color='white')

    plt.tight_layout()

    img_stream = io.BytesIO()
    plt.savefig(img_stream, format='png')
    img_stream.seek(0)
    img_base64 = base64.b64encode(img_stream.read()).decode('utf-8')
    plt.close()

    logger.debug("Winrate bar graph successfully generated.")
    return img_base64


def plot_game_status_distribution(df: pd.DataFrame) -> str:
    """
    Generate a base64-encoded donut chart for game status distribution.

    Args:
        df (pd.DataFrame): DataFrame containing a 'status' column.

    Returns:
        str: Base64-encoded PNG image of the chart.
    """
    logger.debug("Generating game status distribution chart.")

    # Count and compute relative frequency
    status_counts = df['status'].value_counts()
    total = status_counts.sum()
    status_percent = status_counts / total

    # Group small categories into 'other'
    threshold = 0.10
    major_statuses = status_percent[status_percent >= threshold]
    other_count = status_counts[status_percent < threshold].sum() / 100

    # Final data
    final_counts = major_statuses.copy()
    if other_count > 0:
        final_counts['other'] = other_count

    # Define color mapping
    color_map = {
        'resign': '#93b674',
        'mate': '#da6f73',
        'draw': '#d49b54',
        'outoftime': '#3288d1',
        'other': '#6c757d'
    }

    # Assign colors based on final labels
    custom_colors = [color_map.get(status, '#6c757d') for status in final_counts.index]

    # Plot
    fig, ax = plt.subplots()
    wedges, _, _ = ax.pie(
        final_counts,
        labels=final_counts.index,
        autopct='%1.1f%%',
        startangle=90,
        wedgeprops={'width': 0.4},
        colors=custom_colors
    )

    centre_circle = plt.Circle((0, 0), 0.70, fc='white')
    fig.gca().add_artist(centre_circle)

    ax.axis('equal')
    plt.title("Game Status Distribution")
    ax.legend(
        wedges,
        final_counts.index,
        title="Status",
        loc="center left",
        bbox_to_anchor=(1, 0.5)
    )

    plt.tight_layout()

    img_stream = io.BytesIO()
    plt.savefig(img_stream, format='png')
    img_stream.seek(0)
    img_base64 = base64.b64encode(img_stream.read()).decode('utf-8')
    plt.close()

    logger.debug("Game status distribution chart successfully generated.")
    return img_base64
