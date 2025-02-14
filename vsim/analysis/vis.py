from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import plotly.express as px
import pandas as pd

loc_style_map = {
    "WS": {
        "color": "blue",
        "marker": "p"
    },
    "YARD": {
        "color": "green",
        "marker": "|"
    },
    "RAIL": {
        "color": "brown",
        "marker": "_"
    },
    "QC": {
        "color": "orange",
        "marker": "2"
    }
}


def visualize_terminal_map(location_coords: list[dict], vehicle_coords: list[dict], position_tracking_df: Optional[pd.DataFrame] = None, show_routes_for: Optional[list[str]] = None, save_path: Optional[str] = None):
    # Plot locations and vehicles
    fig = plt.figure(figsize=(20, 15))

    for loc in location_coords:
        name = loc['location_name']
        loc_type = loc["location_type"]
        x = loc['x']
        y = loc['y']
        plt.scatter(x, y, label=loc_type, color=loc_style_map[loc_type]['color'], marker=loc_style_map[loc_type]['marker'], s=1000, alpha=0.7)
        # plt.text(x, y, name, fontsize=8, rotation=90)

    # Plot vehicles at their initial locations
    for vehicle_loc in vehicle_coords:
        name, x, y = vehicle_loc["id"], vehicle_loc["x"], vehicle_loc["y"]
        plt.scatter(x, y, color="red", marker="s", s=100, edgecolors='black', label=f"Vehicle")
        # plt.text(x, y - 2000, name, fontsize=8, color="red")

    # Customize the grid
    plt.title("Container Terminal Locations and Vehicles", fontsize=20, pad=5, y=1.02)
    plt.xlabel("X-Coordinate (mm)", fontsize=16)
    plt.ylabel("Y-Coordinate (mm)", fontsize=16)
    plt.tick_params(axis='both', which='major', labelsize=16)
    plt.grid(True)
    # Extract unique labels and handles
    handles, labels = plt.gca().get_legend_handles_labels()
    unique_labels = dict(zip(labels, handles))

    # Add the legend with unique labels
    plt.legend(unique_labels.values(), unique_labels.keys(), loc="upper right", bbox_to_anchor=(1.1, 1), labelspacing=3.0, borderpad=1.5, fontsize=12)

    if show_routes_for:
        vehicle_routes = position_tracking_df[position_tracking_df['vehicle_id'].isin(show_routes_for)].to_dict("records")
        for route in vehicle_routes:
            plt.plot(route['x'], route['y'], linestyle='--')
    """
    # Annotate routes with their order
    for i in range(1, len(route["x"])):
        x_prev, y_prev = route["x"][i - 1], route["y"][i - 1]
        x_curr, y_curr = route["x"][i], route["y"][i]
        plt.text((x_prev + x_curr) / 2, (y_prev + y_curr) / 2, i + 1)
    """

    plt.tight_layout()
    plt.show()

    if save_path:
        fig.savefig(save_path, bbox_inches='tight')


def create_gantt_chart(sequential_df: pd.DataFrame, start: str, end: str, y: str, **kwargs):
    # Create the Gantt chart
    fig = px.timeline(sequential_df, x_start=start, x_end=end, y=y, color=kwargs.get('color', None), text=kwargs.get('text', None))

    # Add labels on the bars
    fig.update_traces(textposition='inside', insidetextanchor='middle', textfont=dict(size=kwargs.get("fontsize", 12)))

    # Customize layout
    fig.update_layout(
        title=kwargs.get("title", "Gantt Chart"),
        xaxis_title="Time",
        yaxis_title=kwargs.get("y_label", None),
        showlegend=True,
        height=800
    )

    fig.show()

    if save_path := kwargs.get("save_path", None):
        fig.write_image(save_path)


def draw_boxplot(df: pd.DataFrame, metric: str, title: str | None = None, separator: str | None = None, labels: list[str] | None = None, fig=None, ax=None, **kwargs):
    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=(12, 9), sharex=True)

    if separator is not None:
        x = [df[df[separator] == label][metric].values for label in labels]
        sequence_lengths = [len(item) for item in x]
        # Note: if we have sequence of 1D arrays with different lengths (e,g, shape of x: (2,)), a boxplot is draw for each array; however, if x becomes a 2D array, meaning that
        # all arrays in the sequence have the same shape (e.g. shape of x: (2, 128)), then a boxplot is drawn for each column
        # https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.boxplot.html
        if min(sequence_lengths) == max(sequence_lengths):
            x = np.array(x).transpose()
    else:
        x = df[metric].values

    boxplot = ax.boxplot(x, patch_artist=True, notch=False, label=labels, tick_labels=labels)

    box_colors = [f"C{c_idx}" for c_idx in range(len(labels))]
    for label_idx, (patch, color) in enumerate(zip(boxplot['boxes'], box_colors)):
        patch.set_alpha(0.5)
        patch.set_facecolor(color)
        patch.set_label(labels[label_idx])

    ax.set_xlabel(kwargs.get('x_label_hr', ''), fontsize=kwargs.get('x_label_fs', 12))
    ax.set_ylabel(kwargs.get('y_label_hr', metric), fontsize=kwargs.get('y_label_fs', 12))
    ax.set_title(title)
    ax.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=0.8)

    if not labels:
        ax.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)

    ax.set_xticklabels(labels, rotation=45)

    if fig:
        fig = adjust_figure(fig, labels)

    return fig, ax


def adjust_figure(fig, legends: list[str], loc: str = 'lower center', space_per_legend: float = 0.05, n_cols: int = 1, bbox_to_anchor: tuple | None = None):
    adjustments = {
        'lower': {'bottom': len(legends) * space_per_legend},
        'upper': {'top': 1 - len(legends) * space_per_legend},
    }
    fig.legend(legends, loc=loc, fancybox=True, shadow=True, ncols=n_cols, bbox_to_anchor=bbox_to_anchor)
    fig.tight_layout()
    fig.subplots_adjust(**adjustments[loc.split()[0]])

    return fig
