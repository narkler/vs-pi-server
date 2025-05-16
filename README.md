Tutorial for installing the server (Tested on Raspberry Pi 4):

Install dotnet 7.0 or whichever your version uses, either manually or with this command:

```wget -O - https://raw.githubusercontent.com/pjgpetecodes/dotnet7pi/master/install.sh | sudo bash```

Run the serverinstall script:

```./serverinstall.sh -b BRANCH -v VERSION -d DIRECTORY```
Example:
```./serverinstall.sh -b stable -v 1.20.6 -d /home/pi/vs_server```

Running the server (in the server directory):

```./VintagestoryServer```
