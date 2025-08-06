#!/bin/bash
set -e

# ------------------------------------
# Update and Install apps
# ------------------------------------
echo "[*] Updating and installing system packages."
apt update -y
apt install -y python3 python3-flask hostapd dnsmasq dhcpcd5

# ------------------------------------
# Moving JackAttack.py to opt
# ------------------------------------
echo "[*] Setting up web app directory."
mkdir -p /opt/jackattack/templates
mkdir -p /opt/jackattack/static
mkdir -p /opt/jackattack/scripts

cp jackattack.py /opt/jackattack/jackattack.py
cp static/style.css /opt/jackattack/static/
cp templates/* /opt/jackattack/templates/
cp scripts/* /opt/jackattack/scripts/
chmod +x /opt/jackattack/jackattack.py

# ------------------------------------
# USB Gadget: Persistent Boot Support
# ------------------------------------

echo "[*] Creating USB gadget boot script."
mkdir -p /opt/jackattack

cat << 'EOF' > /opt/jackattack/setup_gadget.sh
#!/bin/bash
set -e
modprobe libcomposite

UDC=$(ls /sys/class/udc | head -n 1)
GADGET_DIR=/sys/kernel/config/usb_gadget/g1

# Clean up old gadget
if [ -d "$GADGET_DIR" ]; then
    echo "" > $GADGET_DIR/UDC || true
    find $GADGET_DIR/configs/c.1 -type l -exec rm -f {} \; || true
    rm -rf $GADGET_DIR/functions/* || true
    rm -rf $GADGET_DIR/configs/* || true
    rm -rf $GADGET_DIR/strings/* || true
    rm -rf $GADGET_DIR || true
fi

# Create new gadget
mkdir -p $GADGET_DIR
cd $GADGET_DIR

echo 0x1d6b > idVendor
echo 0x0104 > idProduct
echo 0x0100 > bcdDevice
echo 0x0200 > bcdUSB
echo 0xEF > bDeviceClass
echo 0x02 > bDeviceSubClass
echo 0x01 > bDeviceProtocol
echo 0x40 > bMaxPacketSize0

mkdir -p strings/0x409
echo "deadbeef1234" > strings/0x409/serialnumber
echo "JackAttack" > strings/0x409/manufacturer
echo "Composite Gadget" > strings/0x409/product

mkdir -p configs/c.1/strings/0x409
echo "Config 1" > configs/c.1/strings/0x409/configuration
echo 120 > configs/c.1/MaxPower

# HID Function
mkdir -p functions/hid.usb0
echo 1 > functions/hid.usb0/protocol
echo 1 > functions/hid.usb0/subclass
echo 8 > functions/hid.usb0/report_length
echo -ne '\x05\x01\x09\x06\xa1\x01\x05\x07\x19\xe0\x29\xe7\x15\x00\x25\x01\x75\x01\x95\x08\x81\x02\x95\x01\x75\x08\x81\x01\x95\x05\x75\x01\x05\x08\x19\x01\x29\x05\x91\x02\x95\x01\x75\x03\x91\x01\x95\x06\x75\x08\x15\x00\x25\x65\x05\x07\x19\x00\x29\x65\x81\x00\xc0' > functions/hid.usb0/report_desc

# ECM Function
mkdir -p functions/ecm.usb0
echo "02:42:c0:a8:00:01" > functions/ecm.usb0/dev_addr
echo "02:42:c0:a8:00:02" > functions/ecm.usb0/host_addr

ln -s functions/hid.usb0 configs/c.1/
ln -s functions/ecm.usb0 configs/c.1/

# Bind
for attempt in {1..10}; do
    echo "$UDC" > UDC 2>/dev/null && break
    sleep 1
done
EOF

chmod +x /opt/jackattack/setup_gadget.sh

echo "[*] Creating systemd service for USB gadget setup."
cat << EOF > /etc/systemd/system/jackgadget.service
[Unit]
Description=USB Gadget Setup for JackAttack
Before=jackattack.service
After=network.target
DefaultDependencies=no

[Service]
ExecStart=/opt/jackattack/setup_gadget.sh
Type=oneshot
RemainAfterExit=true

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable jackgadget.service

# ------------------------------------
# Flask App Systemd Service
# ------------------------------------

echo "[*] Creating systemd service for JackAttack."
cat << EOF > /etc/systemd/system/jackattack.service
[Unit]
Description=JackAttack Web UI
After=network.target jackgadget.service

[Service]
ExecStart=/usr/bin/python3 /opt/jackattack/jackattack.py
WorkingDirectory=/opt/jackattack
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable jackattack.service
systemctl start jackattack.service

# ------------------------------------
# Access Point setup
# ------------------------------------
echo "[+] Stopping and disabling interfering services."
systemctl stop wpa_supplicant.service || true
systemctl disable wpa_supplicant.service || true
systemctl mask wpa_supplicant.service || true

if systemctl list-units --full -all | grep -q NetworkManager.service; then
    echo "[+] Disabling NetworkManager."
    systemctl stop NetworkManager.service
    systemctl disable NetworkManager.service
    systemctl mask NetworkManager.service
fi

echo "[+] Adding persistent static IP to /etc/dhcpcd.conf"
grep -q "^interface wlan0" /etc/dhcpcd.conf || tee -a /etc/dhcpcd.conf > /dev/null <<EOF

interface wlan0
static ip_address=10.0.3.14/24
nohook wpa_supplicant
EOF

echo "[+] Clearing existing dnsmasq config."
mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig || true

echo "[+] Creating dnsmasq config for DHCP."
tee /etc/dnsmasq.conf > /dev/null <<EOF
interface=wlan0
dhcp-range=10.0.3.20,10.0.3.26,255.255.255.0,24h
EOF

echo "[+] Creating hostapd config for WPA2 AP."
tee /etc/hostapd/hostapd.conf > /dev/null <<EOF
interface=wlan0
driver=nl80211
ssid=JackAttack
hw_mode=g
channel=6
wmm_enabled=1
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=jackattack
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
max_num_sta=7
EOF

echo "[+] Linking hostapd config to default."
echo 'DAEMON_CONF="/etc/hostapd/hostapd.conf"' | tee /etc/default/hostapd

echo "[+] Bringing up wlan0 with static IP."
ip link set wlan0 down || true
ip addr flush dev wlan0
ip addr add 10.0.3.14/24 dev wlan0
ip link set wlan0 up

sleep 2

echo "[+] Restarting services."
systemctl unmask hostapd
systemctl enable hostapd
systemctl restart hostapd

systemctl enable dnsmasq
systemctl restart dnsmasq

#echo '@reboot root sleep 30 && ip addr add 10.0.3.14/24 dev wlan0' >> /etc/crontab
echo "@reboot root sleep 30 && ip addr show wlan0 | grep -q '10.0.3.14' || ip addr add 10.0.3.14/24 dev wlan0" >> /etc/crontab

# ------------------------------------
# Cleanup
# ------------------------------------
# Removes personal SSID and PASSPHRASE from first boot
rm -f /etc/NetworkManager/system-connections/preconfigured.nmconnection
echo "[+] Setup complete. Reboot recommended."
reboot
