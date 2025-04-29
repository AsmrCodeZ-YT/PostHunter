import subprocess
import logging

logging.basicConfig(level=logging.INFO)


class ELK:
    def __init__(self, username, docker_name):
        self.username = username
        self.docker_name = docker_name

    def get_password(self):
        command = [
            "cmd", "/c",
            f"docker exec -i {self.docker_name} "
            f"/usr/share/elasticsearch/bin/elasticsearch-reset-password "
            f"-u {self.username} -s"
        ]
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        output, error = process.communicate(input="Y\n")

        if error:
            logging.error(f"Error while resetting password: {error}")
        else:
            logging.info("Password reset successfully.")

        return output.strip()


    
    def get_certificate(self):
        dest_path = "./data/http_ca.crt"
        command = [
            "docker", "cp",
            f"{self.docker_name}:/usr/share/elasticsearch/config/certs/http_ca.crt",
            dest_path
        ]
        subprocess.run(command, shell=False, check=True)
        logging.info("Certificate copied successfully!")
