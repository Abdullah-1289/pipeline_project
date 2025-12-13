# ⚙️ Installation Guide: ICS Pipeline Security AI

## Prerequisites

### Hardware Requirements
- **Development Machine**: Ubuntu 22.04+ or Windows with WSL2
- **Tested on**: 8GB RAM, 4-core CPU, 20GB free disk space

### Software Requirements
- **Python**: 3.10 or higher
- **Node.js**: 18.x or higher
- **Mosquitto**: MQTT broker (required to run the simulation)
- **Git**: Version control

## 1. Project Setup (Clone & Prepare)

First, clone the repository and navigate into the project directory:

```bash
# Clone the repository
git clone [https://github.com/Abdullah-1289/pipeline_project.git](https://github.com/Abdullah-1289/pipeline_project.git)
cd pipeline_project

2. Automated Installation

The setup script handles the installation of all necessary software components (Python libraries, Node.js, Node-RED, and Mosquitto).
Execution

Run the automated setup script. This requires root/sudo privileges.
Bash

# Corrected path to the setup script
chmod +x 2_CODE_AND_SCRIPTS/setup_environment.sh
./2_CODE_AND_SCRIPTS/setup_environment.sh

3. Manual Installation (What the script does)

If the automated script fails or for system administrators who prefer manual control, follow these steps:
A. Install System Dependencies (Node.js & Mosquitto)

Ensure Node.js and the Mosquitto MQTT broker are installed on your system. (Note: Specific installation commands may vary by OS. Example for Ubuntu/Debian:)
Bash

# Install Node.js (if not already present)
sudo apt update
sudo apt install -y nodejs npm

# Install Mosquitto MQTT Broker
sudo apt install -y mosquitto mosquitto-clients

B. Setup Python Environment & Dependencies

    Create a Virtual Environment (venv):
    Bash

python3 -m venv venv

Activate the Environment:
Bash

source venv/bin/activate

Install Python Packages:
Bash

    pip install -r 1_SETUP_DOCS/REQUIREMENTS.txt

C. Install Node-RED

Install Node-RED globally, which will be used to run the ICS pipeline simulation.
Bash

sudo npm install -g node-red

4. Running the Simulation

Once the environment is set up, use the runner script to start the entire pipeline:
Bash

./2_CODE_AND_SCRIPTS/run_simulation.sh


### Final Steps to Update GitHub

You need to update the file on your local laptop and commit the change.

1.  **Edit the file:** Paste the revised content into your local file: `1_SETUP_DOCS/INSTALLATION.md`.
2.  **Stage the change:**
    ```bash
    git add 1_SETUP_DOCS/INSTALLATION.md
    ```
3.  **Commit the change:**
    ```bash
    git commit -m "Update: Corrected INSTALLATION.md paths and added detailed manual setup steps for Node-RED."
    ```
4.  **Push the update:**
    ```bash
    git push origin main
    ```
