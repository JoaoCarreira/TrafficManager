RASPBERRY = False
import sys, json
if RASPBERRY == True:
	import RPi.GPIO as GPIO
from time import sleep
import time
import threading

FREQUENCY = 100
MIN_SPEED = 0
MAX_SPEED = 100
MAX_FORWARD_SPEED = 60
MAX_BACKWARD_SPEED =60

def read_gpio_conf(field):
	print('read_gpio_conf')
	with open('gpio_pins.txt') as json_data:
		data = json.load(json_data)
		print('gpio_pins  data: ', data)
		json_data.close()
	return data[field]

def gpio_init(gpio_data, pwm_motor):
	print ('gpio_init')
	gpio_data = read_gpio_conf('gpio_pins')
	if RASPBERRY == True:
	   GPIO.setmode(GPIO.BOARD)
	print('GPIO.setmode(GPIO.BOARD)')
	reset_gpio(gpio_data)
	reset_pwm_motor(gpio_data, pwm_motor)
	return (gpio_data, pwm_motor)

def reset_gpio(gpio_data):
	for key, val in list(gpio_data.items()):
		if key != 'stop':
			if RASPBERRY == True:
				GPIO.setup(val,GPIO.OUT)
				GPIO.output(val,GPIO.LOW)
			print ('GPIO.setup(',val,',GPIO.OUT)')
			print ('GPIO.output(',val,',GPIO.LOW)')

def reset_pwm_motor(gpio_data, pwm_motor):
	for key, val in list(gpio_data.items()):
		if key in ('enable_dir'):
			if RASPBERRY == True:
				pwm_motor[key] = GPIO.PWM(val, FREQUENCY)
				pwm_motor[key].start(MIN_SPEED)
			print ('pwm_motor[',key,'] = GPIO.PWM(',val,',',FREQUENCY,')')
			print ('pwm_motor[',key,'].start(',MIN_SPEED,')')
	return pwm_motor