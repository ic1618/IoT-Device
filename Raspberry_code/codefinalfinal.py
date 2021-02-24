import smbus2
from time import sleep,time
from gpiozero import DigitalInputDevice,LED, Button
from signal import pause
import numpy as np
import paho.mqtt.client as mqtt
import json
import ssl

#I/O configuration
red = LED(17)
green= LED(27)
button = Button(18,hold_time=3)

#I2C configuration
bus=smbus2.SMBus(1)

#ADC I2C writing/reading modes
adc_config= smbus2.i2c_msg.write(0x48,[0x01,0x44,0x83])
adc_read= smbus2.i2c_msg.write(0x48,[0x00])
adc_reg=smbus2.i2c_msg.read(0x48,2)

#Temperature sensor I2C modes
tmp_config= smbus2.i2c_msg.write(0x40,[0x02,0x78,0x00])
tmp_read= smbus2.i2c_msg.write(0x40,[0x01])
tmp_reg=smbus2.i2c_msg.read(0x40,2)

#I2C devices configuration
print("initializing")
bus.i2c_rdwr(adc_config)
sleep(0.1)
bus.i2c_rdwr(tmp_config)
sleep(0.1)

#MQTT data
BROKER_ADDRESS="test.mosquitto.org"
N=8884

#Connection to the mqtt broker
client = mqtt.Client()
client.tls_set(ca_certs="mosquitto.org.crt",certfile="client.crt",keyfile="client.key",tls_version=ssl.PROTOCOL_TLSv1_2)
print(client.connect(BROKER_ADDRESS,port=N))
####################
warnings=[" You are bending your wrist too much!"," Please take a break, temperature too high!"," You are shaking, take a break"," Please warm up!"]


#Variable declaration
temperature = 0
voltage = 0
state="idle"
voltages=np.zeros(30)
avg_voltage=0
avg_temperature=37.125
temperatures=np.zeros(30)
counter_array=0
variance=0

#treshold declaration and initialization
bend_tresh=1.6
bend_tresh_low=0
bend_tresh_high=2
# timer represents the time between temperature measurements in seconds, it is initially set to 10 sec
timer=10
start_reset=0
temp_tresh_low=37.0
temp_tresh_high=38.0
#variance tresholds both lower and higher
# they are both needed in order to distinguish from electrical noise and mechanical vibrations
var_tresh_low=0.005
var_tresh_high=0.05

#values that flag the transmission and temperature measurements
send_bool=False
tmp_bool=False

#initial value of the json with warnings
sent_json={
"temperature":0,
"warnings":["Let's start"]
}
i=0

#red LED is on
red.on()

########################
##Function declaration##
########################
#this function converts from bytes to voltage in the case of the ADC
def bend_conv():
    return (int.from_bytes(adc_reg.buf[0],byteorder='big')*256+int.from_bytes(adc_reg.buf[1],byteorder='big'))*0.000063

#this function converts from bytes to voltage in the case of the temperature sensor
def tmp_conv():
    return (int.from_bytes(tmp_reg.buf[0],byteorder='big')*256+int.from_bytes(tmp_reg.buf[1],byteorder='big'))/128

#function that measures the voltage from  the adc through the i2c
def measure_adc():
    bus.i2c_rdwr(adc_read)
    bus.i2c_rdwr(adc_reg)
    sleep(0.03)
    global voltage
    voltage=bend_conv()

#function that measures the temperature from  the TMP006
def measure_tmp():
    bus.i2c_rdwr(tmp_read)
    bus.i2c_rdwr(tmp_reg)
    global temperature
    temperature=tmp_conv()

#the following function checks the values of the temperature and voltage
# it chooses which values to show and when to send data (by changing the value of send_bool)
def checker(temperature,voltage,variance,tmp_bool):
    sent_json["warnings"].clear()
    sent_json["temperature"]=temperature
    global send_bool
    if tmp_bool==True:
        send_bool=True
        if temp_tresh_high<temperature:
            sent_json["warnings"].append(warnings[1])
        elif temp_tresh_low>temperature:
            sent_json["warnings"].append(warnings[3])
    if voltage<bend_tresh:
        sent_json["warnings"].append(warnings[0])
        send_bool=True
    if var_tresh_low<variance<var_tresh_high:
        sent_json["warnings"].append(warnings[2])
        send_bool=True

# this function publishes the json
def send_data():
    load=json.dumps(sent_json)
    client.publish("IC.embedded/TBChip",load)

#the following function is run when the button is held
#it does the reset state of the devices
def hold():
    global state
    state="reset"
    global bend_tresh
    bend_tresh_low=2.0
    bend_tresh_high=1.0
    red.blink(0.1,0.1)
    green.off()
    sleep(0.2)
    time_held=0
    if button.held_time is not None:
        time_held=button.held_time

    while 0<time_held<3 :
        measure_adc()
        bend_tresh_low=min(bend_tresh_low,voltage)
        if button.held_time is None:
            break
        else:
            time_held=button.held_time

    while 6>time_held>3:
        green.on()
        measure_adc()
        bend_tresh_high=max(bend_tresh_high,voltage)
        if button.held_time is None:
            break
        else:
            time_held=button.held_time

    bend_tresh=(bend_tresh_low+bend_tresh_high)/2
    print(bend_tresh)
    state="idle"
    red.on()
    green.off()

# the following function is run when the button is pressed it switches to the idle or measure states
def press():
    global state
    if state=="idle":
        state="measure"
        global start_tmp
        start_tmp=time()
        red.off()
        green.on()
    else:
        state="idle"
        green.off()
        red.on()


#the infinite while loop keeps the device running
while True:
#defines how the measure state is configured
    if state=="measure":
        measure_adc()
        stop_tmp=time()
#checks if it is the time to measure the temperature
        if stop_tmp-start_tmp>timer and i==0:
            tmp_bool=True
            start_tmp=time()
#the following if records the 30 measurements and measures the temperature if it is the case
        if i<30:
            if tmp_bool==True:
                measure_tmp()
                temperatures[i]=temperature
            voltages[i]=voltage
            i=i+1
        else:
#the else does the averaging, variance, checking and transmission

            if tmp_bool==True:
                avg_temperature=np.average(temperatures)
            avg_voltage=np.average(voltages)
            variance=np.var(voltages)
            i=0
            #checks the values and compares them to the tresholds
            checker(avg_temperature,avg_voltage,variance,tmp_bool)
            if send_bool==True:
            #send data
                send_data()
                print(sent_json)
                if tmp_bool==False:
                    green.off()
                send_bool=False
            else:
                green.on()
            # makes tmp_bool false if the temperature was measured
            if tmp_bool==True:
                tmp_bool=False

#defines the functions used for the button
    button.when_held=hold
    button.when_pressed=press
