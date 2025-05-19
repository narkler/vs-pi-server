## Setting up a Dedicated Vintage Story Server on Raspberry Pi 4/5

Running a dedicated, unmodded Vintage Story server for 2-3 players on a Raspberry Pi 4 or 5 can be a surprisingly viable option. Here you'll find the necessary files and steps to get your server up and running. I've also made a basic python script for implementing server status LEDs, start buttons, or an I2C LCD1602 display, using the GPIO pins.

**Important Considerations:**

* This setup is for an **unmodded** server.
* Due to the Raspberry Pi's ARM64 architecture, **mods using Harmony patching will not work.**
* This tutorial and the provided script have been **verified to work on a Raspberry Pi 4.**

### Tutorial for Installing the Server (Verified on Raspberry Pi 4)

1.  **Install .NET 7.0 (or the required version for your Vintage Story server):**

    You can install this manually or by using the following command:

    ```bash
    wget -O - [https://raw.githubusercontent.com/pjgpetecodes/dotnet7pi/master/install.sh](https://raw.githubusercontent.com/pjgpetecodes/dotnet7pi/master/install.sh) | sudo bash
    ```

    > **Note:** Ensure you have `wget` installed. If not, install it using:
    > ```bash
    > sudo apt install wget
    > ```

2.  **Download and execute the server installation script:**

    ```bash
    ./serverinstall.sh -b BRANCH -v VERSION -d DIRECTORY
    ```

    > **Example:**
    > ```bash
    > ./serverinstall.sh -b stable -v 1.20.6 -d /home/pi/vs_server
    > ```

3.  **To run the server (navigate to your server directory first):**

    ```bash
    ./VintagestoryServer
    ```

### Getting Started with the GPIO Script

The provided Python script aims to add basic hardware interactions to your server. All the necessary steps to get it working are documented within the script itself.

**Recommendation:**

* It's recommended to have some basic understanding of Python, especially if you plan on making modifications to the script.

```python
import gpiozero as gpio
from signal import pause
from RPLCD.i2c import CharLCD
import threading
import subprocess
import time
import os

class ServerController:
	def __init__(self):
		self.vs_path = f"/home/{str(os.getlogin())}/vintagestory" # Set this to the path of your server unless you are using the default install path from the serverinstall.sh script
		self.vslog_path = f"/home/{str(os.getlogin())}/.config/VintagestoryData/Logs/server-main.log" # If you have a custom vs data path, you will have to change this

		self.server_running = False # Running means the server is on but still starting
		self.server_operational = False # Operational means the server is fully running and players can join
		self.shutdownqueued = False
		self.plrcount = 0

		# Set these to use whichever gpio pins you're using for your components, or if you aren't using it just leave it as is
		# Keep in mind every component will still be "active" and the gpio will still be sending signals even if you don't use them
		# This also means you shouldn't run this script while doing any wiring with the gpio pins

		self.statusled = gpio.LED(6)
		self.overloadled = gpio.PWMLED(5)
		self.startbutton = gpio.Button(26, bounce_time=0.1)
		self.queuedshutdownled = gpio.LED(22)
		try:
			self.lcd = CharLCD('PCF8574', 0x27)
			self.lcd.clear()
		except:
			print("No LCD Found")
			self.lcd = None
		if self.lcd:
			# Positions for status and player counter on the lcd screen
			self.playercounter_pos = (1,0) # Row / Column
			self.status_pos = (0,0)
			# Status messages, 16 letters and under usually
			self.messages = {
			"inactive_msg": "Server inactive ",
			"starting_msg": "Server starting!",
			"running_msg": "Server running   ",
			"queued_msg": "Shutdown queued   "
			}
			DisplayMethods.lcd = self.lcd
			DisplayMethods.playercounter_pos = self.playercounter_pos
			DisplayMethods.status_pos = self.status_pos
			DisplayMethods.messages = self.messages
			DisplayMethods.plrcount = self.plrcount
			DisplayMethods.inactive()
		self.blinking = {}
		self.startbutton.when_pressed = self.startvs

	# This function constantly checks the main log file for any specificed lines then executes a function

	def eventlistener(self):
		process = subprocess.Popen(
			["tail", "-n", "0", "-F", self.vslog_path],
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			text=True,
			bufsize=1
		)
		while True:
			if not self.server_running:
				break
			line = process.stdout.readline().strip()
			if not line:
				continue
			if "Dedicated Server now running" in line:
				print(line) # Prints the whole line
				self.server_operational = True
				print(self.server_operational)
				self.statusled.on()
				usageannouncer = threading.Thread(target=self.announce_usage, daemon=True)
				usageannouncer.start()
				if self.lcd:
					DisplayMethods.running()
					DisplayMethods.tickplayercounter()
			if "overloaded" in line:
				print(f"\033[31m{line}\033[0m")
				led_blink = threading.Thread(target=self.ledblink, args=(self.overloadled, 2), daemon=True)
				led_blink.start()
			if "Stopped the server!" in line:
				self.shutdownqueued=False
				self.server_operational, self.server_running = False, False
				self.statusled.off()
				self.overloadled.off()
				self.queuedshutdownled.off()
				if self.lcd:
					DisplayMethods.inactive()
					DisplayMethods.clearplayercounter()
				print("Server successfully shutdown")
			if "Loaded" in line or "Starting world" in line:
				print(f"\033[94m{line}\033[0m")

			if "pausing game" in line or "resuming game" in line:
				print(f"\033[33m{line}\033[0m")

			if "joins." in line:
				print(f"\033[95m{line}\033[0m")
				self.plrcount += 1
				self.lcd and DisplayMethods.tickplayercounter()
			elif "left." in line:
				print(f"\033[95m{line}\033[0m")
				self.plrcount -= 1
				self.lcd and DisplayMethods.tickplayercounter()
			time.sleep(0.1)
	def gpu_usage(self):
			try:
				clock_speed = subprocess.run(
					["vcgencmd", "measure_clock", "core"],
					stdout=subprocess.PIPE,
					text=True
				)
			except:
				print("Failed getting gpu usage")
				return
			clock_speed = int(clock_speed.stdout.split("=")[1]) / 1000000
			gpu_usage = (clock_speed / 500) * 100
			return int(gpu_usage)
	def cpu_usage(self):
			try:
				clock_speed = subprocess.run(
				["vcgencmd", "measure_clock", "arm"],
				stdout=subprocess.PIPE,
				text=True,
				)
			except:
				print("Failed getting cpu usage")
				return
			clock_speed = int(clock_speed.stdout.split("=")[1]) / 1000000
			cpu_usage = (clock_speed / 1500) * 100
			return int(cpu_usage)
	def announce_usage(self):
		while self.server_operational:
			gpu = self.gpu_usage()
			cpu = self.cpu_usage()
			if not cpu or gpu:
				return
			if cpu >= 60 or cpu >= 60:
				try:
					subprocess.run(
						["screen", "-S", "vs_server", "-X", "stuff", f"/announce CPU Usage: {str(cpu)}%, GPU Usage: {str(gpu)}%\n"]
					)
				except:
					return
			time.sleep(10)
	def startvs(self):
		if self.shutdownqueued:
			print("Shutdown already queued.")
			return

		if self.server_operational and not self.shutdownqueued:
			self.shutdownqueued=True
			self.queuedshutdownled.on()
			self.stopvs()

			self.lcd and DisplayMethods.queued()
			print("Shutting down server...")
			return

		if self.server_running:
			if not self.server_operational and not self.shutdownqueued:
				self.shutdownqueued=True
				self.queuedshutdownled.on()
				self.stopvs()

				self.lcd and DisplayMethods.queued()
				print("Queued server shutdown (server still starting)")	
			return
		try:
			subprocess.run(["screen", "-S", "vs_server", "-dm", f"{self.vs_path}/VintagestoryServer"]) # Starts the server
		except:
			print("Failed to run server start command")
			return
		print("Starting Vintage Story server... Will take \033[33m~2\033[0m mins")
		self.server_running = True

		event_listener = threading.Thread(target=self.eventlistener, daemon=True)
		event_listener.start()
		self.lcd and DisplayMethods.starting()
	def stopvs(self):
		try:
			subprocess.run(["screen", "-S", "vs_server", "-X", "stuff", "/stop\n"])
		except:
			print("Failed to run server stop command")
			return
	def ledblink(self, led, amount):
		if self.blinking.get(led):
			return
		self.blinking[led] = True
		led.pulse(fade_in_time=0.5, fade_out_time=0.5, n=amount, background=False)
		self.blinking.pop(led, None)
class DisplayMethods:
	lcd = None
	playercounter_pos = ()
	plrcount = None
	status_pos = ()
	messages = {}

	@classmethod
	def write(cls, pos, msg):
		cls.lcd.cursor_pos = pos
		cls.lcd.write_string(msg)

	@classmethod
	def tickplayercounter(cls): # Updates the lcd with the current player count when called
		cls.lcd.cursor_pos = cls.playercounter_pos
		cls.lcd.write_string(f"Player count: {cls.plrcount}")
	
	@classmethod
	def clearplayercounter(cls):
		cls.write(cls.playercounter_pos, "                ")
	
	@classmethod
	def inactive(cls):
		cls.write(cls.status_pos, cls.messages["inactive_msg"])

	@classmethod
	def starting(cls):
		cls.write(cls.status_pos, cls.messages["starting_msg"])

	@classmethod
	def running(cls):
		cls.write(cls.status_pos, cls.messages["running_msg"])

	@classmethod
	def queued(cls):
		cls.write(cls.status_pos, cls.messages["queued_msg"])

if __name__ == "__main__":
	server_controller = ServerController()
	print("\033[94mVintage Story server script running!\033[0m", "\n\n\033[1mPress the button to start / stop the server\033[0m")
	pause()
