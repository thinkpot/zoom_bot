import streamlit as st
import boto3
import math

st.title("Zoom Webinar Bot Scaler")

# --- Input fields ---
aws_access_key = st.text_input("AWS Access Key", type="password")
aws_secret_key = st.text_input("AWS Secret Key", type="password")
aws_region = st.text_input("AWS Region", value="us-east-1")

webinar_url = st.text_input("Zoom Webinar Link")
base_email = st.text_input("Base Email (e.g. bot@example.com)")
base_name = st.text_input("Base Display Name", value="ZoomBot")

joiners = st.number_input("Total Number of Joiners", min_value=1, value=50, step=1)
bots_per_instance = st.number_input("Bots per Instance", min_value=1, value=5, step=1)

key_pair = st.text_input("AWS Key Pair Name")
security_group = st.text_input("AWS Security Group ID")
subnet_id = st.text_input("AWS Subnet ID")
ami_id = st.text_input("AMI ID (Ubuntu 22.04)", value="ami-xxxxxxxx")

# Session state to store launched instance IDs
if "launched_instances" not in st.session_state:
    st.session_state.launched_instances = []

def get_ec2_client():
    return boto3.client(
        "ec2",
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name=aws_region
    )

# --- Launch Bots Button ---
if st.button("Launch Bots"):
    st.write("Calculating resources...")

    instances_needed = math.ceil(joiners / bots_per_instance)
    st.write(f"Launching {instances_needed} EC2 instances with {bots_per_instance} bots each...")

    ec2 = get_ec2_client()

    # --- UserData Script ---
    user_data_script = f"""#!/bin/bash
    sudo apt update
    sudo apt install -y chromium-browser chromium-chromedriver python3-pip
    pip3 install selenium webdriver-manager

    # Fetch your bot script (update with actual repo or S3 path)
    wget https://raw.githubusercontent.com/thinkpot/zoom_bot/main/zoom_bot.py -O /home/ubuntu/zoom_bot.py

    cd /home/ubuntu
    python3 zoom_bot.py \\
        --url "{webinar_url}" \\
        --email "{base_email}" \\
        --name "{base_name}" \\
        --count {bots_per_instance} &
    """

    response = ec2.run_instances(
        ImageId=ami_id,
        InstanceType="t3.large",
        MinCount=instances_needed,
        MaxCount=instances_needed,
        KeyName=key_pair,
        SecurityGroupIds=[security_group],
        SubnetId=subnet_id,
        UserData=user_data_script
    )

    instance_ids = [inst["InstanceId"] for inst in response["Instances"]]
    st.session_state.launched_instances.extend(instance_ids)

    st.success(f"Launched {instances_needed} instances for {joiners} bots!")
    st.json(instance_ids)

# --- Stop Bots Button ---
if st.button("Stop All Bots"):
    if not st.session_state.launched_instances:
        st.warning("No instances were launched from this session.")
    else:
        ec2 = get_ec2_client()
        ec2.terminate_instances(InstanceIds=st.session_state.launched_instances)
        st.success(f"Terminated {len(st.session_state.launched_instances)} instances.")
        st.session_state.launched_instances = []

# --- Status Panel ---
if st.session_state.launched_instances:
    st.subheader("Launched Instances Status")
    ec2 = get_ec2_client()
    response = ec2.describe_instances(InstanceIds=st.session_state.launched_instances)

    statuses = []
    for reservation in response["Reservations"]:
        for inst in reservation["Instances"]:
            statuses.append({
                "InstanceId": inst["InstanceId"],
                "State": inst["State"]["Name"],
                "Type": inst["InstanceType"],
                "Public IP": inst.get("PublicIpAddress", "N/A")
            })

    st.table(statuses)
