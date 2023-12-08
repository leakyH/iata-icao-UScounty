from urllib.request import urlopen
import json
import pandas as pd
from rtree import index
from shapely import from_geojson,geometry
import geopandas as gpd
from tqdm import tqdm
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--geo",default='plotly',type=str,help='if --geo plotly, use a us counties geojson from plotly repo, requires internet connection. Otherwise, provide a local geojson file')
parser.add_argument("--county_name",default='FIPS',type=str,help='specify the county name to be found and inserted into the airport file')
args = parser.parse_args()
#url method
county_name = args.county_name
if args.geo == 'plotly':
    with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
        counties:gpd.GeoDataFrame = gpd.read_file(response)
    counties.loc[:,county_name] = counties.loc[:,"STATE"]+counties.loc[:,"COUNTY"]
else:
    with open(args.geo,'r') as f:
        counties:gpd.GeoDataFrame = gpd.read_file(f)
    counties.loc[:,county_name] = counties.loc[:,"STATE"]+counties.loc[:,"COUNTY"]
assert county_name in counties.columns, f"provided --county_name {county_name} not in counties.columns"



tree = index.Index()

for line,item in counties.iterrows():
    tree.insert(line,item.geometry.bounds)
breakpoint()

airport_df = pd.read_csv("iata-icao.csv")
airport_df = airport_df.query("country_code == 'US'")

for line,item in tqdm(airport_df.iterrows()):
    point = geometry.Point(item['longitude'],item['latitude'])
    found = False
    for idx in tree.intersection(point.bounds):
        feature = counties.loc[idx,"geometry"]
        if feature.contains(point):
            if not found:
                print(f"found: {item['iata']} in {counties.loc[idx,county_name]}")
                found = True
            else:
                print(f"warning: found {item['iata']} in {counties.loc[idx,county_name]} as well as {airport_df.loc[line,county_name]}")
            airport_df.loc[line,county_name] = counties.loc[idx,county_name]
airport_df.to_csv(f"iata-icao-{county_name.lower()}.csv")
