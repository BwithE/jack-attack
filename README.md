# Jack-Attack

Jack-Attack is a web application designed to run on a Raspberry Pi Zero configured as a USB HID gadget.  

Jack-Attack was created for research inspired by P4wnP1.

It allows sending custom keyboard keystrokes and key combinations via a web interface, making it ideal for automation, testing, or DIY USB keyboard projects.

---

## DISCLAIMER
Jack-Attack is not made for illegal purposes. Use at your own RISK, preferrably with PERMISSION.

---
## Features

- Send single keys, key combos (e.g. `CTRL+ALT+DEL`, `GUI+SPACE` for macOS Spotlight)
- Supports special keys: ENTER, ESC, BACKSPACE, TAB, SPACE, function keys, modifiers (CTRL, SHIFT, ALT, GUI)
- Custom delay commands, e.g. `DELAY 2` to wait 2 seconds between key presses
- Web UI for easy input and sending of keystrokes
- Runs as a web server on port 80, accessible on your local network
- Configures Raspberry Pi Zero as both USB HID gadget and Wi-Fi Access Point (SSID: `JackAttack`)

---

## Requirements

- Raspberry Pi Zero (configured for USB HID gadget and Wi-Fi AP)
- USB Dongle Breakout Board

---

## Automated Setup Script

A setup script is included to automate system preparation, USB gadget configuration, and service setup.

### What the setup script does:

- Updates the system and installs required packages:
  - `python3`, `python3-flask`, `hostapd`, `dnsmasq`, `dhcpcd5`
- Copies the web app files to `/opt/jackattack`
- Creates a USB gadget boot script that sets up the HID and ECM USB functions
- Creates and enables a systemd service (`jackgadget.service`) to initialize the USB gadget at boot
- Creates and enables a systemd service (`jackattack.service`) to run the Flask app on startup
- Sets up the Pi as a Wi-Fi Access Point:
  - SSID: `JackAttack`
  - WPA2 passphrase: `jackattack`
  - Static IP: `10.0.3.14`
- Configures and enables `hostapd` and `dnsmasq` for DHCP and Wi-Fi management
- Disables conflicting network services like `wpa_supplicant` and `NetworkManager`

---

## How to Run Setup
1. Using the Raspberry-Pi imager, select the RaspberryPi Zero W

2. Select Raspberry PI OS LITE 32bit

3. Allow the RaspberryPi to associate to your personal network with internet access
  - Recommend creating the username `jackattack` to make it easier for the scripts to work. If not, make sure to change username directories in the `setup.sh` before executing the script.


4. After the SD card has been flashed; in bootfs; add the following to the end of cmdline.txt 
    ```
    modules-load=dwc2
    ```

5. After the SD card has been flashed; in bootfs; replace the contents in config.txt  with the following
    ```
    # Standard Raspberry Pi config
    dtparam=audio=on
    disable_overscan=1
    arm_boost=1

    # Enable DRM VC4 V3D driver (if using video)
    dtoverlay=vc4-kms-v3d
    max_framebuffers=2
    disable_fw_kms_setup=1

    # Enable dwc2 USB Device mode
    [cm4]

    [all]
    dtoverlay=dwc2
    camera_auto_detect=1
    display_auto_detect=1
    auto_initramfs=1
    ```

6. Power on the RasperryPi, and wait for it to connect to your access point

7. Copy the setup script and web app files (`jackattack.py`, `templates/`, `static/`) to your Raspberry Pi Zero.
    ```
    scp -r * jackattack@<IP>:/home/jackattack/
    ```

8. Make sure the setup script is executable:

    ```bash
    chmod +x setup.sh
    ```

9. Run the setup script with root privileges:

    ```bash
    sudo ./setup.sh
    ```

10. The script will configure everything and then reboot the Pi automatically.

---

## Accessing the App

- After reboot, connect to the Wi-Fi Access Point named `JackAttack` using password `jackattack`.
- Access the web interface at:  
  `http://10.0.3.14/`

---

## Usage

- Enter keystrokes in the web form.
- Use key names and combos separated by `+`, e.g.:
    - For MacOS
    ```
    GUI+SPACE
    Hello There.
    DELAY 1
    SPACE What's SPACE up SPACE doc
    ```
    - For Windows
    ```
    GUI+R
    Hello There.
    DELAY 1
    SPACE What's SPACE up SPACE doc
    ```

- `DELAY <seconds>` pauses the typing for the specified number of seconds.
- Press **Send** to transmit the keys over the USB HID interface.

---

## Important Notes

- The app writes HID reports directly to `/dev/hidg0`, created by the USB gadget setup.
- The USB gadget also exposes a network interface (ECM function).
- Use with caution—sending key sequences to connected hosts may cause unexpected behavior.
- You must run the setup script on a Raspberry Pi Zero or compatible device with gadget support.
- Reboot is required after setup to apply all configurations.
