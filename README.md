# Tutorial for installing the server (verified on Raspberry Pi 4):

## Begin by installing dotnet 7.0 or the version required for your setup. This can be done manually or using the following:

```wget -O - https://raw.githubusercontent.com/pjgpetecodes/dotnet7pi/master/install.sh | sudo bash``` 


Download and execute the server installation script:

```./serverinstall.sh -b BRANCH -v VERSION -d DIRECTORY```
> e.g: ```./serverinstall.sh -b stable -v 1.20.6 -d /home/pi/vs_server```

## To run the server (within the server directory):

```./VintagestoryServer```
