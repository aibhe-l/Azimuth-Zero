import os
import io
import base64
import math
import pandas as pd
import numpy as np
import rasterio
import matplotlib
matplotlib.use('Agg')  # Headless backend so Matplotlib works inside Dash without needing to display a separate window
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
from rasterio.windows import from_bounds, Window
from rasterio.transform import rowcol, xy
from skimage.graph import MCP_Geometric

GOLD_HEX = "#cda961"
BLUE_HEX = "#004d89"


def mars_distance(lat1, lon1, lat2, lon2): # Convert from Martian coordinates to km
    
    radius_km = 3389.5
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    return 2 * radius_km * math.asin(min(1.0, math.sqrt(a)))


def km_to_degrees(km, lat): # Convert search radius from km to degrees
    
    radius_km = 3389.5
    lat_radius = math.degrees(km / radius_km)
    cos_lat = max(0.01, abs(math.cos(math.radians(lat))))
    lon_radius = lat_radius / cos_lat
    return lat_radius, lon_radius


def _get_target_name_column(df): # Return the first column name that is likely to contain target names, or the first non-coordinate column if none of the expected names are found.
    for candidate in ["Target", "Name", "Target_Name", "Site", "Feature", "Label"]:
        if candidate in df.columns:
            return candidate
    for col in df.columns:
        if col not in ("Latitude", "Longitude", "Distance_km"):
            return col
    return df.columns[0]


def _fig_to_svg_uri_and_save(fig, filepath): # Save figures to plots .svg and return a Base64 SVG string for Dash.
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    fig.savefig(filepath, format="svg", bbox_inches="tight", dpi=100)

    buf = io.BytesIO()
    fig.savefig(buf, format="svg", bbox_inches="tight", dpi=100)
    plt.close(fig)
    encoded = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/svg+xml;base64,{encoded}"


def get_closest_targets(lat, lon, radius): # Return distance-sorted DataFrame of targets within radius (km).
   
    df_targets = pd.read_csv("curiosity_science_targets_clean.csv")
    df_targets["Distance_km"] = [
        mars_distance(lat, lon, row_lat, row_lon)
        for row_lon, row_lat in df_targets[["Longitude", "Latitude"]].values
    ]
    df_closest = (
        df_targets[df_targets["Distance_km"] <= radius]
        .sort_values(by="Distance_km")
        .copy()
        .reset_index(drop=True)
    )
    return df_closest


def search_area(aerial=True, lat=None, lon=None, radius=None): # Generate plots/search_area.svg and return (svg_uri, targets_list).

    df_closest_targets = get_closest_targets(lat, lon, radius)
    name_col = _get_target_name_column(df_closest_targets)

    fig, ax = plt.subplots(figsize=(5.4, 3.9), dpi=100)

    with rasterio.open("gale_topography_small.tif") as src:
        elevation = src.read(1, masked=True)
        bounds = src.bounds

    im = ax.imshow(
        elevation,
        cmap="gray" if aerial else "terrain",
        extent=[bounds.left, bounds.right, bounds.bottom, bounds.top],
        origin="upper",
    )

    if not aerial:
        cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label("Elevation (m)", fontsize=8)
        cbar.ax.tick_params(labelsize=7)

    ax.scatter(
        lon, lat,
        marker="*",
        color=GOLD_HEX,
        edgecolors="black",
        linewidths=0.6,
        s=110,
        label="Astronaut",
        zorder=5
    )
    if not df_closest_targets.empty:
        ax.scatter(
            df_closest_targets["Longitude"],
            df_closest_targets["Latitude"],
            color=GOLD_HEX,
            edgecolors=BLUE_HEX,
            linewidths=0.5,
            s=18,
            label="Targets",
            zorder=4,
        )

    lat_radius, lon_radius = km_to_degrees(radius, lat)
    ax.set_xlim(lon - lon_radius, lon + lon_radius)
    ax.set_ylim(lat - lat_radius, lat + lat_radius)

    search_ellipse = Ellipse(
        (lon, lat),
        width=2 * lon_radius,
        height=2 * lat_radius,
        edgecolor=GOLD_HEX,
        facecolor="none",
        linestyle="--",
        linewidth=1.5,
        label=f"Radius ({radius:.2f} km)",
        zorder=4,
    )
    ax.add_patch(search_ellipse)

    ax.set_xlabel("Longitude", fontsize=8)
    ax.set_ylabel("Latitude", fontsize=8)
    ax.tick_params(labelsize=7)
    ax.set_title("Gale Crater - Search Area", fontsize=9, fontweight="bold")
    ax.legend(loc="upper right", fontsize=7, framealpha=0.85)

    svg_uri = _fig_to_svg_uri_and_save(fig, "plots/search_area.svg")

    targets_list = []
    for idx, row in df_closest_targets.iterrows():
        targets_list.append({
            "index": int(idx),
            "name": str(row[name_col]),
            "distance_km": float(row["Distance_km"]),
        })

    return svg_uri, targets_list


def find_route(selection_index, lat, lon, radius, aerial=True): # Generate plots/route.svg and return (svg_uri, target_name, display_distance_km).

    df_closest_targets = get_closest_targets(lat, lon, radius)
    if selection_index < 0 or selection_index >= len(df_closest_targets):
        raise ValueError("Selection index out of range.")

    name_col = _get_target_name_column(df_closest_targets)
    selected_target = df_closest_targets.iloc[selection_index]
    target_name = str(selected_target[name_col])
    straight_distance_km = float(selected_target["Distance_km"])

    lat_radius, lon_radius = km_to_degrees(radius * 1.5, lat)
    left = lon - lon_radius
    right = lon + lon_radius
    bottom = lat - lat_radius
    top = lat + lat_radius

    with rasterio.open("gale_topography_small.tif") as src:
        if src.crs is None or not src.crs.is_geographic:
            raise ValueError("This code requires a DEM using longitude/latitude.")

        window = from_bounds(left, bottom, right, top, transform=src.transform)
        window = window.intersection(Window(0, 0, src.width, src.height))

        elevation_win = src.read(1, window=window, masked=True)
        transform = src.window_transform(window)

    z = elevation_win.filled(np.nan).astype(float)

    mars_radius_m = 3389500.0
    dx = abs(transform.a) * math.pi / 180.0 * mars_radius_m * math.cos(math.radians(lat))
    dy = abs(transform.e) * math.pi / 180.0 * mars_radius_m

    gradient_y, gradient_x = np.gradient(z, dy, dx)
    slope = np.degrees(np.arctan(np.hypot(gradient_x, gradient_y)))

    cost = 1.0 + 10.0 * np.tan(np.radians(slope)) ** 2
    cost[(slope > 12) | ~np.isfinite(slope)] = np.inf

    start = rowcol(transform, lon, lat)
    end = rowcol(transform, selected_target["Longitude"], selected_target["Latitude"])

    for point in (start, end):
        r, c = point
        if not (0 <= r < z.shape[0] and 0 <= c < z.shape[1]):
            raise ValueError("Start or target is outside the elevation map.")
        if not np.isfinite(cost[r, c]):
            raise ValueError("Start or target is on blocked terrain (>12° slope).")

    dijkstra = MCP_Geometric(cost, fully_connected=True, sampling=(dy, dx))
    distances, _ = dijkstra.find_costs(starts=[start], ends=[end])

    if not np.isfinite(distances[end]):
        raise ValueError("No route found within the permitted terrain.")

    path = np.array(dijkstra.traceback(end))
    route_lon, route_lat = xy(transform, path[:, 0], path[:, 1], offset="center")

    route_lon = [lon, *route_lon, float(selected_target["Longitude"])]
    route_lat = [lat, *route_lat, float(selected_target["Latitude"])]

    path_distance_km = 0.0
    for i in range(len(route_lon) - 1):
        path_distance_km += mars_distance(
            route_lat[i], route_lon[i], route_lat[i + 1], route_lon[i + 1]
        )
    display_distance_km = path_distance_km if path_distance_km > 0 else straight_distance_km

    fig, ax = plt.subplots(figsize=(5.4, 3.9), dpi=100)

    with rasterio.open("gale_topography_small.tif") as src:
        full_elevation = src.read(1, masked=True)
        bounds = src.bounds

    im = ax.imshow(
        full_elevation,
        cmap="gray" if aerial else "terrain",
        extent=[bounds.left, bounds.right, bounds.bottom, bounds.top],
        origin="upper",
    )

    if not aerial:
        cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label("Elevation (m)", fontsize=8)
        cbar.ax.tick_params(labelsize=7)

    ax.plot(
        route_lon,
        route_lat,
        color=GOLD_HEX,
        linewidth=2.2,
        label=f"Route ({display_distance_km:.2f} km)",
        zorder=4,
    )
    ax.scatter(
        lon, lat,
        marker="*",
        color=GOLD_HEX,
        edgecolors="black",
        linewidths=0.6,
        s=110,
        label="Astronaut",
        zorder=5,
    )
    ax.scatter(
        selected_target["Longitude"],
        selected_target["Latitude"],
        marker="X",
        color=BLUE_HEX,
        edgecolors=GOLD_HEX,
        linewidths=1.0,
        s=85,
        label=f"{target_name} ({display_distance_km:.2f} km)",
        zorder=5,
    )

    padding = 0.005
    ax.set_xlim(min(route_lon) - padding, max(route_lon) + padding)
    ax.set_ylim(min(route_lat) - padding, max(route_lat) + padding)

    ax.set_xlabel("Longitude", fontsize=8)
    ax.set_ylabel("Latitude", fontsize=8)
    ax.tick_params(labelsize=7)
    ax.set_title(
        f"Route to {target_name} — {display_distance_km:.2f} km",
        fontsize=9,
        fontweight="bold",
    )
    ax.legend(loc="upper right", fontsize=7, framealpha=0.85)

    svg_uri = _fig_to_svg_uri_and_save(fig, "plots/route.svg")
    return svg_uri, target_name, display_distance_km