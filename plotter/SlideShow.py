import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import struct
import time

minmaxfile = open('minmax.txt', 'r')
MIN_LATITUDE = float(minmaxfile.readline())
MAX_LATITUDE = float(minmaxfile.readline())
MIN_LONGITUDE = float(minmaxfile.readline())
MAX_LONGITUDE = float(minmaxfile.readline())
minmaxfile.close()

fig = plt.figure(figsize=(7, 7)) # make a figure
ax = fig.subplots(nrows=2, ncols=1, gridspec_kw={'height_ratios': [3, 1]}) # make two subplots
fig.subplots_adjust(bottom=0.07, left=0.2, top=0.93, right=0.8) # adjust margins
img = mpimg.imread('map.png') # open map
(IMAGE_HEIGHT, IMAGE_WIDTH, COLOR_CHANNELS) = img.shape # get height and width in pixels
ax[0].axis('off') # turn off units on axes
ax[0].imshow(img) # display image
text_object = ax[0].text(0, 0, '', horizontalalignment='left', verticalalignment='top') # initialize text
map_marker, = ax[0].plot(0, 0, 'bx', markersize=15, markeredgewidth=4);
map_marker.set_visible(False)

def gps_available(gpsdata):
    if (gpsdata[10] != b'N' and gpsdata[6] != b'S'):
        return False
    else:
        return True

def plot_on_map(gpsdata):
    global map_marker
    if not gps_available(gpsdata):
        return;
    latitude = gpsdata[8] + (gpsdata[9] / 60) # convert from degrees and deimal minutes to decimal degrees
    longitude = gpsdata[11] + (gpsdata[12] / 60) # convert from degrees and deimal minutes to decimal degrees
    pixelsx = ((longitude - MIN_LONGITUDE)/(MAX_LONGITUDE - MIN_LONGITUDE)) * IMAGE_WIDTH
    pixelsy = IMAGE_HEIGHT - ((latitude - MIN_LATITUDE)/(MAX_LATITUDE - MIN_LATITUDE)) * IMAGE_HEIGHT
    map_marker.set_data(pixelsx, pixelsy)
    map_marker.set_visible(True)

def plot_graph_update_text(data, text):
    global text_object
    ax[1].cla()
    text_object.set_text(text)
    ax[1].set_xlabel('Time (s)')
    ax[1].set_ylabel('Acceleration (g)')
    ax[1].plot(np.linspace(-1.5, 1.5, 300), data/4096)
    plt.ion()
    fig.show()
    plt.pause(0.001)

def get_data_from_file(file):
    data = np.frombuffer(file.read(1800), dtype = np.int16)

    if (len(data) == 0):
        print('\nReached end of file.\n')
        time.sleep(2)
        exit()
    
    timeseries = data.reshape(300, 3)    
    gpsdata = struct.unpack('BBBcBBdcBdcBdcdc', file.read(65))

    file.read(7) # What is this? Why 7? Won't work unless I do this.

    if (gpsdata[7] == b'U'): # time available
        if gps_available(gpsdata):
            description = ('Date ' + str(gpsdata[0]) + '/' + str(gpsdata[1]) + '/' + str(gpsdata[2]) + '\n'
                           + 'Time ' + str(gpsdata[4]) + ':' + str(gpsdata[5]) + ':' + str(gpsdata[6]) + '\n'
                           + 'Latitude ' + str(gpsdata[8]) + ' ' + str(gpsdata[9]) + str(gpsdata[10], "ascii") + '\n'
                           + 'Longitude ' + str(gpsdata[11]) + ' ' + str(gpsdata[12]) + str(gpsdata[13], "ascii") + '\n'
                           )
        elif (gpsdata[3] == b'D'): # date available
            description = ('Date ' + str(gpsdata[0]) + '/' + str(gpsdata[1]) + '/' + str(gpsdata[2]) + '\n'
                           + 'Time ' + str(gpsdata[4]) + ':' + str(gpsdata[5]) + ':' + str(gpsdata[6]) + '\n'
                           + 'Latitude \nLongitude ')
        else:
            description = ('Date \n'
                           + 'Time ' + str(gpsdata[4]) + ':' + str(gpsdata[5]) + ':' + str(gpsdata[6]) + '\n'
                           + 'Latitude \nLongitude ')
    else:
        description = 'Date \nTime \nLatitude \nLongitude'
    
    delimiter = str(log_file.read(16), 'ascii')    
    if not (delimiter == 'thisisadelimiter'):
        print('\nDelimiter not found! Aborting...\n')
        time.sleep(5)
        exit()

    return (timeseries, description, gpsdata)


log_file = open('AxGPS.log', 'rb')
slide_duration = float(input('Enter slideshow slide duration in seconds: '))
while(log_file):    
    (timeseries, description, gpsdata) = get_data_from_file(log_file)    
    plot_graph_update_text(timeseries, description)
    plot_on_map(gpsdata)
    time.sleep(slide_duration)
