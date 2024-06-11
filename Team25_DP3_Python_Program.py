## Imports for classes and modules ##

from gpiozero import Buzzer
from gpiozero import Button
from gpiozero import Motor
import time
import sys
from sensor_library import *



''' Data Input Function '''

def input_data(sensor, y_angle_list, z_angle_list, y_accel_list):

    # Calls sensor method calls, collecting x,y,z data point for euler angles and linear acceleration

    euler = sensor.euler_angles()
    accel = sensor.lin_acceleration()

    # Appends the y, z angles and y acceleration to three seperate global lists (initially empty)
    
    y_angle_list.append(euler[1])
    z_angle_list.append(euler[2])
    y_accel_list.append(accel[1])

    # Assigns raw y,z angles and y acceleration to variables within a raw data list

    raw_y_angle = round(euler[1],2)
    raw_z_angle = round(euler[2],2)
    raw_y_accel = round(accel[1],2)

    raw_data = [raw_y_angle, raw_z_angle, raw_y_accel]

    time.sleep(0.5)

    return raw_data



''' Rolling Average '''
    ##Calculates the rolling average over n=5 most recent data points

def rolling_avg(y_angle_list, z_angle_list, y_accel_list):     

    n = 5

    # When the length of the global lists are less than 5, averages aren't calculated
    
    if len(y_angle_list) < n:
        avgs = None

    # When the length of the global lists are equal to 5:
    ## Calculates the rounded averages and removes the first (oldest) data point from the lists
        
    elif len(y_angle_list) == n:

        y_angle_avg = round(sum(y_angle_list)/n, 2)
        z_angle_avg = round(sum(z_angle_list)/n, 2)
        y_accel_avg = round(sum(y_accel_list)/n, 2)
        
        y_angle_list.remove(y_angle_list[0])
        z_angle_list.remove(z_angle_list[0])
        y_accel_list.remove(y_accel_list[0])

        avgs = [y_angle_avg, z_angle_avg, y_accel_avg]

    return avgs



''' Airbag Function '''
    ## Compares y acceleration to predetermined threshold to detect a fall, and if so, signals a motor
    ##(This output device is a placeholder; the real output would release compressed air to inflate a protective belt)
        
def airbag(avgs):

    button_obj = Button(15)
    motor_obj = Motor(forward=16, backward=12)
    airbag_status = 'Off'

    # When there are less than 5 data points and the average isn't calculated, the motor stays off
    
    if avgs == None:
        return airbag_status

    ## Threshold ##

    y_accel_avg = avgs[2]
    accel_thresh = -0.5

    # When the averages are calculated:
    ## If the y acceleration is above a predetermined threshold and the button is held, the motor does not turn on
    ## If the y acceleration is above a predetermined threshold, but the button is NOT pressed, the motor turns on for 5 seconds
    
    if y_accel_avg < accel_thresh and button_obj.is_pressed: 
        print('\n' + "Button is held. Airbag will NOT inflate" + '\n')
    
    elif y_accel_avg < accel_thresh and not button_obj.is_pressed:
        motor_obj.forward()
        airbag_status = 'On'
        print('\n' + "Airbag is inflating" + '\n')
        time.sleep(1)
    
    return airbag_status



''' Buzzer Function '''
    ## Calculates change in angle of 2 most recent average calculations and compares to threshold values to signal buzzer
    ## Calculating the change in angle can help avoid catching regular head movements

def buzzer(avgs,delta_y_ang,delta_z_ang):

    button_obj = Button(15)
    buzzer_obj = Buzzer(18)
    buzzer_obj.off()
   
    buzzer_status = 'Off'

    m = 2

    ## Thresholds

    ang_thresh = 7
    accel_thresh = -1

    # When there are less than 5 data points and the average isn't calculated, the buzzer is off
    
    if avgs == None:
        return buzzer_status

    # As averages are calculated:
    ## Appends angle averages to two global lists (initially empty) that are used to calculate the change in angle between the 2 previous averages

    # When the length of the two global lists are less than 2:
    ## Appends y and z angle averages to the lists and the buzzer stays off

    y_ang_avg = avgs[0]
    z_ang_avg = avgs[1]
    y_accel_avg = avgs[2]
    
    if len(delta_y_ang) < m:
        delta_y_ang.append(y_ang_avg)
        delta_z_ang.append(z_ang_avg)

    # When the length of the two lists are equal to 2:
    ## Calculates the absolute value of the difference, removes the first (older) averages, and appended newer averages

    elif len(delta_y_ang) == m:

        delta_y = abs(delta_y_ang[-1] - delta_y_ang[0])
        delta_z = abs(delta_z_ang[-1] - delta_z_ang[0])
        
        delta_y_ang.remove(delta_y_ang[0])
        delta_y_ang.append(y_ang_avg)
        
        delta_z_ang.remove(delta_z_ang[0])
        delta_z_ang.append(z_ang_avg)

        ## If the sensor is accelerating down (i.e. user is falling), the buzzer conditions are passed and do not run
        ## If button is being held, the buzzer conditions are passed and do not run
        ## If the change in angle is greater than the threshold, the buzzer turns on to signal potential head drooping

        if y_accel_avg < accel_thresh or button_obj.is_pressed:
            pass

        elif (delta_y > ang_thresh or delta_z > ang_thresh):
            buzzer_obj.on()
            buzzer_status = 'On'
            print('\n' + "Head is drooping. Buzzer is ON.\nPress button to turn buzzer OFF" + '\n')

            # While the buzzer is on:
            ## If the button is pressed, the buzzer turns off and breaks from the loop (the user must hold the button when lifting head back up)
            ## If the button is not pressed, the buzzer stays on for 1 second and then turns off (creating an alarm) -- this will repeat  until the rolling average stabilizes. 

            start = time.time()

            while buzzer_status == 'On':                
                if button_obj.is_pressed:
                    buzzer_obj.off()
                    print('\n' + "Button pressed. Buzzer OFF. Hold button for 5 seconds while lifting head up." + '\n\n')
                    break
                elif time.time() - start >= 1:
                    buzzer_obj.off()
                    break

    return buzzer_status



''' Text File Function '''

def text(raw_data, avgs, buzzer_status, airbag_status):

    # Assigns raw data angle and accel values to seperate lists and converts them into strings

    angle_raw = str((raw_data[0], raw_data[1]))
    accel_raw = str(raw_data[2])

    # When there are less than 5 data points and the average isn't calculated:
    ## Assigns the string "None" to both average angles and acceleration

    if avgs == None:
        angle_avg = "None"
        accel_avg = "None"

    # When the averages are calculated:
    ## Assigns average angles and acceleration values into seperate lists((y,z) and (y) respectively) and converts them into strings

    else:
        angle_avg = str((avgs[0], avgs[1]))
        accel_avg = str(avgs[2])

    ## All relevant textfile data in organized into a list and appended to Sensor_Data text file
    
    text_data = [angle_raw,angle_avg,accel_raw,accel_avg,buzzer_status,airbag_status]
    
    with open('Sensor_Data.txt', 'a') as f:
        f.write(f'{text_data[0]:<21}{text_data[1]:<21}{text_data[2]:<19}{text_data[3]:<19}{text_data[4]:<12}{text_data[5]:<12}' + '\n')
     
    return text_data



''' Main Function '''

def main():

    # Opens Sensor_Data text file in write mode and organizes headers

    heading = ['Angle_Raw_(y,z)','Angle_Avg_(y,z)','Accel_Raw_(y)','Accel_Avg_(y)','Buzzer','Airbag']

    with open('Sensor_Data.txt', 'w') as f:
        f.write(f'{heading[0]:<21}{heading[1]:<21}{heading[2]:<19}{heading[3]:<19}{heading[4]:<12}{heading[5]:<12}' + '\n\n')

    # Initialized orientation sensor

    sensor = Orientation_Sensor()

    # Global Variables #

    y_angle_list = []
    z_angle_list = []
    y_accel_list = []

    delta_y_ang = []
    delta_z_ang = []

    airbag_status = "Off"
    buzzer_status = "Off"

    # Inputs data for 7 iterations to smooth out inital fluctuations in the data as the sensor is initializing
    ## Data is printed in the Python Shell as well
    
    print("Initializing sensor" + '\n')

    with open(r'Sensor_Data.txt', 'r') as f:
        first_line = f.readline() 
        print(first_line)
    
    for i in range(7):
        raw_data = input_data(sensor, y_angle_list, z_angle_list, y_accel_list)
        avgs = (rolling_avg(y_angle_list, z_angle_list, y_accel_list))
        text_data = text(raw_data, avgs, buzzer_status, airbag_status)

        with open(r'Sensor_Data.txt', 'r') as f:
            for last_line in f:
                pass
        print(last_line)
            
    print("Sensor initialized. Output devices now active." + '\n')

    #Once initialized, the functions above loop infintitely
    ## Again, data is printed in the Python Shell

    with open(r'Sensor_Data.txt', 'r') as f:
        first_line = f.readline() 
        print(first_line)
    
    while True:
        raw_data = input_data(sensor, y_angle_list, z_angle_list, y_accel_list)
        avgs = rolling_avg(y_angle_list, z_angle_list, y_accel_list)
        airbag_status = airbag(avgs)
        buzzer_status = buzzer(avgs, delta_y_ang, delta_z_ang)
        text(raw_data, avgs, buzzer_status, airbag_status)

        with open(r'Sensor_Data.txt', 'r') as f:
            for last_line in f:
                pass
        print(last_line)
