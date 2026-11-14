import rasterio
import matplotlib.pyplot as plt

with rasterio.open("TES_Thermal_Inertia.tif") as src:
    thermal_inertia = src.read(1, masked=True)
    bounds = src.bounds

plt.imshow(
    thermal_inertia,
    cmap="inferno",
    extent=[
            bounds.left,
            bounds.right,
            bounds.bottom,
            bounds.top
        ],
        origin="upper"
    )

plt.colorbar(label="Thermal Inertia")
plt.xlabel("Easting")
plt.ylabel("Northing")
plt.title("Gale Crater Thermal Inertia")
plt.show()
