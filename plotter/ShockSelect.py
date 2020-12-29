print('Initializing...')

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.widgets import TextBox
import struct
import time
import math

MARKER_SIZE = 10 # text size of map markers
SELECTED_COLOR = '#000088'
UNSELECTED_COLOR = "#008888"
ACCEL_1G_FACTOR = 4096 # LSBs per g of accleration

TIMESERIES_LENGTH = 300

minmaxfile = open('minmax.txt', 'r') # open text file containing coordinate bounds of map in decimal degrees
MIN_LATITUDE = float(minmaxfile.readline())
MAX_LATITUDE = float(minmaxfile.readline())
MIN_LONGITUDE = float(minmaxfile.readline())
MAX_LONGITUDE = float(minmaxfile.readline())
minmaxfile.close()

# figure setup
fig = plt.figure(figsize=(5, 7))                                   # make a figure
grid_main = fig.add_gridspec(49, 35)                               # add a grid
description_ax = fig.add_subplot(grid_main[0, :])                  # add axes for description box occupying rows 0 to 3
map_ax = fig.add_subplot(grid_main[1:36, :])                       # add axes for map occupying rows 3 to 10
input_ax = fig.add_subplot(grid_main[37:39, 30:])                  # add axes for input field
graph_ax = fig.add_subplot(grid_main[40:, :])                      # add axes for accelerometer data graph
fig.subplots_adjust(bottom=0.1, left=0.15, top=0.9, right=0.85)    # adjust margins
img = mpimg.imread('map.png')                                      # open image file contaning map
(IMAGE_HEIGHT, IMAGE_WIDTH, COLOR_CHANNELS) = img.shape            # get height and width in pixels
map_ax.axis('off')                                                 # turn off units on map image axes
map_ax.imshow(img)                                                 # display image
input_ax.set(xlim=(0, 0.1))                                        # set text input field placement and dimensions
descriptionbox = description_ax.text(0, -1, '')                    # for displaying date, time latitude, longitude
descriptionbox.set_visible(False)                                  # no description by default
description_ax.axis('off')                                         # turn off units

def show_description(string):
    descriptionbox.set_text(string)
    descriptionbox.set_visible(True)

class datablock:    
    x_axis_time = np.linspace(-1.5, 1.5, TIMESERIES_LENGTH)
    
    def __init__(self):
        self.axdata = np.zeros([TIMESERIES_LENGTH, 3], dtype=np.int16)
        self.date_day = 0; self.date_month = 0; self.date_year = 0; self.date_fmt = b'\0';
        self.time_hr = 0; self.time_min = 0; self.time_sec = 0; self.time_fmt = b'\0';
        self.lat_deg = 0; self.lat_min = 0; self.lat_fmt = b'\0';
        self.lng_deg = 0; self.lng_min = 0; self.lng_fmt = b'\0';
        self.alt = 0; self.alt_fmt = b'\0';
        self.max_ax = 0 # max x-y-z rms acceleration value
        self.xpixel = 0 # x coordinate in pixels
        self.ypixel = 0 # y coordinate in pixels
        self.description = ''
        self.position_was_modified = False
        self.map_marker = map_ax.text(self.xpixel, self.ypixel, '', va='center', ha='center', size=MARKER_SIZE, weight='heavy')
        self.map_marker.set_visible(False)
        
    def __lt__(self, other):
        return self.max_ax < other.max_ax

    def date_available(self):
        return self.date_fmt == b'D'

    def time_available(self):
        return self.time_fmt == b'U'

    def loc_available(self):
        return not self.lng_fmt == b'\0'

    def pixel_distance_to(self, x, y):
        return math.sqrt((x - self.xpixel)*(x - self.xpixel) + (y - self.ypixel)*(y - self.ypixel))
    
    def get_from_file(self, file):
        data = np.frombuffer(file.read(1800), dtype = np.int16)

        if (len(data) == 0):
            print('\nReached end of file.\n')
            return False
        
        self.axdata = data.reshape(TIMESERIES_LENGTH, 3)

        # find max
        maxval = 0
        for i in range(TIMESERIES_LENGTH):
            cur = abs((self.axdata[i, 0]**2 + self.axdata[i, 1]**2 + self.axdata[i, 2]**2)**(1/2))
            if (cur > self.max_ax):
                self.max_ax = cur
        
        (self.date_day, self.date_month, self.date_year, self.date_fmt,
         self.time_hr, self.time_min, self.time_sec, self.time_fmt,
         self.lat_deg, self.lat_min, self.lat_fmt,
         self.lng_deg, self.lng_min, self.lng_fmt,
         self.alt, self.alt_fmt)                                        = struct.unpack('BBBcBBdcBdcBdcdc', file.read(65))

        file.read(7) # padding alignmet bytes
        
        delimiter = str(log_file.read(16), 'ascii')    
        if not (delimiter == 'thisisadelimiter'):
            print('\nDelimiter not found! (Data Corrupted)\n')
            return False

        if self.loc_available():
            # set coordinates in pixels for plotting on map
            latitude = self.lat_deg + (self.lat_min / 60) # convert from degrees and deimal minutes to decimal degrees
            longitude = self.lng_deg + (self.lng_min / 60) # convert from degrees and deimal minutes to decimal degrees
            self.xpixel = ((longitude - MIN_LONGITUDE)/(MAX_LONGITUDE - MIN_LONGITUDE)) * IMAGE_WIDTH
            self.ypixel = IMAGE_HEIGHT - ((latitude - MIN_LATITUDE)/(MAX_LATITUDE - MIN_LATITUDE)) * IMAGE_HEIGHT
            self.map_marker.set_position((self.xpixel, self.ypixel))

        # set text description
        if self.time_available():
            if self.loc_available():
                self.description = ('Date ' + str(self.date_day) + '/' + str(self.date_month) + '/' + str(self.date_year) + '\n'
                               + 'Time ' + str(self.time_hr) + ':' + str(self.time_min) + ':' + str(self.time_sec) + '\n'
                               + 'Latitude ' + str(self.lat_deg) + ' ' + str(self.lat_min) + str(self.lat_fmt, "ascii") + '\n'
                               + 'Longitude ' + str(self.lng_deg) + ' ' + str(self.lng_min) + str(self.lng_fmt, "ascii") + '\n'
                               )
            elif self.date_available():
                self.description = ('Date ' + str(self.date_day) + '/' + str(self.date_month) + '/' + str(self.date_year) + '\n'
                               + 'Time ' + str(self.time_hr) + ':' + str(self.time_min) + ':' + str(self.time_sec) + '\n'
                               + 'Latitude \nLongitude \n')
            else:
                self.description = ('Date \n'
                               + 'Time ' + str(self.time_hr) + ':' + str(self.time_min) + ':' + str(self.time_sec) + '\n'
                               + 'Latitude \nLongitude \n')
        else:
            self.description = 'Date \nTime \nLatitude \nLongitude \n'

        # read data from file successful
        return True

    def set_pixel_position(self, x, y):
        self.position_was_modified = True
        self.xpixel = x
        self.ypixel = y
        self.map_marker.set_position((self.xpixel, self.ypixel))

    def show_on_map(self, label):
        # show asterisk if modified i.e. interpolated, no asterisk means actual gps reading
        if not self.loc_available():
            if self.position_was_modified:
                self.map_marker.set_text(label + '*')
            else: # nothing to show on map
                return False
        else:
            self.map_marker.set_text(label)
            
        self.map_marker.set_color(UNSELECTED_COLOR)
        self.map_marker.set_visible(True)
        return True

    def hide_on_map(self):
        self.map_marker.set_visible(False)

    def color_on_map(self):
        self.map_marker.set_color(SELECTED_COLOR)

    def reset_color_on_map(self):
        self.map_marker.set_color(UNSELECTED_COLOR)

    def plot_ax(self):
        graph_ax.cla()
        graph_ax.set_xlabel('Time (s)')
        graph_ax.set_ylabel('Acceleration (g)')
        graph_ax.plot(self.x_axis_time, self.axdata/ACCEL_1G_FACTOR)
        

blocklist = [] # list of all datablocks in file
first_selected_block = None
no_of_blocks_selected = 0

print('Reading data from file...')

# read datablocks from file
log_file = open('AxGPS.log', 'rb')
tmpblock = datablock()
while (tmpblock.get_from_file(log_file)):
    blocklist.append(tmpblock)    
    tmpblock = datablock()
log_file.close()

blocklist_length = len(blocklist) # this doesn't change now

# interpolate map location for blocks without gps data
for i in range(blocklist_length):
    if not blocklist[i].loc_available():
        # find closest points ahead and behind with location available
        prev = i
        nxt = i
        while (prev>0 and not blocklist[prev].loc_available()):
            prev = prev-1
        while (nxt<blocklist_length-1 and not blocklist[nxt].loc_available()):
            nxt = nxt+1        
        if not (blocklist[prev].loc_available() and blocklist[nxt].loc_available()):
            continue
        
        blocklist[i].set_pixel_position((blocklist[prev].xpixel + ((blocklist[nxt].xpixel - blocklist[prev].xpixel)/(nxt - prev)) * (i - prev)),
                                        (blocklist[prev].ypixel + ((blocklist[nxt].ypixel - blocklist[prev].ypixel)/(nxt - prev)) * (i - prev)))

# sort by max shock
blocklist.sort()

def show_clicked_block(mouseclick):
    # if click is somewhere not on the map or points not yet displayed
    if ((mouseclick.inaxes != map_ax) or first_selected_block == None):
        return
    
    # find closest point to click
    closest = 0
    for i in range(no_of_blocks_selected):
        if (blocklist[first_selected_block + i].pixel_distance_to(mouseclick.xdata, mouseclick.ydata) <
            blocklist[closest].pixel_distance_to(mouseclick.xdata, mouseclick.ydata)):
            closest = first_selected_block + i

    # color closest point differently from rest
    for block in (blocklist[first_selected_block : ]):
        block.reset_color_on_map()        
    blocklist[closest].color_on_map()
    
    # show data
    show_description(blocklist[closest].description)
    blocklist[closest].plot_ax()

def show_numbered_points(percentile_input):
    global first_selected_block
    global no_of_blocks_selected
    global descriptionbox
    global graph_ax

    descriptionbox.set_visible(False)
    graph_ax.cla()
    
    # clear points from last click
    for block in blocklist[first_selected_block : ]:
        block.hide_on_map()
    
    # select blocks above threshold i.e. set first_selected_block and show subsequent points on map
    first_selected_block = int((float(percentile_input) * ((blocklist_length - 1) / 100)))
    no_of_blocks_selected = blocklist_length - first_selected_block
    # show selected blocks numbered in reverse order i.e. by decreasing max shock value
    for i in range(no_of_blocks_selected):
        blocklist[first_selected_block + i].show_on_map(str(no_of_blocks_selected - i))

plt.ion()
fig.show()

# text input event
thresh_input_field = TextBox(input_ax, 'Enter Threshold for Percentile Shock: ',)
thresh_input_field.on_submit(show_numbered_points)
# mouseclick event
click_cid = fig.canvas.mpl_connect('button_press_event', show_clicked_block)

# keep program from exiting while figure window is open
while plt.fignum_exists(fig.number):
    plt.pause(0.1)
