"""
vm_snapshot_report.py

Author: Marcos Fermin

This script connects to vCenter, checks all VMs, and sends a report of
all the remaining snapshots for each VM. It also sends an email if there
are any snapshots older than 24 hours.
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
smtp_server = 'mail-relay.cuny.edu'
smtp_port = 25
sender_email = 'sphtech@sph.cuny.edu'
receiver_email = 'marcos.fermin@sph.cuny.edu'

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
              table {
               border-collapse: collapse;
               width: 100%;
               margin-bottom: 1rem;
               background-color: transparent;
               color: #212529;
              }
              table th,
              table td {
               padding: 0.75rem;
               vertical-align: top;
               border-top: 1px solid #dee2e6;
              }
              table thead th {
               vertical-align: bottom;
               border-bottom: 2px solid #dee2e6;
              }
              table tbody + tbody {
               border-top: 2px solid #dee2e6;
              }
              table .table {
               background-color: #fff;
              }
              table-sm th,
              table-sm td {
               padding: 0.3rem;
              }
              table-bordered {
               border: 1px solid #dee2e6;
              }
              table-bordered th,
              table-bordered td {
               border: 1px solid #dee2e6;
              }
              table-bordered thead th,
              table-bordered thead td {
               border-bottom-width: 2px;
              }
              table-borderless th,
              table-borderless td,
              table-borderless thead th,
              table-borderless tbody + tbody {
               border: 0;
              }
              table-striped tbody tr:nth-of-type(odd) {
               background-color: rgba(0, 0, 0, 0.05);
              }
              table-hover tbody tr:hover {
               background-color: rgba(0, 0, 0, 0.075);
              }
              @media (max-width: 575.98px) {
               table-responsive-sm {
                display: block;
                width: 100%;
                overflow-x: auto;
                -webkit-overflow-scrolling: touch;
               }
               table-responsive-sm > .table-bordered {
                border: 0;
               }
              }
              @media (max-width: 767.98px) {
               table-responsive-md {
                display: block;
                width: 100%;
                overflow-x: auto;
                -webkit-overflow-scrolling: touch;
               }
               table-responsive-md > .table-bordered {
                border: 0;
               }
              }
              @media (max-width: 991.98px) {
               table-responsive-lg {
                display: block;
                width: 100%;
                overflow-x: auto;
                -webkit-overflow-scrolling: touch;
               }
               table-responsive-lg > .table-bordered {
                border: 0;
               }
              }
              @media (max-width: 1199.98px) {
               table-responsive-xl {
                display: block;
                width: 100%;
                overflow-x: auto;
                -webkit-overflow-scrolling: touch;
               }
               table-responsive-xl > .table-bordered {
                border: 0;
               }
              }
              /* New styles */
              table {
               background-color: #f8d7da;
               color: #721c24;
               font-weight: bold;
              }
              table th,
              table td {
               border: 1px solid #f5c6cb;
               padding: 0.75rem;
               vertical-align: top;
              }
              table thead th {
               border-bottom: 2px solid #f5c6cb;
              }
              table tbody + tbody {
               border-top: 2px solid #f5c6cb;
              }
              table-striped tbody tr:nth-of-type(odd) {
               background-color: #fff3f4;
              }
              table-hover tbody tr:hover {
               background-color: #f1b0b7;
              }
             </style>
             <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto;">
              <div class="table-responsive">
               <table class="table table-bordered table-striped table-hover">
                <thead>
                 <tr>
                  <th>VM Name</th>
                  <th>Snapshot Name</th>
                  <th>Description</th>
                  <th>Created On</th>
                  <th>Age</th>
                 </tr>
                </thead>
                <tbody>
             """
    for snap in snapshot_data:
              snapshot_report += f"""
               <tr>
                <td>{snap['vm_name']}</td>
                <td>{snap['name']}</td>
                <td>{snap['description']}</td>
                <td>{snap['created_on']}</td>
                <td>{snap['age']}</td>
               </tr>
              """
    snapshot_report += "</tbody></table></div></div>"
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

            # Send the email
with smtplib.SMTP(smtp_server, smtp_port) as server:
             server.send_message(msg)
             print('Email has been sent!')


