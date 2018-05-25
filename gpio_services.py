#!/usr/bin/python
RASPBERRY = False
import sys, json, logging

if RASPBERRY == True:
    import RPi.GPIO as GPIO
from time import sleep

WAIT_TIME = 0.2
FREQUENCY = 100
MIN_SPEED = 30
MAX_SPEED = 50
MAX_FORWARD_SPEED = 60
MAX_BACKWARD_SPEED = 40


def read_gpio_conf(field):
    logging.debug('read_gpio_conf')
    with open('gpio_pins.txt') as json_data:
        data = json.load(json_data)
        logging.debug('gpio_pins  data: {}'.format(data))
        json_data.close()
    return data[field]


def gpio_init(gpio_data, pwm_motor):
    logging.debug('gpio_init')
    gpio_data = read_gpio_conf('gpio_pins')
    if RASPBERRY == True:
       GPIO.setmode(GPIO.BOARD)
    logging.warning('GPIO.setmode(GPIO.BOARD)')
    reset_gpio(gpio_data)
    reset_pwm_motor(gpio_data, pwm_motor)
    return (gpio_data, pwm_motor)


def reset_gpio(gpio_data):
    logging.debug('gpio_data')
    for key, val in list(gpio_data.items()):
        if key != 'stop':
            if RASPBERRY == True:
                GPIO.setup(val,GPIO.OUT)
                GPIO.output(val,GPIO.LOW)
            logging.warning('GPIO.setup({}, GPIO.OUT)'.format(val))
            logging.warning('GPIO.output({}, GPIO.LOW)'.format(val))


def reset_pwm_motor(gpio_data, pwm_motor):
    logging.debug('reset_pwm_motor')
    for key, val in list(gpio_data.items()):
        if key in ('enable_dir'):
            if RASPBERRY == True:
                pwm_motor[key] = GPIO.PWM(val, FREQUENCY)
                pwm_motor[key].start(MIN_SPEED)
            logging.warning('pwm_motor[{}] = GPIO.PWM({}, {})'.format(key,val,FREQUENCY))
            logging.warning('pwm_motor[{}].start({})'.format(key, MIN_SPEED))
    return pwm_motor

def control_gpio_car(gpio_data, direction, pwm_motor):
    logging.debug('control_gpio_car')
    res = 'ok'
    if direction == 'forward_dir':
        traction_motor (gpio_data['forward_dir'], gpio_data['backward_dir'], gpio_data['enable_dir'], gpio_data['enable_turn'], pwm_motor, MAX_FORWARD_SPEED)
    elif direction == 'backward_dir':
        traction_motor(gpio_data['backward_dir'], gpio_data['forward_dir'], gpio_data['enable_dir'], gpio_data['enable_turn'], pwm_motor, MAX_BACKWARD_SPEED)
    elif direction == 'turn_right':
        direction_motor(gpio_data['turn_right'], gpio_data['turn_left'], gpio_data['enable_turn'])
    elif direction == 'turn_left':
        direction_motor(gpio_data['turn_left'], gpio_data['turn_right'], gpio_data['enable_turn'])
    elif direction == 'stop':
        control_stop(gpio_data, pwm_motor)
    else:
        res = 'not_ok'
    logging.debug('activate direction {}'.format(direction))
    return res

# def control_gpio(on_pin, off_pin, enable):
#     logging.debug('control_gpio')
#     if RASPBERRY == True:
#         GPIO.output(on_pin, GPIO.HIGH)
#         GPIO.output(off_pin, GPIO.LOW)
#         GPIO.output(enable, GPIO.HIGH)
#     else:
#         logging.warning('pwm_motor['enable_dir'].ChangeDutyCycle{})'.format(MAX_FORWARD_SPEED))
#         logging.warning('GPIO.output({}, GPIO.HIGH)'.format(on_pin))
#         logging.warning('GPIO.output({}, GPIO.LOW)'.format(off_pin))
#         logging.warning('GPIO.output({}, GPIO.HIGH)'.format(enable))
#     logging.debug('on_pin: {} off_pin: {} enable_pin: {}'.format(on_pin, off_pin, enable))


def traction_motor(on_pin, off_pin, enable_pin, disable_pin, pwm_motor, speed):
    logging.debug('traction_motor')
    if RASPBERRY == True:
        pwm_motor['enable_dir'].ChangeDutyCycle(speed)
        GPIO.output(on_pin, GPIO.HIGH)
        GPIO.output(off_pin, GPIO.LOW)
        GPIO.output(enable_pin, GPIO.HIGH)
        GPIO.output(disable_pin, GPIO.LOW)
    logging.warning('GPIO.output({}, GPIO.HIGH)'.format(on_pin))
    logging.warning('GPIO.output({}, GPIO.LOW'.format(off_pin))
    logging.warning('GPIO.output({}, GPIO.HIGH'.format(enable_pin))
    logging.warning('GPIO.output({}, GPIO.LOW'.format(disable_pin))


def direction_motor(on_pin, off_pin, enable_pin):
    logging.debug('direction_motor')
    if RASPBERRY == True:
        GPIO.output(on_pin, GPIO.HIGH)
        GPIO.output(off_pin, GPIO.LOW)
        GPIO.output(enable_pin, GPIO.HIGH)
    logging.warning('GPIO.output({}, GPIO.HIGH)'.format(on_pin))
    logging.warning('GPIO.output({}, GPIO.LOW)'.format(off_pin))
    logging.warning('GPIO.output({}, GPIO.HIGH)'.format(enable_pin))


def control_stop(gpio_data, pwm_motor):
    logging.debug('control_stop')
    for key, val in list(gpio_data.items()):
        if key in ('forward_dir', 'backward_dir', 'enable_dir', 'turn_left', 'turn_right', 'enable_turn'):
            if RASPBERRY == True:
                GPIO.output(val, GPIO.LOW)
            logging.info('GPIO.output({}, GPIO.LOW)'.format(val))
    logging.info('Terminating manual driving functions')


def gpio_terminate():
    logging.debug('gpio_terminate')
    if RASPBERRY == True:
        GPIO.cleanup()
    logging.warning('GPIO.cleanup')
