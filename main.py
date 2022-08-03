#Spin servo @Dylan 
import RPi.GPIO as GPIO
from time import sleep

gpio_num=11 #Can change??

GPIO.setmode(GPIO.BOARD)
GPIO.setup(gpio_num, GPIO.OUT)
pwm=GPIO.PWM(gpio_num, 50) #Second parameter = freq.
pwm.start(0)

def setAngle(angle):
    duty = angle / 18 + 3
    GPIO.output(gpio_num, True)
    pwm.ChangeDutyCycle(duty)
    sleep(1)
    GPIO.output(gpio_num, False)
    pwm.ChangeDutyCycle(duty)

#Take an image with PiCam @Calvin Medeira 
#Read load sensor @pat 

# must do "pip install hx711-rpi-py==1.57.0" first 
# rpi gpio has to be also installed
from HX711 import *

hx = SimpleHX711(2, 3, -370, -367471)
hx.zero()
while True:
  print(hx.weight(35))


compensation = 0
def readLS():
    value=0 #fix this
    return value
#Calibrate load sensor @Harry 
def calibrateLS():
    compensation = readLS()

#Read IMU @Kaelan

#Process image