If you want to create a dedicated, unmodded server for 2-3 players for Vintage Story on a Raspberry Pi 4 or 5, then it is a surprisingly good option. Here, I have all the files and steps required to install a server. I have also included a Python script that you can use to implement server status LEDs, server start buttons, or an I2C LCD1602 display. Please keep in mind that the Python script is one of my first, so it may not meet typical standards, or be efficient, but hopefully it will be useful or enjoyable to mess around with.

Also please note that, since the pi uses ARM64, mods using harmony patching will not work. This has all only been verified to work on a Raspberry Pi 4

# Tutorial for installing the server (verified on Raspberry Pi 4)

Begin by installing dotnet 7.0 or the version required for your setup. This can be done manually or using the following:

```wget -O - https://raw.githubusercontent.com/pjgpetecodes/dotnet7pi/master/install.sh | sudo bash``` 
> Make you have wget installed if using this method, if you don't simply install it using ```sudo apt install wget```


Download and execute the server installation script:

```./serverinstall.sh -b BRANCH -v VERSION -d DIRECTORY```
> e.g: ```./serverinstall.sh -b stable -v 1.20.6 -d /home/pi/vs_server```

To run the server (within the server directory):

```./VintagestoryServer```

### Getting started with the GPIO script it rather straightforward, all the steps needed to get it working are listed in the script, I just recommend you have some knowledge on python before using it, especially if you want to make modifications.

