# This is to import Chrome and ChromeDriver to work

# Install necessary packages
!apt update
!apt install -y wget unzip xvfb

# Install Google Chrome
!wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
!dpkg -i google-chrome-stable_current_amd64.deb
!apt -f install -y  # Install dependencies

# Install Chromedriver using autoinstaller
!pip install chromedriver-autoinstaller pyvirtualdisplay selenium

import chromedriver_autoinstaller
from pyvirtualdisplay import Display

# Automatically install the appropriate ChromeDriver version
chromedriver_autoinstaller.install()

# Start a virtual display
display = Display(visible=0, size=(1920, 1080))
display.start()

# Verify installations
!google-chrome --version
!chromedriver --version