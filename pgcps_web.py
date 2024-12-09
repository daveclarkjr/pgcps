from flask import Flask, render_template, request
import paramiko
import re

# Function to execute a command over SSH and return the output
def execute_command(ssh_client, command):
    stdin, stdout, stderr = ssh_client.exec_command(command)
    return stdout.read().decode('utf-8')

# Function to parse the "show interface brief" output
def get_up_interfaces(output):
    up_interfaces = []
    lines = output.splitlines()
    for line in lines:
        match = re.search(r'(\S+)\s+\S+\s+\S+\s+\S+\s+yes\s+up\s+\S+\s+\S+', line)
        if match:
            up_interfaces.append(match.group(1))
    return up_interfaces

# Function to check MAC addresses on a specific interface
def has_no_mac_address(output):
    return "No MAC entries found." in output

# Flask app
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/check', methods=['POST'])
def check_interfaces():
    hostname = request.form['hostname']
    username = request.form['username']
    password = request.form['password']

    result = []

    try:
        # Establish SSH connection
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, username=username, password=password)

        # Get interfaces with status "up"
        interface_output = execute_command(ssh, "show interface brief")
        up_interfaces = get_up_interfaces(interface_output)

        # Check each "up" interface for MAC addresses
        for interface in up_interfaces:
            mac_output = execute_command(ssh, f"show mac-address-table interface {interface}")
            if has_no_mac_address(mac_output):
                result.append(f"Interface {interface} is 'up' but has no MAC addresses.")

        # Close the SSH connection
        ssh.close()

    except Exception as e:
        result.append(f"An error occurred: {e}")

    return render_template('result.html', result=result)

if __name__ == '__main__':
    app.run(debug=True)