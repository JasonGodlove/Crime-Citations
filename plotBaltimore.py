# -*- coding: utf-8 -*-
"""
Created on Wed Oct 14 18:07:35 2015

@author: Jason Godlove
Reads in Parking Ticket data from Baltimore and plots the coordinate data to a graph
Has functions to classify street cleaning days and hours for each street
"""


import time
import csv as csv
import numpy as np
import matplotlib.pyplot as plt
import geopy
import geopandas as gpd
import datetime
import scipy.cluster as cluster #centroid,label = cluster.vq.kmeans(d,k,iter=200)


def find_location(street,dataframe,disp=False):#finds the latiude and Longitude of the street
    class coordinates(object):
        def __init__(self,latitude,longitude):
            self.latitude = latitude
            self.longitude = longitude
    
    suffix = {'ALAMEDA':'Alameda', 'AV':'Avenue', 'AVE':'Avenue', 'BALTIMORE':'Baltimore', 
              'BLVD':'Boulevard', 'BROADWAY':'Broadway', 'DR':'Drive', 'DWY':'Driveway', 
              'E':'East', 'E/S':'Expressway', 'EAST':'East', 'GRN':'Green', 'HILL':'Hill',
              'HTS':'Heights', 'HWY':'Highway', 'LANE':'Lane', 'PK':'Park', 'PKWY':'Parkway', 
              'PL':'Place', 'RD':'Road', 'ST':'Street', 'STREET':'Street', 'TERR':'Terrace',
              'VE':'View', 'WAY':'Way'}
    prefix = {'E':'East','E/':'East','MT':'Mount','N':'North','S':'South','ST':'Saint','W':'West'}
    #fill with {'AVE':'Avenue','ST':'Street'} using unique from lists   abbrev['AVE']  use np.unique
    
    #format the street to match the dataframe format
    fstreet = street[street.find(' ')+1:street.rfind(' ')].title()    
    
    if fstreet.rfind(' ') == -1:
        keystreet = ' '+fstreet+' '
    else:
        keystreet = fstreet[fstreet.rfind(' '):].title() + ' '  #keyword of street aka second to last separated word in the name
        
    if suffix.has_key(street[street.rfind(' ')+1:]):   
        fstreet = fstreet + ' '+ suffix[street[street.rfind(' ')+1:]]
    if prefix.has_key(fstreet[:fstreet.find(' ')]):
        fstreet = prefix[fstreet[:fstreet.find(' ')].upper()] + fstreet[fstreet.find(' '):]
    
     
    
    #Search the data frame for the street
    roadlist = dataframe.values[:,5].tolist()
    iroadlist = [x for x in roadlist if x is not None] #iterable roadlist with None's removed
    if fstreet in roadlist:
        DFindex = roadlist.index(fstreet)
        if disp:
            print '{} was found'.format(roadlist[DFindex])
    elif any(keystreet in x for x in iroadlist): #If not found an exact match, search for keywords and print found street
        #find the first index of semi matching street
        
        iroadlist_index = [keystreet in x for x in iroadlist].index(True) #Finds the index in iroadlist where the keyword is found       
        
        DFindex = roadlist.index(iroadlist[iroadlist_index]) #returns the index in the larger database for the road
        
        if disp:
            print '\'{}\' was found for \'{}\' when searching for \'{}\' after failing to find \'{}\''.format(iroadlist[iroadlist_index],street,keystreet,fstreet)
        
    else:     #otherwise print not found street's name
        if disp:
            print '{} was not found after searching for \'{}\' and \'{}\'.'.format(street,fstreet,keystreet)
        return [],[]
        

    #return lat and long coordinates of street
    location = coordinates(dataframe.geometry[DFindex].centroid.coords.xy[0][0],dataframe.geometry[DFindex].centroid.coords.xy[1][0])
    return location , DFindex



def find_location_geocoder(street,geo): #uses the geocoder #geo = geopy.geocoders.GoogleV3() to find lat and long
    location = []    
    try:    
        location = geo.geocode(street + ' Baltimore MD',timeout=60)
    except:
        print 'Timeout at {}'.format(street)
        time.sleep(1)
        location = geo.geocode(street + ' Baltimore MD',timeout=60)
    time.sleep(.2)    
    
    return location



def save_csv_data(filename,data,header): #Saves data
    data_file = open(filename, "wb")
    data_file_object = csv.writer(data_file)
    data_file_object.writerow(header)	# write the column headers
    for row in data:									# For each row in test file,
        data_file_object.writerow(row)			# write the PassengerId, and predict 0.
    											# Close out the files.
    data_file.close()


    
def load_csv_data(filename):#Loads all of the data in a csv file and returns the data and header
    
    csv_file_object = csv.reader(open(filename, 'rb'))       # Load in the csv file
    header = csv_file_object.next()         
    data=[]                                                     # Create a variable to hold the data
    for row in csv_file_object:                 # Skip through each row in the csv file
        data.append(row)                        # adding each row to the data variable
    data = np.array(data)                       # Then convert from a list to an array
    return data,header
        
    
    
def exportBaltimore(): # Separates out just the Baltimore data from the data
    regionsdf = gpd.read_file('dc-baltimore_maryland_admin.geojson')
    
    #baltimore shape in index 18
    baltimoreBD = regionsdf.values[18,:]
    baltimoreBD[1]
    df = gpd.read_file('dc-baltimore_maryland_roads.geojson')
    df = df[df.geometry.within(baltimoreBD[1])]
    
    with open('baltimore.geojson','w') as f:
        f.write(df.to_json())

def format_raw_citation(): #Formats the raw citation data adding useful parameters
        
    csv_file_object = csv.reader(open('Baltimore_Parking_Citations_2013-2015.csv', 'rb'))       # Load in the csv file
    header = csv_file_object.next()                             # Skip the fist line as it is a header
    header.append('Latitude')
    header.append('Longitude')
    header.append('Datetime')
    header.append('Weekday') #Mon:0 Sun:6
    header.append('Day')
    header.append('Hour')
    header.append('Linked Street')
    header.append('Street Index')
    data=[]                                                     # Create a variable to hold the data
    
    
    #geo = geopy.geocoders.Nominatim()
    #geo = geopy.geocoders.GoogleV3()
    
    for row in csv_file_object:                 # Skip through each row in the csv file
        #converting the street data to latitude and longitude 
        if row[8]!='No Stop/Park Street Cleaning' :
            continue
    
        #location = find_location_geocoder(row[6],geo)
        location,DFindex = find_location(row[6],baltimoreDF)   
        if not location: #no location at that spot 
            continue
        else:
            row.append(location.latitude)
            row.append(location.longitude)
        #Breaking down date data into a useable form
        t = datetime.datetime.strptime(row[10],'%m/%d/%Y %I:%M:%S %p')
        row.append(t)
        row.append(t.weekday()) #Day of the week   Mon:0 Sun:7
        row.append(t.day) #Day of the month
        row.append(t.hour) #Hour of the day out of 24
        row.append(baltimoreDF.values[DFindex,5])
        row.append(DFindex)
        data.append(row)# adding each row to the data variable

        
    data = np.array(data)                       # Then convert from a list to an array
    
    save_csv_data('Baltimore_Cleaning_Citations_w_locations.csv',data,header)
    return data,header



def road_profile(road_index,data,baltimoreDF,baltimoreBD):#,data_frame): # Plots various descriptive data based on weekday, day of month, and time histograms
    #input road_index which is the index of one of the citations in data
    #returns street cleaning schedule estimation
    
    #profile for each day, indicates hours for that day and which weeks of the month it is active,    
    #profile = [[None]*2]*7 #Change to one variable called profile and make it a dataframe
    
    
    cit = [x for x in range(len(data)) if data[x,24].astype(np.int) == data[road_index,24].astype(np.int)]
    cit = data[cit,20:23].astype(np.int)
    #0: weekday
    #1: day of the month
    #2: time of the day
    
    fig = plt.figure()
    plt1 = fig.add_subplot(221)
    #Plot the outline of Baltimore and the road in question
    gpd.plotting.plot_polygon(plt1,baltimoreBD[1]) #plots the outline of the city
    gpd.plotting.plot_linestring(plt1,baltimoreDF.values[data[road_index,24],3])
    children = plt1.get_children()
    children[2].set_lw(5)
    children[3].set_lw(5)
    
    plt.title('{}: {} samples'.format(data[road_index,23],len(cit)))    
    
    
    #Note that empty entries don't append properly!!!!!!!!!
    plt2 = fig.add_subplot(222)
    d=[None]*7
    for i in range(7):
        d[i] = cit[cit[:,0]==i,0] #Don't need to do this for this plot but want to make everything color coded

    plt.hist(d,np.subtract(range(8),0.5),stacked=True)
    
    plt.title('Days of the Week')
    plt2.set_xticks(range(7))
    plt2.set_xticklabels(['Mon','Tue','Wed','Thr','Fri','Sat','Sun'])
    ax = plt2.axis()
    plt2.axis([-1,7,ax[2],ax[3]])    
    
    
    d=[None]*7
    week_in_month = [None]*7
    for i in range(7):
        d[i] = cit[cit[:,0]==i,1] #Don't need to do this for this plot but want to make everything color coded
        bins = np.bincount(d[i])
        bins = np.resize(bins,28) #pads end with zeros in case no data is for the end of the month       
        temp = [False]*4        
        for weeks in range(4):
            temp[weeks] = any(bins[(weeks*7+1):((weeks+1)*7+1)])
        if any(temp):
            week_in_month[i] = temp
                        
    plt3 = fig.add_subplot(223)
    plt.hist(d,np.subtract(range(1,33),0.5),stacked=True)
    plt.title('Day of the Month')
    ax = plt3.axis()
    plt3.axis([0,32,ax[2],ax[3]])    
    plt3.set_xticks(range(1,32))
    #plt.legend(['Mon','Tue','Wed','Thr','Fri','Sat','Sun'])
    
    d=[None]*7
    hours=[None]*7
    for i in range(7):
        d[i] = cit[cit[:,0]==i,2] #Don't need to do this for this plot but want to make everything color coded
        if len(d[i]):
            hours[i] = [d[i].min(), d[i].max()]


    plt4 = fig.add_subplot(224)
    bins,_,_ = plt.hist(d,np.subtract(range(24),0.5),stacked=True)
    plt.title('Hour of the Day')
    ax = plt4.axis()
    plt4.axis([-1,24,ax[2],ax[3]])    
    plt4.set_xticks(range(24))
    plt.legend(['Mon','Tue','Wed','Thr','Fri','Sat','Sun'])
    
    return hours , week_in_month #profile #returns the predicted day of the week, frequency of cleaning (every week, every other week, every month) and hours

############################   Loading data
        
regionsdf = gpd.read_file('dc-baltimore_maryland_admin.geojson')
baltimoreBD = regionsdf.values[18,:]
del regionsdf   

baltimoreDF = gpd.read_file('baltimore.geojson')
# FYI there are 536 different roads in the set
   
#data,header = format_raw_citation()
data,header = load_csv_data('Baltimore_Cleaning_Citations_w_locations.csv')

X = data[:,17].astype(np.float)
Y = data[:,18].astype(np.float)


fig = plt.figure()
plt1 = fig.add_subplot(111)
gpd.plotting.plot_polygon(plt1,baltimoreBD[1]) #plots the outline of the city
children = plt1.get_children()
children[2].set_lw(5)

plt.scatter(X,Y,zorder=2)
plt.show()

road_profile(16,data,baltimoreDF,baltimoreBD) #Single road
road_profile(14,data,baltimoreDF,baltimoreBD) #Mixed road







