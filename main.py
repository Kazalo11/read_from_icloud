import os
import shutil
import sys

from pyicloud import PyiCloudService

username = input("Enter your username: ")
password = input("Enter your password: ")
album_name = input("Enter the album name")

api = PyiCloudService(username, password)

SAVE_DIR = '/Volumes/CRUMBS_32'
os.makedirs(SAVE_DIR, exist_ok=True)

if api.requires_2fa:
    print("Two-factor authentication required.")
    code = input("Enter the code you received of one of your approved devices: ")
    result = api.validate_2fa_code(code)
    print("Code validation result: %s" % result)

    if not result:
        print("Failed to verify security code")
        sys.exit(1)

    if not api.is_trusted_session:
        print("Session is not trusted. Requesting trust...")
        result = api.trust_session()
        print("Session trust result %s" % result)

        if not result:
            print("Failed to request trust. You will likely be prompted for the code again in the coming weeks")
elif api.requires_2sa:
    import click
    print("Two-step authentication required. Your trusted devices are:")

    devices = api.trusted_devices
    for i, device in enumerate(devices):
        print(
            "  %s: %s" % (i, device.get('deviceName',
            "SMS to %s" % device.get('phoneNumber')))
        )

    device = click.prompt('Which device would you like to use?', default=0)
    device = devices[device]
    if not api.send_verification_code(device):
        print("Failed to send verification code")
        sys.exit(1)

    code = click.prompt('Please enter validation code')
    if not api.validate_verification_code(device, code):
        print("Failed to verify verification code")
        sys.exit(1)

all_files = set()
for root, dirs, files in os.walk(SAVE_DIR):
    for file in files:
        all_files.add(file)
        
for video in api.photos.albums[album_name]:
    destination_file = os.path.join(SAVE_DIR, video.filename)
    if video.filename in all_files:
        print(f"File {video.filename} already exists, skipping download...")
    else:
        print(f"Downloading {video.filename}...")
        download = video.download()
        with open(destination_file, 'wb') as file:
            shutil.copyfileobj(download.raw, file)

