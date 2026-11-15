import pandas as pd
import numpy as np
import rasterio
import matplotlib.pyplot as plt
import math
from matplotlib.patches import Ellipse
from rasterio.windows import from_bounds, Window
from rasterio.transform import rowcol, xy
from skimage.graph import MCP_Geometric

def mars_distance(lat1, lon1, lat2, lon2): #convert distance between coordinates to km
    radius_km = 3389.5

    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2)

    return 2 * radius_km * math.asin(min(1.0, math.sqrt(a)))

def km_to_degrees(km):
    #convert search radius from km to degrees
    radius_km = 3389.5

    lat_radius = math.degrees(km / radius_km)
    lon_radius = lat_radius / math.cos(math.radians(lat))

    return lat_radius, lon_radius


aerial = False
#location of astronaut and desired search radius in km
lat, lon = -4.58833, 137.44967
radius = 30

df_targets = pd.read_csv("curiosity_science_targets_clean.csv")

#make new series with distances from astronaut to each target
df_targets["Distance_km"] = pd.Series([mars_distance(lat, lon, coord[1], coord[0]) for coord in df_targets[["Longitude", "Latitude"]].values])

#make new df with targets in radius and plot
df_closest_targets = df_targets[df_targets["Distance_km"] <= radius]

#---------------------------
plt.scatter(lon, lat, marker="*", color="blue", s=90, label="Astronaut")
plt.scatter(df_closest_targets["Longitude"], df_closest_targets["Latitude"], color="red", s=5)

lat_radius, lon_radius = km_to_degrees(radius)

#zoom plot to search area
plt.xlim(lon - lon_radius, lon + lon_radius)
plt.ylim(lat - lat_radius, lat + lat_radius)

search_area = Ellipse(
    (lon, lat),
    width=2 * lon_radius,
    height=2 * lat_radius,
    edgecolor="blue",
    facecolor="none",
    linestyle="--",
    linewidth=1.5,
    label="Search radius"
)

plt.gca().add_patch(search_area)

with rasterio.open("gale_topography_small.tif") as src:
    elevation = src.read(1, masked=True)
    bounds = src.bounds

plt.imshow(
    elevation,
    cmap="gray" if aerial else "terrain",
    extent=[
        bounds.left,
        bounds.right,
        bounds.bottom,
        bounds.top
    ],
    origin="upper"
)

plt.colorbar(label="Elevation (m)") if not aerial else None
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.title("Gale Crater Terrain Elevation - Search Area")
plt.savefig('plots/search_area.svg')
plt.show()
#---------------------------



#sort df by distance and print 10 closest targets
df_closest_targets = df_closest_targets.sort_values(by="Distance_km").copy().reset_index(drop=True)
df_closest_targets.index = df_closest_targets.index + 1 

print(f"\nClosest targets within {radius}km of ({lon}, {lat}):")
print(df_closest_targets[:10].to_string())

#prompt user to select target
selection_index = int(input("\nSelect a target (by index): ")) - 1
if selection_index < 0 or selection_index >= len(df_closest_targets):
    print("Selection index out of range.")
    exit()
selected_target = df_closest_targets.iloc[selection_index]

plt.scatter(selected_target["Longitude"], selected_target["Latitude"], marker="X", color="blue", s=80, label="Selected Target")


# Calculate a search area slightly larger than the radius
lat_radius, lon_radius = km_to_degrees(radius * 1.5)

left = lon - lon_radius
right = lon + lon_radius
bottom = lat - lat_radius
top = lat + lat_radius

# Read only the relevant part of the elevation map
with rasterio.open("gale_topography_small.tif") as src:
    if src.crs is None or not src.crs.is_geographic:
        raise ValueError("This code requires a DEM using longitude/latitude.")

    window = from_bounds(
        left, bottom, right, top,
        transform=src.transform
    )

    window = window.intersection(
        Window(0, 0, src.width, src.height)
    )

    elevation = src.read(1, window=window, masked=True)
    transform = src.window_transform(window)
    bounds = rasterio.windows.bounds(window, src.transform)

# Convert elevation to a NumPy array
z = elevation.filled(np.nan).astype(float)

# Calculate pixel dimensions in metres
mars_radius_m = 3389500

dx = abs(transform.a) * math.pi / 180 * mars_radius_m
dx *= math.cos(math.radians(lat))

dy = abs(transform.e) * math.pi / 180 * mars_radius_m

# Calculate terrain slope
gradient_y, gradient_x = np.gradient(z, dy, dx)
slope = np.degrees(
    np.arctan(np.hypot(gradient_x, gradient_y))
)

# Assign a cost to each pixel
# Steeper terrain is more expensive
cost = 1 + 10 * np.tan(np.radians(slope))**2

# Block slopes greater than 12 degrees and missing data
cost[(slope > 12) | ~np.isfinite(slope)] = np.inf

# Convert longitude/latitude into pixel positions
start = rowcol(transform, lon, lat)

end = rowcol(
    transform,
    selected_target["Longitude"],
    selected_target["Latitude"]
)

# Check both points are within traversable terrain
for point in (start, end):
    r, c = point

    if not (0 <= r < z.shape[0] and 0 <= c < z.shape[1]):
        raise ValueError("Start or target is outside the elevation map.")

    if not np.isfinite(cost[r, c]):
        raise ValueError("Start or target is on blocked terrain.")

# Run Dijkstra's algorithm
dijkstra = MCP_Geometric(
    cost,
    fully_connected=True,
    sampling=(dy, dx)
)

distances, _ = dijkstra.find_costs(
    starts=[start],
    ends=[end]
)

if not np.isfinite(distances[end]):
    raise ValueError("No route found within the permitted terrain.")

# Get the route as pixel coordinates
path = np.array(dijkstra.traceback(end))

route_lon, route_lat = xy(
    transform,
    path[:, 0],
    path[:, 1],
    offset="center"
)

# Add exact astronaut and target coordinates
route_lon = [
    lon,
    *route_lon,
    selected_target["Longitude"]
]

route_lat = [
    lat,
    *route_lat,
    selected_target["Latitude"]
]

# Plot Dijkstra route
plt.plot(
    route_lon,
    route_lat,
    color="red",
    linewidth=2,
    label="Dijkstra Route",
    zorder=3
)


plt.scatter(lon, lat, marker="*", color="blue", s=90, label="Astronaut")
plt.scatter(selected_target["Longitude"], selected_target["Latitude"], marker="X", color="blue", s=80, label="Selected Target")

padding = 0.005
plt.xlim(
    min(route_lon) - padding,
    max(route_lon) + padding
)
plt.ylim(
    min(route_lat) - padding,
    max(route_lat) + padding
)

with rasterio.open("gale_topography_small.tif") as src:
    elevation = src.read(1, masked=True)
    bounds = src.bounds

plt.imshow(
    elevation,
    cmap="gray" if aerial else "terrain",
    extent=[
        bounds.left,
        bounds.right,
        bounds.bottom,
        bounds.top
    ],
    origin="upper"
)

plt.colorbar(label="Elevation (m)") if not aerial else None
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.title("Gale Crater Terrain Elevation - Route")
plt.savefig('plots/route.svg')
plt.show()