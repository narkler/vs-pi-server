import gpiozero as gpio

from signal import pause
from pathlib import Path
from RPLCD.i2c import CharLCD

import threading
import subprocess
import time

# Change this to the path of your server
# If you ran the install script, the default path is: "/home/user/vintagestory"

vs_path = "/home/server/vs_server"

# Change this to the path of your main server log
# Logs are typically located in "/home/user/.config/VintagestoryData/Logs"

vslog_path = "/home/server/.config/VintagestoryData/Logs/server-main.log"

server_running = False # Running means the server is on but still starting
server_operational = False # Operational means the server is fully running and players can join
shutdownqueued = False
plrcount = 0

# Change the numbers to the GPIO pins your components are on

# If you aren't using any components, just leave it as it, but
# make sure all of the unused components aren't using any of the
# active components same gpio, since they are still "active" and sending signals

# This also means you shouldn't have this script running if you are doing any wiring / adding more external components

statusled = gpio.LED(6)
overloadled = gpio.PWMLED(5)
startbutton = gpio.Button(26)
queuedshutdownled = gpio.LED(22)

lcd = CharLCD('PCF8574', 0x27)
lcd.clear()

# The event listener constantly checks the main log file for the specificed words
# If the line has "Dedicated Server now running", it can run code, like printing the line

def eventlistener():
	global server_operational, server_running, shutdownqueued, plrcount

	process = subprocess.Popen(
		["tail", "-n", "0", "-F", vslog_path],
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE,
		text=True,
		bufsize=1
	)

	while True:
		if not server_running:
			break

		line = process.stdout.readline().strip()

		if not line:
			continue

		if "Dedicated Server now running" in line:
			print(line) # Prints the whole line
			server_operational = True

			statusled.on()

			usageannouncer = threading.Thread(target=announce_usage, daemon=True)
			usageannouncer.start()
			# ^^^ Comment these two lines out if you don't want gpu / cpu usage to be announced in chat

			DisplayMethods.running()
			DisplayMethods.tickplayercounter()
			
		if "overloaded" in line:
			print(f"\033[31m{line}\033[0m")

			led_blink = threading.Thread(target=ledblink, args=(overloadled, 2), daemon=True)
			led_blink.start()

		if "Stopped the server!" in line:
			shutdownqueued=False
			server_operational, server_running = False, False

			statusled.off()
			overloadled.off()
			queuedshutdownled.off()
			DisplayMethods.inactive()
			DisplayMethods.clearplayercounter()

			print("Server successfully shutdown")

		if "Loaded" in line or "Starting world" in line:
			print(f"\033[94m{line}\033[0m")

		if "pausing game" in line or "resuming game" in line:
			print(f"\033[33m{line}\033[0m")

		if "joins." in line:
			print(f"\033[95m{line}\033[0m")
			plrcount += 1
			DisplayMethods.tickplayercounter()
		elif "left." in line:
			print(f"\033[95m{line}\033[0m")
			plrcount -= 1
			DisplayMethods.tickplayercounter()
		time.sleep(0.1)

playercounter_pos = (1,0)
status_pos = (0,0)
messages = {
    "inactive_msg": "Server inactive ",
    "starting_msg": "Server starting!",
    "running_msg": "Server running  ",
    "queued_msg": "Shutdown queued "
}

# All the functions you can use to write a built-in message to the lcd at the given position

class DisplayMethods:
	def tickplayercounter(): # Updates the lcd with the current player count when called
		lcd.cursor_pos = playercounter_pos
		lcd.write_string(f"Player count: {plrcount}")
	def clearplayercounter():
		lcd.cursor_pos = playercounter_pos
		lcd.write_string("                ")
	def inactive():
		lcd.cursor_pos = status_pos
		lcd.write_string(messages["inactive_msg"])
	def starting():
		lcd.cursor_pos = status_pos
		lcd.write_string(messages["starting_msg"])
	def running():
		lcd.cursor_pos = status_pos
		lcd.write_string(messages["running_msg"])
	def queued():
		lcd.cursor_pos = status_pos
		lcd.write_string(messages["queued_msg"])
DisplayMethods.inactive()

# Functions to calculate gpu / cpu usage

def gpu_usage():
		clock_speed = subprocess.run(
			["vcgencmd", "measure_clock", "core"],
			stdout=subprocess.PIPE,
			text=True
		)
		clock_speed = int(clock_speed.stdout.split("=")[1]) / 1000000
		gpu_usage = (clock_speed / 500) * 100
		return int(gpu_usage)
def cpu_usage():
		clock_speed = subprocess.run(
		["vcgencmd", "measure_clock", "arm"],
		stdout=subprocess.PIPE,
		text=True,
		)
		clock_speed = int(clock_speed.stdout.split("=")[1]) / 1000000
		cpu_usage = (clock_speed / 1500) * 100
		return int(cpu_usage)

# Announces the gpu and cpu usage in chat if it's over 60%

def announce_usage():
	while True:
		if not server_operational:
			break
		gpu = gpu_usage()
		cpu = cpu_usage()
		if cpu >= 60 or cpu >= 60:
			subprocess.run(
				["screen", "-S", "vs_server", "-X", "stuff", f"/announce CPU Usage: {str(cpu)}%, GPU Usage: {str(gpu)}%\n"]
			)
		time.sleep(10)
def startvs():
	global server_running, shutdownqueued
	if shutdownqueued:
		print("Shutdown already queued.")

	if server_operational and not shutdownqueued:
		shutdownqueued=True
		queuedshutdownled.on()

		DisplayMethods.queued()

		print("Shutting down server...")
		stopvs()
		return

	if server_running:
		if not server_operational and not shutdownqueued:
			shutdownqueued=True
			queuedshutdownled.on()

			DisplayMethods.queued()

			print("Queued server shutdown")
			stopvs()
		return

	subprocess.run(["screen", "-S", "vs_server", "-dm", f"{vs_path}/VintagestoryServer"]) # Starts the server
	print("Starting Vintage Story server... Will take \033[33m~2\033[0m mins")
	server_running = True

	event_listener = threading.Thread(target=eventlistener, daemon=True)
	event_listener.start()
	DisplayMethods.starting()
def stopvs():
	subprocess.run(["screen", "-S", "vs_server", "-X", "stuff", "/stop\n"])

blinking = {}
def ledblink(led, amount):
	if blinking.get(led):
		return
	blinking[led] = True
	led.pulse(fade_in_time=0.5, fade_out_time=0.5, n=amount, background=False)
	blinking.pop(led, None)

startbutton.when_pressed = startvs

print(
"\033[94mVintage Story server script running!\033[0m",
"\n\n\033[1mPress the button to start / stop the server\033[0m",
)

pause()
