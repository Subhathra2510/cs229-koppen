#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May  5 11:27:24 2019

@author: ngotm
"""

import numpy as np
import pandas as pd
import urllib
from scipy import spatial
import os.path

def main():
    
    pos = ["landscape", "nature", "outdoors", "natureza", "forest", 
           "nationalpark", "worldwidelandscapes", "desert", "arctic"]
    
    neg = ["bw", "night", "abstract", "architecture", "animal", "animals", "bird", "birds", "bokeh",
           "black", "blackandwhite", "blackwhite", "building", "boy", "camping", "car",
           "city", "dog", "dogs", "downtown", "family", "fauna", "flower", "flowers", 
           "food", "funny", "girl", "graffiti", "life", "macro", "me", "myself", "nyc", "ocean", "people", 
           "portrait", "portraiture", "reflection", "sea", "street", 
           "underwater", "urban", "white", "wildlife", "zenubud"]
    
    metadata_file = "photo_metadata.csv"
    coords_file = "coords.csv"
    labels_file = "koppen_labels.csv"
    koppen_file = "KG_1986-2010_5m_ocean.csv"
    photo_folder = "photos"
    n = 100000

    downloadImages(metadata_file, coords_file, photo_folder, pos, neg, n)
    classifyCoords(coords_file, koppen_file, labels_file)
    

def downloadImages(metadata_file, coords_file, folder, pos, neg, n):
    print("Reading metadata...")
    data = pd.read_csv(metadata_file)
#    data = pd.read_csv(metadata_file, nrows=n)
#    data.to_csv("values.csv")
   
    print("Metadata read.")
    i = 0
    total = 0
    image_data = {}
    for row in data.values:
        tags = set(row[3][1:-1].split(","))
        if checkTags(tags, pos, neg):
            photo_id = row[0]
            latitude = row[4]
            longitude = row[5]
            date_taken = row[7]
            secret = row[10]
            server = row[11]
            farm = row[12]
            url = ("https://farm%s.staticflickr.com/%s/%s_%s.jpg" % (farm, server, photo_id, secret))
            success = attemptDownload(url, photo_id, folder)
            if (success):
                image_data[photo_id] = (latitude, longitude, date_taken)
                total += 1
        i += 1
        if (i % 10000 == 0):
            print("%s images checked (%s)" % (i, total))
            
    print("%s / %s" % (total, n))
    
    print("Creating dataframe...")
    image_df = pd.DataFrame.from_dict(image_data, orient="index", columns=['lat', 'lon', 'date'])
    image_df = image_df.reset_index()
    image_df['id'] = image_df['index']
    del image_df['index']

    print("Writing coords to %s..." % coords_file)
    image_df.to_csv(coords_file)

def classifyCoords(coords_file, koppen_file, labels_file):
    
    legend = ['Af', 'Am', 'As', 'Aw',           # tropical
              'BSh', 'BSk', 'BWh', 'BWk',       # dry
              'Cfa', 'Cfb', 'Cfc',              # temperate
              'Csa', 'Csb', 'Csc', 
              'Cwa', 'Cwb', 'Cwc',
              'Dfa', 'Dfb', 'Dfc', 'Dfd',       # continental
              'Dsa', 'Dsb', 'Dsc', 'Dsd',
              'Dwa', 'Dwb', 'Dwc', 'Dwd',
              'EF', 'ET', 'Ocean']              # polar + ocean
    
    print("Reading coordinates and Koppen data...")
    coords = pd.read_csv(coords_file, index_col=0)    
    koppen = pd.read_csv(koppen_file)
    
    koppen_xy = np.hstack((koppen['lat'][:, np.newaxis], koppen['lon'][:, np.newaxis]))
    coords_xy = np.hstack([coords['lat'][:, np.newaxis], coords['lon'][:, np.newaxis]])
    
    print("Classifying coordinates...")
    mytree = spatial.cKDTree(koppen_xy)
    dist, indexes = mytree.query(coords_xy)
    print(np.mean(dist))
    print(np.max(dist))

    coords['climate'] = koppen['KG'][indexes].values
    coords['symbol'] = [legend[i-1] for i in coords['climate']]
    
    # sort ids alphabetically
    coords['id'] = coords['id'].apply(str)
    coords = coords.sort_values(by=['id'])
    coords['id'] = coords['id'].apply(int)
    coords.reset_index(drop=True, inplace=True)
    
    # print(coords)
    print("Writing labels to %s..." % labels_file)
    coords.to_csv(labels_file)

def attemptDownload(url, id, folder=""):
    try:
        if not os.path.isfile("%s/%s.jpg" % (folder, id)):
            urllib.request.urlretrieve(url, ("%s/%s.jpg" % (folder, id)))
        return True
    except:
        return False
    
def checkTags(tags, pos, neg):
    return False if any(x in tags for x in neg) else any(x in tags for x in pos)
    
if __name__ == '__main__':
    main()
    
