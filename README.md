# VCenter VM Snapshot Report

Author: Marcos Fermin

## Description
This project connects to vCenter, checks for any existing snapshots on all VMs, and sends a report via email. It highlights snapshots that are older than 24 hours.

## Setup & Installation

### Prerequisites
- Ubuntu Server with Python installed.
- pip installed.
- Access to vCenter.

### Installation
1. Clone this repository:
```sh
git clone https://github.com/marcosfermin/vcenter_vm_snapshot_report.git
cd vcenter_vm_snapshot_report
```
2. Run the `install_dependencies.sh` to install the necessary dependencies:
```sh
sh install_dependencies.sh
```
3. Set up the environment variable for the vCenter password:
```sh
export VCENTER_HOST=your_host
export VCENTER_USER=your_user
export VCENTER_PASSWORD=your_password
```
4. Add the `run_vm_snapshot_report.sh` script to your crontab to run it daily at your preferred time.

## Usage
Run the script manually:
```sh
sh run_vm_snapshot_report.sh
```

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
