import rasterio
import matplotlib.pyplot as plt

with rasterio.open("gale_topography_small.tif") as src:
    elevation = src.read(1, masked=True)
    bounds = src.bounds
print(bounds)
# while True:
#     print("Astronaut starting position:")
#     lon = float(input("Longitude: "))
#     lat = float(input("Latitude:"))

#     if lon < bounds.left or lon > bounds.right:
#         print("Longitude is out of bounds.")
#     elif lat < bounds.bottom or lat > bounds.top:
#         print("Latitude is out of bounds.")
#     else:
#         break

#plt.scatter(lon, lat, color="red", s=10)

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
