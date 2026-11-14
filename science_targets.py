import pandas as pd
import numpy as np

df_raw = pd.read_csv("curiosity_science_targets.csv")

#new df from useful columns
df_clean = df_raw[["Target"]].copy()

#mars equatorial radius in metres
MARS_RADIUS = 3396190.0

#convert coordinates from metres to degrees
df_clean["Longitude"] = np.degrees(df_raw["Easting_m"] / MARS_RADIUS)
df_clean["Latitude"] = np.degrees(df_raw["Northing_m"] / MARS_RADIUS)

df_clean.dropna(inplace = True)

df_clean.to_csv(
    "curiosity_science_targets_clean.csv",
    index=False
)