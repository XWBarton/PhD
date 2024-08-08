import geopandas as gpd
import rasterio
from rasterstats import zonal_stats
import pandas as pd
import argparse

def calculate_land_type_percentages(shapefile_path, geotiff_path):
    # Load the shapefile
    shapefile = gpd.read_file(shapefile_path)
    
    # Open the GeoTIFF file
    with rasterio.open(geotiff_path) as src:
        # Ensure shapefile is in the same CRS as the raster
        if shapefile.crs != src.crs:
            shapefile = shapefile.to_crs(src.crs)
        
        affine = src.transform
        array = src.read(1)  # Read the first band

    # Calculate zonal statistics
    stats = zonal_stats(
        shapefile,
        array,
        affine=affine,
        nodata=src.nodata,
        categorical=True
    )
    
    # Process the results
    results = []
    for feature, stat in zip(shapefile.itertuples(), stats):
        total_pixels = sum(stat.values())
        percentages = {land_type: (count / total_pixels) * 100 for land_type, count in stat.items()} if total_pixels > 0 else {}
        
        # Create a dictionary for each feature with separate columns for each land type
        result = {'id': feature.Index}
        result.update(percentages)
        results.append(result)

    # Convert results to a DataFrame for better readability
    results_df = pd.DataFrame(results)
    return results_df

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Calculate land type percentages in shapefile elements.')
    parser.add_argument('shapefile', type=str, help='Path to the shapefile')
    parser.add_argument('geotiff', type=str, help='Path to the GeoTIFF file')
    parser.add_argument('--output', type=str, default='land_type_percentages.csv', help='Output CSV file name')
    
    # Parse arguments
    args = parser.parse_args()

    # Calculate land type percentages
    land_type_percentages = calculate_land_type_percentages(args.shapefile, args.geotiff)
    
    # Print results in a pretty format
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    pd.set_option('display.max_colwidth', None)
    print(land_type_percentages.to_string(index=False))
    
    # Save results to a CSV file
    land_type_percentages.to_csv(args.output, index=False)
    print(f"Results saved to {args.output}")

if __name__ == '__main__':
    main()