import rasterio

with rasterio.open("gale_elevation.IMG") as src:
    print("CRS:", src.crs)
    print("Bounds:", src.bounds)
    print("Resolution:", src.res)
    print("Dimensions:", src.width, src.height)
    print("Data type:", src.dtypes)
    print("NoData:", src.nodata)
    print("Transform:", src.transform)