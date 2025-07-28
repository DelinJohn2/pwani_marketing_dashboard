import json
from pathlib import Path
import geopandas as gpd
from constants import dc





def load_county_geo():
    geo = json.loads(Path(dc.COUNTY_GJ).read_text("utf-8"))
    for f in geo["features"]:
        nm = f["properties"].get("COUNTY_NAM") or f["properties"].get("NAME", "")
        f["properties"]["COUNTY_KEY"] = nm.title().strip()
    return geo


def county_centroids(geojson):
    gdf = gpd.GeoDataFrame.from_features(geojson["features"])
    if gdf.crs is None:
        gdf.set_crs(epsg=4326, inplace=True)
    gdf = gdf.to_crs(3857)
    gdf["geometry"] = gdf.geometry.centroid
    gdf = gdf.to_crs(4326)
    gdf["lon"], gdf["lat"] = gdf.geometry.x, gdf.geometry.y
    return gdf[["COUNTY_KEY", "lon", "lat"]]



def load_sub_geo():
        geo = json.loads(Path(dc.SUBCOUNTY_GJ).read_text("utf-8"))
        for f in geo["features"]:
            name = (
                (
                    f["properties"].get("shapeName")
                    or f["properties"].get("SubCounty")
                    or f["properties"].get("Subcounty")
                    or f["properties"].get("SUB_COUNTY")
                    or f["properties"].get("NAME", "")
                )
                .title()
                .strip()
            )
            f["properties"]["SUB_KEY"] = name
        return geo
