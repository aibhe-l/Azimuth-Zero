import pandas as pd
import numpy as np
import rasterio
import matplotlib.pyplot as plt
import math

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


#location of astronaut and desired search radius in km
lat, lon = -4.58833, 137.44967
radius = 0.5

plt.scatter(lon, lat, marker="*", color="blue", s=90, label="Astronaut")

df_targets = pd.read_csv("curiosity_science_targets_clean.csv")

#make new series with distances from astronaut to each target
df_targets["Distance_km"] = pd.Series([mars_distance(lat, lon, coord[1], coord[0]) for coord in df_targets[["Longitude", "Latitude"]].values])

#make new df with targets in radius and plot
df_closest_targets = df_targets[df_targets["Distance_km"] <= radius]
plt.scatter(df_closest_targets["Longitude"], df_closest_targets["Latitude"], color="red", s=5)

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

lat_radius, lon_radius = km_to_degrees(radius)

#zoom plot to search area
plt.xlim(lon - lon_radius, lon + lon_radius)
plt.ylim(lat - lat_radius, lat + lat_radius)


with rasterio.open("gale_topography_small.tif") as src:
    elevation = src.read(1, masked=True)
    bounds = src.bounds

print(elevation)

plt.imshow(
    elevation,
    cmap="terrain",
    extent=[
        bounds.left,
        bounds.right,
        bounds.bottom,
        bounds.top
    ],
    origin="upper"
)

plt.colorbar(label="Elevation (m)")
plt.xlabel("Easting")
plt.ylabel("Northing")
plt.title("Gale Crater Terrain Elevation")
plt.show()

