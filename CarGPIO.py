import json

FREQUENCY = 100
MIN_SPEED = 0
MAX_SPEED = 100

def read_gpio_conf(field):
	with open('gpio_pins.txt') as json_data:
		data = json.load(json_data)
		json_data.close()
	return data[field]

def gpio_init(gpio_data, pwm_motor, RASPBERRY):
	gpio_data = read_gpio_conf('gpio_pins')
	if RASPBERRY == True:
	   GPIO.setmode(GPIO.BOARD)
	reset_gpio(gpio_data, RASPBERRY)
	reset_pwm_motor(gpio_data, pwm_motor, RASPBERRY)
	return (gpio_data, pwm_motor)

def reset_gpio(gpio_data, RASPBERRY):
	for key, val in list(gpio_data.items()):
		if key != 'stop':
			if RASPBERRY == True:
				GPIO.setup(val,GPIO.OUT)
				GPIO.output(val,GPIO.LOW)

def reset_pwm_motor(gpio_data, pwm_motor, RASPBERRY):
	for key, val in list(gpio_data.items()):
		if key in ('enable_dir'):
			if RASPBERRY == True:
				pwm_motor[key] = GPIO.PWM(val, FREQUENCY)
				pwm_motor[key].start(MIN_SPEED)
	return pwm_motor