__version__ = "1.0.0"

import rasterio
import geopandas as gpd
import pandas as pd
import numpy as np
from rasterstats import zonal_stats
import argparse
import warnings
from rasterio.warp import calculate_default_transform, reproject, Resampling

warnings.filterwarnings("ignore", category=UserWarning, module="pyproj")
warnings.filterwarnings("ignore", category=UserWarning, module="fiona")

def process_features(gdf, raster_path, wasg_code_to_name):
    with rasterio.open(raster_path) as src:
        print(f"GeoTIFF CRS: {src.crs}")
        print(f"GeoTIFF Bounds: {src.bounds}")
        print(f"GeoTIFF shape: {src.shape}")
        print(f"GeoTIFF nodata value: {src.nodata}")
        
        print(f"Shapefile CRS: {gdf.crs}")
        print(f"Shapefile Bounds: {gdf.total_bounds}")
        
        if src.crs != gdf.crs:
            print("Reprojecting raster data on-the-fly...")
            transform, width, height = calculate_default_transform(
                src.crs, gdf.crs, src.width, src.height, *src.bounds)
            kwargs = src.meta.copy()
            kwargs.update({
                'crs': gdf.crs,
                'transform': transform,
                'width': width,
                'height': height
            })
            reprojected_data = np.zeros((src.count, height, width), dtype=src.dtypes[0])
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=reprojected_data[i-1],
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=gdf.crs,
                    resampling=Resampling.nearest)
            
            stats = zonal_stats(gdf, reprojected_data[0], affine=transform, categorical=True, nodata=src.nodata)
        else:
            print("CRS match. No reprojection needed.")
            stats = zonal_stats(gdf, raster_path, categorical=True, nodata=src.nodata)
    
    results = []
    for idx, feature_stats in enumerate(stats):
        print(f"Processed feature {idx + 1} out of {len(gdf)}:")
        print(f"  Raw count data: {feature_stats}")
        
        if feature_stats:
            total_pixels = sum(feature_stats.values())
            percentages = {wasg_code_to_name.get(int(k), f"Unknown_{k}"): (v / total_pixels) * 100 
                           for k, v in feature_stats.items() if k != 'None'}
        else:
            percentages = {"No_Data": 100}
        
        percentages['feature_id'] = idx
        results.append(percentages)
        print(f"  Soil types found: {len(percentages) - 1}")
        print(f"  Percentages: {', '.join([f'{k}: {v:.2f}%' for k, v in percentages.items() if k != 'feature_id'])}")
    
    return results

def main():
    print(f"dpird-077.py version {__version__}")
    parser = argparse.ArgumentParser(description='Process GeoTIFF and shapefile to determine WASGname percentages.')
    parser.add_argument('shapefile_path', type=str, help='Path to the input shapefile')
    args = parser.parse_args()

    # Load the lookup table
    lookup_df = pd.read_csv("lookup.csv")
    wasg_code_to_name = dict(zip(lookup_df['WASG_CODE'], lookup_df['WASGname']))
    print("First 5 entries of wasg_code_to_name dictionary:")
    for k, v in list(wasg_code_to_name.items())[:5]:
        print(f"  {k}: {v}")
    print(f"Total entries in lookup table: {len(wasg_code_to_name)}")

    # Load the shapefile
    gdf = gpd.read_file(args.shapefile_path)
    print(f"Loaded shapefile with {len(gdf)} features")

    # Process all features at once
    geotiff_path = "./soilgrooup.tif"
    results = process_features(gdf, geotiff_path, wasg_code_to_name)

    if results:
        # Create a DataFrame from the results
        result_df = pd.DataFrame(results)

        # Reorder columns to have feature_id first
        columns = ['feature_id'] + [col for col in result_df.columns if col != 'feature_id']
        result_df = result_df[columns]

        # Output to CSV
        output_path = "output_percentages.csv"
        result_df.to_csv(output_path, index=False)

        print(f"Results saved to {output_path}")
        print(f"Columns in the output: {result_df.columns.tolist()}")
    else:
        print("No results were generated due to an error.")

if __name__ == "__main__":
    main()