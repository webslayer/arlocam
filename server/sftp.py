import os
from io import BytesIO

import paramiko
import requests
from PIL import Image


class SFTP:
    """sftp utils"""

    # Open a transport
    host = os.getenv("SFTP_HOST")
    port = 22

    # Auth
    username = os.getenv("SFTP_USER")
    password = os.getenv("SFTP_PASS")

    remote_snaphot_path = "/silverene/wp-content/uploads/snapshots/"
    remote_timelapse_path = "/silverene/wp-content/uploads/timelapse/"

    def __init__(self):
        self.transport = paramiko.Transport((self.host, self.port))
        self.transport.connect(None, self.username, self.password)
        self.sftp = paramiko.SFTPClient.from_transport(self.transport)

    def upload_snaphot(self, url, filename):
        """upload snapshot from url with compression

        Args:
            url (str): image url
            filename (str): fileName to upload

        Returns:
            SFTPAttributes: an SFTPAttributes object containing attributes about the uploaded file.
        """

        req_for_image = requests.get(url)
        # file_object_from_req = req_for_image.raw
        IMAGE_FILE = BytesIO(req_for_image.content)

        img = Image.open(IMAGE_FILE)
        # here, we create an empty string buffer
        buffer = BytesIO()
        img.save(buffer, "JPEG", quality=60)
        buffer.seek(0)
        print("compressed")

        # Do the actual upload
        file_attr = self.sftp.putfo(buffer, self.remote_snaphot_path + filename)

        return file_attr
