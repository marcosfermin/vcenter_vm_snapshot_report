"""
vm_snapshot_report.py

Author: Marcos Fermin

This script connects to vCenter, checks all VMs, and sends a report of
all the remaining snapshots for each VM. It also sends an email if there
are no snapshots found and highlights the snapshots that are older than 24 hours.
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
receiver_email = 'your_receiver_email'

# Establish a connection to vCenter
context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
context.verify_mode = ssl.CERT_NONE
si = SmartConnect(host=vcenter_host, user=vcenter_user, pwd=vcenter_password, sslContext=context)

# Retrieve content and view manager
content = si.RetrieveContent()
view_manager = content.viewManager
container_view = view_manager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)

def recurse_snapshots(snapshot_list):
    snapshot_info = []
    for snapshot in snapshot_list:
        creation_time = snapshot.createTime
        age = datetime.datetime.now(creation_time.tzinfo) - creation_time
        
        if age > datetime.timedelta(days=1):
            age_str = f"{age} *Older than 24 hours*"
        else:
            age_str = str(age)
            
        snapshot_info.append({
            'name': snapshot.name,
            'description': snapshot.description,
            'created_on': creation_time,
            'age': age_str
        })
        
        # Recurse into child snapshots
        snapshot_info.extend(recurse_snapshots(snapshot.childSnapshotList))
    return snapshot_info

# Build an HTML report
snapshot_data = []
for vm in container_view.view:
    if vm.snapshot:
        snapshots_info = recurse_snapshots(vm.snapshot.rootSnapshotList)
        if snapshots_info:
            for snap in snapshots_info:
                snap['vm_name'] = vm.name
                snapshot_data.append(snap)

# Convert snapshot_data to HTML
if snapshot_data:
    snapshot_report = """
    <style>
        @media only screen and (max-width: 600px) {
            table, thead, tbody, th, td, tr {
                display: block;
            }
            thead tr {
                position: absolute;
                top: -9999px;
                left: -9999px;
            }
            tr { margin: 0 0 1rem 0; }
            td {
                border: none;
                border-bottom: 1px solid #7f8c8d;
                position: relative;
                padding-left: 50%;
            }
            td:before {
                position: absolute;
                top: 0;
                left: 6px;
                width: 45%;
                padding-right: 10px;
                white-space: nowrap;
                content: attr(data-column);
                color: #34495e;
                font-weight: bold;
            }
        }
    </style>
    <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto;">
        <table style="border-collapse: collapse; width: 100%;">
            <thead>
                <tr>
                    <th data-column="VM Name">VM Name</th>
                    <th data-column="Snapshot Name">Snapshot Name</th>
                    <th data-column="Description">Description</th>
                    <th data-column="Created On">Created On</th>
                    <th data-column="Age">Age</th>
                </tr>
            </thead>
            <tbody>
    """
    for snap in snapshot_data:
        snapshot_report += f"""
            <tr>
                <td data-column="VM Name">{snap['vm_name']}</td>
                <td data-column="Snapshot Name">{snap['name']}</td>
                <td data-column="Description">{snap['description']}</td>
                <td data-column="Created On">{snap['created_on']}</td>
                <td data-column="Age">{snap['age']}</td>
            </tr>
        """
    snapshot_report += "</tbody></table></div>"
else:
    snapshot_report = '''
    <style>
        @media only screen and (max-width: 600px) {
            div {
                padding: 10px;
            }
            h1, p {
                font-size: 18px;
            }
        }
    </style>
    <div style="border: 2px solid #e74c3c; padding: 20px; font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; text-align: center;">
        <h1 style="color: #e74c3c;">No Snapshots Found!</h1>
        <p style="font-size: 18px; color: #7f8c8d;">We couldn't find any snapshots for the VMs in the vCenter. It's always a good idea to regularly review and clean up unnecessary snapshots to save storage space and maintain VM performance.</p>
    </div>
    '''

# Clean up and disconnect from vCenter
container_view.Destroy()
Disconnect(si)

# Construct and send an email report
subject = 'VM Snapshot Report'
msg = MIMEText(snapshot_report, 'html')  
msg['Subject'] = subject
msg['From'] = sender_email
msg['To'] = receiver_email

with smtplib.SMTP(smtp_server, smtp_port) as server:
    server.send_message(msg)

print('Email has been sent!')
