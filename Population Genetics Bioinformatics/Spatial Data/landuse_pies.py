import geopandas as gpd
import pandas as pd
import folium
import os
import argparse
import io
import matplotlib.pyplot as plt
import pyproj
import branca


def pie_charts(csv_path):
    
    #read in landuse csv
    landuse = pd.read_csv(csv_path)
    
    #make NA values in df 0s 
    landuse = landuse.fillna(0)
    
    pie_charts_data = zip(landuse['trees'], landuse['shrub'], landuse['grass'], 
                      landuse['crop'], landuse['built'], landuse['bare'], 
                      landuse['water'], landuse['wetland'])

    fig = plt.figure(figsize=(0.5, 0.5))
    fig.patch.set_alpha(0)
    ax = fig.add_subplot(111)
    plots = []
    for sizes in pie_charts_data:
        ax.pie(sizes, colors=("#006400", "#FFBB22", "#FFFF4C", "#F096FF", "#FA0000", "#B4B4B4", "#0064C8", "#0096A0"))
        buff = io.StringIO()
        plt.savefig(buff, format="SVG")
        buff.seek(0)
        svg = buff.read()
        svg = svg.replace("\n", "")
        plots.append(svg)
        plt.cla()
    plt.clf()
    plt.close()
    
    #print("Returning plots:", plots)  # Debugging line
    
    return plots

# Function to visualize shapefile with land use data
def visualiseShapes(shapefiles, csv, plots):
    # Load the shapefile
    shp = gpd.read_file(shapefiles)
    print("Shapefile columns:", shp.columns.tolist())  # Debugging line
    print("Original CRS:", shp.crs)
    
    # Reproject to WGS84 (EPSG:4326)
    shp = shp.to_crs(epsg=4326)
    print("Reprojected CRS:", shp.crs)

    # Load the CSV file
    landuse = pd.read_csv(csv)
    print("CSV columns:", landuse.columns.tolist())  # Debugging line

    # Clean column names by stripping whitespace
    shp.columns = shp.columns.str.strip()
    landuse.columns = landuse.columns.str.strip()

    # Convert 'group' column in shapefile and 'id' column in CSV to string for merging
    shp['group'] = shp['group'].astype(str)
    landuse['id'] = landuse['id'].astype(str)

    # Merge the GeoDataFrame with the land use data on 'group' and 'id'
    landshp = shp.merge(landuse, left_on='group', right_on='id', how='left')
    
    print("Merged Shapefiles and Landuse:", landshp.columns.tolist())

    # Create a base map centered on a Perth
    m = folium.Map(location=[-31.9505, 115.8605], zoom_start=8, tiles='http://services.arcgisonline.com/arcgis/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}',
           attr="Sources: National Geographic, Esri, Garmin, HERE, UNEP-WCMC, USGS, NASA, ESA, METI, NRCAN, GEBCO, NOAA, INCREMENT P")
    
    # Function to color the polygons 
    def styleShapes(element):
        return {
            'fillColor': '#ffffff',
            'color': '#000000',
            'weight': 1,
            'fillOpacity': 0.6
        }
        
    # Add shapefile elements to map    
    folium.GeoJson(shp, style_function=styleShapes).add_to(m) 

    # Iterate through GeoDataFrame and add pie charts as DivIcons at each location
    for i, (index, row) in enumerate(landshp.iterrows()):
        # Extract the centroid of the geometry
        centroid = row['geometry'].centroid
        coord = [centroid.y, centroid.x]
        
        #print("Centroids:", coord)

        # Create a marker at the centroid
        marker = folium.Marker(location=coord)

        # Add the pie chart as an icon
        icon = folium.DivIcon(html=plots[i])
        marker.add_child(icon)

        # Create a popup with additional information
        popup = folium.Popup(
            "Group: {}<br>Trees: {}%<br>Shrub: {}%<br>Grass: {}%<br>Crop: {}%<br>Built: {}%<br>Bare: {}%<br>Water: {}%<br>Wetland: {}%".format(
                row['group'], row['trees'], row['shrub'], row['grass'], row['crop'], row['built'], row['bare'], row['water'], row['wetland']
            )
        )
        marker.add_child(popup)

        # Add the marker with icon and popup to the map
        m.add_child(marker)
        
    
    # Determine the output HTML file path
    output_html_path = os.path.join(os.path.dirname(csv), 'landuse_pies.html')

    # Save the map to an HTML file
    m.save(output_html_path)
    print(f"Map has been saved to '{output_html_path}'.")
    
    
    # Main function to handle command-line arguments
def main():
    parser = argparse.ArgumentParser(description='Visualize shapefile and land use data on a Leaflet map.')
    parser.add_argument('shapefile', type=str, help='Path to the shapefile (.shp)')
    parser.add_argument('csv', type=str, help='Path to the CSV file with land use data')

    args = parser.parse_args()
    
    pie_charts(args.csv)

    plots = pie_charts(args.csv)
    
    visualiseShapes(args.shapefile, args.csv, plots)

if __name__ == '__main__':
    main()