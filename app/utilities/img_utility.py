import base64
import hashlib
import io
import os
import paramiko
from PIL import Image
from dotenv import dotenv_values

nginx_static_service: dict = dotenv_values("./.env.nginx")
asdsad=0
def base64_to_image(image):
    # Assuming base64_str is the string value without 'data:image/jpeg;base64,'
    try:
        os.mkdir('images_saved')
    except:
        pass
    image_checksum = hashlib.md5(image.encode('utf-8')).hexdigest()

    img = Image.open(io.BytesIO(base64.decodebytes(bytes(image, "utf-8"))))
    img.save('images_saved/'+image_checksum+'.png')
    # Set up SSH client

    try:
        ssh = paramiko.SSHClient()

        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        ssh.connect(nginx_static_service['NGINX_HOST'], username=nginx_static_service['NGINX_USERNAME'],password=nginx_static_service['NGINX_PASSWORD'])

        # Transfer the file using SCP
        scp = ssh.open_sftp()
        scp.put('images_saved/'+image_checksum+'.png',nginx_static_service['NGINX_STATIC_DIRECTORY']+'/'+image_checksum+'.png')
        scp.close()
        ssh.close()

    except Exception as ssh_nginx_scp_images_error:
        print("error sending images of guest over ssh using scp: "+str(ssh_nginx_scp_images_error))
    # Close the SSH connection

    os.unlink('images_saved/'+image_checksum+'.png')
    return image_checksum