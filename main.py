#Leave comment when not in raspberry pi
#Import relevant files
from email.mime import image
import RPi.GPIO as GPIO
import smbus
from time import sleep
from hx711py.hx711 import HX711
import cv2
import numpy as np
import sys
import math
from datetime import datetime
from gpiozero import AngularServo
import os
import time
from sklearn.cluster import KMeans
from matplotlib import pyplot as plt
import matplotlib
from PIL import Image
#Pat Light --------------------------------------------------------
#Light Initiliasation
light_relay_pin=23 #8 from top outside
GPIO.setmode(GPIO.BCM)
GPIO.setup(light_relay_pin,GPIO.OUT)
GPIO.output(light_relay_pin, GPIO.LOW)

def lightOn():
    """
    Title: Light ON
    Description: This function sets the pin 23 high which the light to turn on
    """
    global currentAngle
    print("light on")
    GPIO.output(light_relay_pin,GPIO.HIGH)
    setAngle(currentAngle,True)
def lightOff():
    """
    Title: Light OFF
    Description: This function sets pin 23 Low, which cuts power to the light, turning it off
    """
    global currentAngle
    print("light off")
    GPIO.output(light_relay_pin, GPIO.LOW)
    setAngle(currentAngle,True)
def lightCleanup():
    """
    Title: Light Cleanup
    Description: This function clears the GPIO programming to the relay
    """
    GPIO.cleanup ## after you are done make sure to cleanup (it will turn the light back on)

#Spin servo @Dylan--------------------------------------------------------
currentAngle = 0
def setAngle(angle,lightCorrect=False):
    """
    Title: Set Angle
    Description: This formula sets the angle of the servo and also updates the value of the current angle. It ranges from -90<angle<90 degrees. This utilises a PWM approach and uses the max and minimum pulse widths to alter the angles
    Inputs: angle - The angle at which the servo will be set at
    Outputs: currentAngle - NOT a return value, however a global variable which is updated whenever the function is called
    """
    #Ensure we the global variable currentAngle
    global currentAngle
    #create the connection between servo, GPIO pin 17, and setting the minimum and maximum pulse width which dictates the angle
    servo = AngularServo(17,min_pulse_width = 0.0006,max_pulse_width = 0.00255)
    servo.angle = angle #set the angle
    sleep(1) #give time to move the servo
    #repeat twice to fix light power issue
    servo.angle = angle #set the angle
    sleep(1) #give time to move the servo
    #set instructions to an unused pin as to 'turn off' the servo and reduce jitter
    servo = AngularServo(21,min_pulse_width = 0.001,max_pulse_width = 0.002)
    currentAngle = angle #update current angle
    if (not lightCorrect):
        print('Angle set to ' + str(angle))

#Read load sensor @pat ------------------------------------------------------------------------------
# ref:https://tutorials-raspberrypi.com/digital-raspberry-pi-scale-weight-sensor-hx711/
# reference unit has been obtained using a known weight

referenceUnit = 1
hx = HX711(5, 6) # data is connected to pin 6 and sck to pin 5 and
hx.set_reading_format("MSB", "MSB")
hx.set_reference_unit(referenceUnit)
hx.reset()

# this function is used to tare the load cell
def calibrateLS():
    """
    Title: Calibrate Load Cell
    Description: used initialise, tare and calibrate load cell
    """
    tareLS()
    print(" enter known weight and place weight on the scale")
    knownWeight=input()
    givenWeight= readLS()
    referenceUnit = givenWeight/float(knownWeight)
    hx.set_reading_format("MSB", "MSB")
    hx.set_reference_unit(referenceUnit)
    hx.reset()
    
    if(abs(readLS() - float(knownWeight))>1):
        print("Error in calibration. Please remove weight and retry")
        


def tareLS():
    """
    Title: read load cell
    Description: thi function is used to determine weight on the load cell
    output: this function outputs the weight on the lod cell in grams
    """
    hx.tare() # tare the scale

    print("Tare done! ")



def readLS():
    val = hx.get_weight(5)
    hx.power_down()
    hx.power_up()
    sleep(1)
    return val

#Read IMU @Kaelan-----------------------------------------------------------------------------------------------------------
#IMU is called the MPU6050
# Help from https://www.electronicwings.com/sensors-modules/mpu6050-gyroscope-accelerometer-temperature-sensor-module
# https://www.electronicwings.com/raspberry-pi/mpu6050-accelerometergyroscope-interfacing-with-raspberry-pi
# https://invensense.tdk.com/wp-content/uploads/2015/02/MPU-6000-Datasheet1.pdf

MPU_initialised = False #global boolean variable used to determine if MPU is already initialised, to stop from recalling it again


def MPU_create_registers():
    """
    Title: MPU6050 Inertia Measurement Unit Register Creation
    Description: This function creates a set of global variables that correspond to the registers for the MPU6050
    """
    global PWR_MGMT_1, SMPLRT_DIV, CONFIG, GYRO_CONFIG, INT_ENABLE, ACCEL_XOUT_H, ACCEL_YOUT_H, ACCEL_ZOUT_H, GYRO_XOUT_H, GYRO_YOUT_H, GYRO_ZOUT_H, IMU_Device_Address
    PWR_MGMT_1   = 0X6B
    SMPLRT_DIV   = 0X19
    CONFIG       = 0X1A
    GYRO_CONFIG  = 0X1B
    INT_ENABLE   = 0X38
    ACCEL_XOUT_H = 0X3B
    ACCEL_YOUT_H = 0X3D
    ACCEL_ZOUT_H = 0X3F
    GYRO_XOUT_H  = 0X43
    GYRO_YOUT_H  = 0X45
    GYRO_ZOUT_H  = 0X47
    IMU_Device_Address = 0x68   # MPU6050 device address

def MPU_init():
    """
    Title: MPU6050 Intertia Measurement Unit Initialiser
    Description: This function initialises the MPU6050 such that the relevant registers are written to and can be read
    """
    global bus, MPU_initialised
    
    
    print("Initialising MPU6050")
    #Create registers used for MPU6050
    MPU_create_registers()
    
    
    bus = smbus.SMBus(1)     # or bus = smbus.SMBus(0) for older version boards
    #If not working solve by https://github.com/johnbryanmoore/VL53L0X_rasp_python/issues/13
    #write to sample rate register
    bus.write_byte_data(IMU_Device_Address, SMPLRT_DIV, 7)

    #Write to power management register
    bus.write_byte_data(IMU_Device_Address, PWR_MGMT_1, 1)

    #Write to Configuration register
    bus.write_byte_data(IMU_Device_Address, CONFIG, 0)

    #Write to Gyro configuration register
    bus.write_byte_data(IMU_Device_Address, GYRO_CONFIG, 24)

    #Write to interrupt enable register
    bus.write_byte_data(IMU_Device_Address, INT_ENABLE, 1)
    
    #Calibrate Device
    MPU_calibrate()
    MPU_initialised = True
    print("MPU6050 initialisation complete")
    
def MPU_read_raw_data(addr):
    """
    Title: MPU6050 Inertia Measurement Unit Raw data Reader
    Description: This function reads the raw data given from the MPU6050. The MPU6050 outputs a 16 bit value given from two 8 bit words registers. This function reads those and combines them to output a signed unscaled 16 bit value.
    Inputs: addr - corresponds to the variable/register we are retrieving the value of. This is the acceleration of or rotation about x,y or z axis.
    Outputs: value - Outputs the signed unscaled value read from the MPU6050 for the given input
    """
    #The data straight from the MPU6050 is in 2 8bit words. Combine them to get the raw value
    #Accelero and Gyro value are 16-bit
    high = bus.read_byte_data(IMU_Device_Address, addr)
    low = bus.read_byte_data(IMU_Device_Address, addr+1)

    #concatenate higher and lower value
    value = ((high << 8) | low)
    
    #to get signed value from mpu6050
    if(value > 32768):
            value = value - 65536
    return value

def MPU_scaledValue(variable):
    """
    Title: MPU6050 Get Value
    Description: THis function obtains the scaled signed value for a given variable input
    Inputs: variable - corresponds to variable/register we are retriving the value of. This is the acceleration of, or rotation about the x,y or z axis.
    Outputs: Returns the scaled signed value for the given variable outputed by the MPU6050
    Note: This is for use between function, and does not produce a value to be used by users
    """
    
    accel_scale_factor = 16384 #corresponds to acceleration sensitivity of +- 2 gforce
    ang_vel_scale_factor = 131 #corresponds to gyroscope sensitivity of +-250 degrees/s
    
    #determine whether acceleration or tilting
    if (variable==ACCEL_XOUT_H or variable == ACCEL_YOUT_H or variable == ACCEL_ZOUT_H):
        return MPU_read_raw_data(variable)/accel_scale_factor
        #returns value in g force which is m/s^2
    elif (variable== GYRO_XOUT_H or variable == GYRO_YOUT_H or variable == GYRO_ZOUT_H):
        return MPU_read_raw_data(variable) /ang_vel_scale_factor
        #returns value in degrees/second
    else:
        print("Variable not suitable for function")
        #if we reach a variable not meant for this function
def MPU_getValue(variable):
    """
    Title: MPU6050 Inertia Measurement Unit Get Value
    Description: This function returns the the user friendly value of the variable inserted into it, rounded to 2 decimal places including the offsets and sensitivity factors. This value differs from MPU_scaledValue since it is a value that includes the offset and is rounded, being intended for presentation and not use from other functions
    Inputs: variable - takes a string input of the shortened value name from the list of aX, aY, aZ, wX, wY, wZ
    Outputs: returns the scaled, calibrated value for the given variable rounded to 2 decimal places
    """
    #Ensure we use the calibrated offsets
    global aX_offset, aY_offset, aZ_offset, wX_offset, wY_offset, wZ_off
    #Given the input variable,return the scaled value after adding the offset and rounding to 2 decimal places.
    if variable=='aX':
        return round(MPU_scaledValue(ACCEL_XOUT_H) + aX_offset,2)
    elif variable == 'aY':
        return round(MPU_scaledValue(ACCEL_YOUT_H) + aY_offset,2)
    elif variable == 'aZ':
        return round(MPU_scaledValue(ACCEL_ZOUT_H) + aZ_offset,2)
    elif variable == 'wX':
        return round(MPU_scaledValue(GYRO_XOUT_H) + wX_offset,2)
    elif variable == 'wY':
        return round(MPU_scaledValue(GYRO_YOUT_H) + wY_offset,2)
    elif variable == 'wZ':
        return round(MPU_scaledValue(GYRO_ZOUT_H) + wZ_offset,2)
    else:
        #error message if we do not enter the correct input
        print("Wrong input type. Did you put in string version?")
        
def MPU_tiltAngles():
    """
    Title: MPU6050 Inertia Measurement Unit Tilt Angle Finder
    Description: This function takes into account the gforce given from the MPU6050 from gravity, and convert it into the amount of tilt of the xy plane. We specifically do not include tilt of the xz or yz plane because does not interfere with our experiment.
    Outputs:
        tiltX - the amount of tilt that occurs around the y axis. E.g. a positive tiltX means we are tilting in the direction of the positive x axis.
        tiltY - the amount of tilt that occurs around the x axis. E.g. a positive tiltY means we are tilting in the direction of the positive y axis
    """
    #Obtain the raw acceleration values of xyz directions including offset
    x = MPU_scaledValue(ACCEL_XOUT_H) + aX_offset
    y = MPU_scaledValue(ACCEL_YOUT_H) + aY_offset
    z = MPU_scaledValue(ACCEL_ZOUT_H) + aZ_offset
    #If input is too insignificant, set it to 0. This helps with accuracy since small reductions in value change the angle greatly
    if abs(x)<0.01:
        x = 0
    if abs(y) <0.01:
        y=0
    if abs(z)<0.01:
        z=0
    #create the total vector via pythagoras
    total_vec = math.sqrt(x*x + y*y +z*z)
    #find roll and ptich and round to 2 decimal places
    roll = round(math.degrees(math.asin(x/total_vec)),2)
    pitch = round(math.degrees(math.asin(y/total_vec)),2)
    return roll,pitch
    
def MPU_calibrate():
    """
    Title: MPU6050 Inertia Measurement Unit Calibration
    Description: This function calibrates the MPU6050 to reduce errors in tilt
    Outputs: Note doesn't return a value but creates global variables
        aX_offset   - value to offset acceleration in x direction
        aY_offset   - value to offset acceleration in y direction
        aZ_offset   - value to offset acceleration in z direction
        wX__offset  - value to offset angular velocity around x axis
        wY_offset   - value to offset angular velocity around y axis
        wZ__offset  - value to offset angular velocity around z axis
    """
    #Warning before calibration
    print("Please ensure device is sitting on a flat stable surface")
    #Creating global values to offset in other functions
    global aX_offset, aY_offset, aZ_offset, wX_offset, wY_offset, wZ_offset
    #Indication of Calibration
    print("Calibrating MPU6050 Now")
    #We obtain the current values of acceleration of and angular velocity around xyz, then set the offset of the difference between what they are and there original set position
    aX = MPU_scaledValue(ACCEL_XOUT_H)
    aX_offset = 0-aX
    aY = MPU_scaledValue(ACCEL_YOUT_H)
    aY_offset = 0-aY
    aZ = MPU_scaledValue(ACCEL_ZOUT_H)
    aZ_offset = -1-aZ
    wX = MPU_scaledValue(GYRO_XOUT_H)
    wX_offset = 0-wX
    wY = MPU_scaledValue(GYRO_YOUT_H)
    wY_offset = 0-wY
    wZ = MPU_scaledValue(GYRO_ZOUT_H)
    wZ_offset = 0-wZ
    print("MPU6050 Calibration Complete")
    
def MPU_test(numTimes):
    """
    Title: MPU6050 Tester
    Description: This function is a testing function used to output the 6 possible values expected from the MPU6050 as well as the 2 tilt values. It can loops it a set number of times or infinitely, and prints the 8 values to the screen in order of
        AccelerationX  AccelerationY  AccelerationZ angularVelocityX   angularVelocityY   angularVelocityZ roll(tilt of X axis) pitch(tilt of Y axis)
        To print infinitely type 'inf' as the input
    Inputs: numTimes - the number of times we print values to the console
    """
    global MPU_initialised
    if MPU_initialised == False:
        MPU_init()
   
    print('{0:>8} {1:>8} {2:>8} {3:>8} {4:>8} {5:>8} {6:>8} {7:>8}'.format('aX','aY','aZ','wX','wY','wZ','tiltX','tiltY'))
    if (numTimes == 'inf'):
        while(True):
            print('{0:8} {1:8} {2:8} {3:8} {4:8} {5:8} {6:8} {7:8}'.format(MPU_getValue('aX'),MPU_getValue('aY'),MPU_getValue('aZ'),MPU_getValue('wX'),MPU_getValue('wY'),MPU_getValue('wZ'),MPU_tiltAngles()[0],MPU_tiltAngles()[1]))
    else:
        for x in range(numTimes):
            print('{0:8} {1:8} {2:8} {3:8} {4:8} {5:8} {6:8} {7:8}'.format(MPU_getValue('aX'),MPU_getValue('aY'),MPU_getValue('aZ'),MPU_getValue('wX'),MPU_getValue('wY'),MPU_getValue('wZ'),MPU_tiltAngles()[0],MPU_tiltAngles()[1]))

recordedValues=[] #Global list used to store a experiment results from MPU_singleTest
def MPU_singleTest(numTimes,variable,recordValues):
    """
    Title: MPU6050 Inertia Measurement Unit Single Variable Test
    Description: This function loops the MPU6050 output for a single variable for a set number of times or infinitely, with the option to save the values to a list
    Inputs:
        numTimes = number of loop iterations (or readings) you want, alternatively can write 'inf' for infinite looping
        variable = refers to which variable from the MPU6050 you wish to read
            Options aX, aY, aZ, tiltX or roll, tiltY or pitch; all written as a string
        recordValues = Boolean value determining whether or not to save values to the list recordedValues.
            Note - will overwrite current recordedValues values
    Outputs:
        Not specified but will update recordedValues list
    """
    global recordedValues #ensure we are working with the global variable
    recordedValues = [] #clear the list
    #Printing
    print('{0:>50}'.format(variable)) #print the variable title
    #obtain relevant value from variable name
    if variable=="roll" or "tiltX":
        outputValue = MPU_tiltAngles()[0]
    elif variable == "pitch" or "tiltY":
        outputValue = MPU_tiltAngles()[1]
    else:
        outputValue = MPU_getValue(variable)
    #print to console indefinitely or set number of times
    if (numTimes == 'inf'):
        while(True):
            print('{0:50}'.format(outputValue))
            if recordValues == True:
                recordedValues.append(outputValue)
    else:
        for x in range(numTimes):
            print('{0:50}'.format(outputValue))
            if recordValues == True:
                recordedValues.append(outputValue)
    
                      
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Take an image with PiCam @Calvin Medeira
# Ref: https://pyimagesearch.com/2015/03/30/accessing-the-raspberry-pi-camera-with-opencv-and-python/
def record_image(path="/home/raspberry/TestPics"):
    """
    Title: WebCam record image
    Description: This function will save a picture in user defined path
    Inputs:
    Outputs: path of saved image
    """
    camera = cv2.VideoCapture(0)
    now = datetime.now()
    
    _, image = camera.read()
    cv2.waitKey(10)
    dir = os.path.join(path, now.strftime("%d%m%Y_%H-%M-%S")+".jpg")
    dir = dir.replace("\\", "/")
    print("Image Saved at " + dir)
    cv2.imwrite(dir, image)
    return dir

def remove_background_fs(path):
    """
    Title: Remove Background (Foreground segmentation)
    Description: This function will remove the background of an image (ie isolate the sample).
    Inputs: Image
    Outputs: path of the inputed image with its background removed.
    """
    # path to input image specified and
    # image is loaded with imread command
    image = cv2.imread(path)

    # create a simple mask image similar
    # to the loaded image, with the
    # shape and return type
    mask = np.zeros(image.shape[:2], np.uint8)

    # specify the background and foreground model
    # using numpy the array is constructed of 1 row
    # and 65 columns, and all array elements are 0
    # Data type for the array is np.float64 (default)
    backgroundModel = np.zeros((1, 65), np.float64)
    foregroundModel = np.zeros((1, 65), np.float64)

    # define the Region of Interest (ROI)
    # as the coordinates of the rectangle
    # where the values are entered as
    # (startingPoint_x, startingPoint_y, width, height)
    # these coordinates are according to the input image
    # it may vary for different images
    rectangle = (265, 330, 216, 98)

    # apply the grabcut algorithm with appropriate
    # values as parameters, number of iterations = 3
    # cv2.GC_INIT_WITH_RECT is used because
    # of the rectangle mode is used
    cv2.grabCut(image, mask, rectangle,
                backgroundModel, foregroundModel,
                3, cv2.GC_INIT_WITH_RECT)

    # In the new mask image, pixels will
    # be marked with four flags
    # four flags denote the background / foreground
    # mask is changed, all the 0 and 2 pixels
    # are converted to the background
    # mask is changed, all the 1 and 3 pixels
    # are now the part of the foreground
    # the return type is also mentioned,
    # this gives us the final mask
    mask2 = np.where((mask == 2)|(mask == 0), 0, 1).astype('uint8')

    # The final mask is multiplied with
    # the input image to give the segmented image.
    src = image * mask2[:, :, np.newaxis]
    # Convert image to image gray
    tmp = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)

    # Applying thresholding technique
    _, alpha = cv2.threshold(tmp, 0, 255, cv2.THRESH_BINARY)

    # Using cv2.split() to split channels
    # of coloured image
    b, g, r = cv2.split(src)

    # Making list of Red, Green, Blue
    # Channels and alpha
    rgba = [b, g, r, alpha]

    # Using cv2.merge() to merge rgba
    # into a coloured/multi-channeled image
    dst = cv2.merge(rgba, 4)
    cv2.imwrite(path+"removed_back.jpg", dst)
    print("Background Removed and saved to "+path+"removed_back.jpg")
    return path+"removed_back.jpg"

# Determines dominant color of an image
# ref: https://www.delftstack.com/howto/python/opencv-average-color-of-image/#:~:text=NumPy%20in%20Python.-,Use%20the%20average()%20Function%20of%20NumPy%20to%20Find%20the,the%20total%20number%20of%20elements.
def dominant_color(path):
    """
    Title: Dominant Color
    Description: This function will determine the dominant color of an image
    Inputs: Image
    Outputs: Dominant color as RGB list
    """
    image = cv2.imread(path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    reshape_img = image.reshape((image.shape[0] * image.shape[1], 3))

    # Display dominant colors Present in the image
    KM_cluster = KMeans(n_clusters=5).fit(reshape_img)
    C_labels = np.arange(0, len(np.unique(KM_cluster.labels_)) + 1)
    (C_hist, _) = np.histogram(KM_cluster.labels_, bins = C_labels)
    C_hist = C_hist.astype("float")
    C_hist /= C_hist.sum()

    dominant_color = sorted(list(zip(C_hist, KM_cluster.cluster_centers_)))[-2][1]
    # rect_color = np.zeros((50, 300, 3), dtype=np.uint8)
    # img_colors = sorted([(percent, color) for (percent, color) in zip(C_hist, KM_cluster.cluster_centers_)])
    # start = 0
    # for (percent, color) in img_colors:
    #     if (np.array_equal(np.floor(color), [0, 0, 0]) == False):
    #         print(color, "{:0.2f}%".format(percent * 100))
    #         end = start + (percent * 300)
    #         cv2.rectangle(rect_color, (int(start), 0), (int(end), 50), \
    #                      img_colors[-1][1].astype("uint8").tolist(), -1)
    #         start = end
    # cv2.rectangle(rect_color, (int(start), 0), (int(end), 50), \
    #                 img_colors[-1][1].astype("uint8").tolist(), -1)
    # rect_color = cv2.cvtColor(rect_color, cv2.COLOR_RGB2BGR)
    # #cv2.imshow('Source image', cv2.imread("image.jpg"))
    # cv2.imshow('visualize_Color', rect_color)
    # cv2.waitKey(0)
    return np.ceil(dominant_color)

def sample_color(path):
    """
    Title:Image Processing
    Description: This function will find the color of the sample
    Inputs: Original Image Path
    Outputs: Color of sample
    """
    print("Determinig digest colour...")
    image_rb = remove_background_fs(path)
    return dominant_color(image_rb)

def plot_color_change(color_change, times):
    """
    Title: Color change plot
    Description: This function will plot color change over time
    Inputs: color_change: list of list of color change [[c1:rgb], [c2:rgb], ...], and times each color was found
            and the last value being the time of the entire process.
    Outputs: Plot of color change over time
    """
    fig = plt.figure(figsize=(5, 2))
    ax = fig.add_subplot(111)
    for i, color in enumerate(color_change):
        color_norm = color/255
        color_rect = matplotlib.patches.Rectangle((times[i], 0), (times[i+1]-times[i]), 2, color=color_norm)
        ax.add_patch(color_rect)

    plt.xlim([times[0], times[-1]])
    plt.ylim([0, 1])
    plt.tick_params(left = False, right = False , labelleft = False)
    plt.title("Color change of Sample Over Time")
    plt.xlabel("Time (s)")
    plt.show()

def foam_height(path):
    """
    Title: Finds foam height
    Description: This function will measure the height of foam
    Inputs: Image
    Outputs: Foam height
    """
    print("Determining foam height...")
    try:
        # path to input image specified and
        # image is loaded with imread command
        image = cv2.imread(path)

        # create a simple mask image similar
        # to the loaded image, with the
        # shape and return type
        mask = np.zeros(image.shape[:2], np.uint8)

        # specify the background and foreground model
        # using numpy the array is constructed of 1 row
        # and 65 columns, and all array elements are 0
        # Data type for the array is np.float64 (default)
        backgroundModel = np.zeros((1, 65), np.float64)
        foregroundModel = np.zeros((1, 65), np.float64)

        # define the Region of Interest (ROI)
        # as the coordinates of the rectangle
        # where the values are entered as
        # (startingPoint_x, startingPoint_y, width, height)
        # these coordinates are according to the input image
        # it may vary for different images
        rectangle = (255, 328, 215, 55)

        # apply the grabcut algorithm with appropriate
        # values as parameters, number of iterations = 3
        # cv2.GC_INIT_WITH_RECT is used because
        # of the rectangle mode is used
        cv2.grabCut(image, mask, rectangle,
                    backgroundModel, foregroundModel,
                    3, cv2.GC_INIT_WITH_RECT)

        # In the new mask image, pixels will
        # be marked with four flags
        # four flags denote the background / foreground
        # mask is changed, all the 0 and 2 pixels
        # are converted to the background
        # mask is changed, all the 1 and 3 pixels
        # are now the part of the foreground
        # the return type is also mentioned,
        # this gives us the final mask
        mask2 = np.where((mask == 2)|(mask == 0), 0, 1).astype('uint8')

        # The final mask is multiplied with
        # the input image to give the segmented image.
        src = image * mask2[:, :, np.newaxis]
        # Convert image to image gray
        tmp = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
        
        # Grab the alpha pixels above a specified threshold
        alpha_threshold = 190
        mask_arr = np.array(np.greater(np.array(tmp), alpha_threshold), dtype=np.uint8)
        hard_mask = Image.fromarray(np.uint8(mask_arr) * 255, 'L')
        
        # Get the smallest & largest non-zero values in y
        nz = np.nonzero(hard_mask)
        #print(np.max(nz[0]))
        #print(np.min(nz[0]))
        height = abs(np.min(nz[0]) - np.max(nz[0])) # miny minx maxy maxx
        return height * 0.33 # scaling factor from pixel -> mm
    except:
        print("Foam is outside of measureable area")
        return 0

def imageProcessing():
    """
    Title: Image Processing
    Description: This function is a summary function to obtain the image processing values
    Outputs:
        -RGB[0} =       Red RGB Value of the sample colour
        -RGB[1} =       Green RGB Value of the sample colour
        -RGB[2} =       Blue RGB Value of the sample colour
        -foamHeight =   height of the foam in the sample
    """
    path = record_image()
    RGB = sample_color(path)
    print("RGB values of colour digest are")
    print(RGB[0],RGB[1],RGB[2])
    foamHeight = foam_height(path)
    print("Foam height is "+str(foamHeight)+" mm")
    return RGB[0], RGB[1], RGB[2], foamHeight
