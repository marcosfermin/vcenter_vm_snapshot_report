"""
vm_snapshot_report.py

Author: Marcos Fermin

This script connects to vCenter, checks all VMs, and sends a report of
all the remaining snapshots for each VM. It also sends an email if there
are no snapshots found and highlights the snapshots which are older than 24 hours.
"""

import ssl
import smtplib
import datetime
import os
from email.mime.text import MIMEText
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim

# Read the vCenter connection info from the environment variables
vcenter_host = os.environ.get('VCENTER_HOST')
vcenter_user = os.environ.get('VCENTER_USER')
vcenter_password = os.environ.get('VCENTER_PASSWORD')

# Raise an error if any of the vCenter environment variables are not set
if not vcenter_host or not vcenter_user or not vcenter_password:
    raise ValueError("VCENTER_HOST, VCENTER_USER, and VCENTER_PASSWORD environment variables must be set!")

# Email settings
smtp_server = 'your_smtp_server'
smtp_port = 25
sender_email = 'your_sender_email'
receiver_email = 'your_sender_email'


# Establish a connection to vCenter
context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
context.verify_mode = ssl.CERT_NONE
si = SmartConnect(host=vcenter_host, user=vcenter_user, pwd=vcenter_password, sslContext=context)

# Retrieve content and view manager
content = si.RetrieveContent()
view_manager = content.viewManager
container_view = view_manager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)


def recurse_snapshots(snapshot_list):
    """
    Recurse through the list of snapshots and compile snapshot information.
    It also marks the snapshots that are older than 24 hours.
    """
    snapshot_info = ""
    for snapshot in snapshot_list:
        creation_time = snapshot.createTime
        age = datetime.datetime.now(creation_time.tzinfo) - creation_time
        if age > datetime.timedelta(days=1):
            snapshot_info += f"Snapshot Name: {snapshot.name}, Description: {snapshot.description}, Created On: {creation_time}, Age: {age}, *Older than 24 hours*\n"
        else:
            snapshot_info += f"Snapshot Name: {snapshot.name}, Description: {snapshot.description}, Created On: {creation_time}, Age: {age}\n"
        
        # Recurse into child snapshots
        snapshot_info += recurse_snapshots(snapshot.childSnapshotList)
    return snapshot_info


# Iterate through VMs and compile a report for existing snapshots
snapshot_report = ''
for vm in container_view.view:
    if vm.snapshot:
        snapshots_info = recurse_snapshots(vm.snapshot.rootSnapshotList)
        if snapshots_info:
            snapshot_report += f"VM Name: {vm.name}\n{snapshots_info}\n"

# Clean up and disconnect from vCenter
container_view.Destroy()
Disconnect(si)

# Construct and send an email report
subject = 'VM Snapshot Report'
if not snapshot_report:
    snapshot_report = 'No snapshots were found for any VMs.'

msg = MIMEText(snapshot_report)
msg['Subject'] = subject
msg['From'] = sender_email
msg['To'] = receiver_email

with smtplib.SMTP(smtp_server, smtp_port) as server:
    server.send_message(msg)

print('Email has been sent!')
