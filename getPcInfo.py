import subprocess
import sys
import platform
import psutil
import socket
import cpuinfo

# Upgrade pip
subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])

# Continue with the rest of your imports
import pandas as pd
import streamlit as st

# Conditional imports for Windows-specific packages
if sys.platform == 'win32':
    try:
        import ctypes
        ctypes.windll.ole32.CoInitialize(None)
        import win32com.client
    except ImportError:
        st.warning("Required Windows modules not found. Please ensure pywin32 is installed.")

# Your Streamlit app code here

# Function to get system information
def get_system_info():
    system_info = platform.uname()
    user_info = subprocess.check_output('whoami').decode().strip()

    return {
        "System": system_info.system,
        "Device Name": system_info.node,
        "Release": system_info.release,
        "Version": system_info.version,
        "Machine": system_info.machine,
        "Processor": system_info.processor,
        "User Name": user_info
    }

# Function to get CPU information
# Function to get CPU information
def get_cpu_info():
    try:
        cpu_info = cpuinfo.get_cpu_info()
        
        return {
            "CPU Name": cpu_info.get('brand_raw', 'N/A'),
            "Logical Processors": psutil.cpu_count(logical=True),
            "Physical Processors": psutil.cpu_count(logical=False),
            "Architecture": cpu_info.get('arch', 'N/A'),
            "Current Clock Speed": f"{psutil.cpu_freq().current:.2f} MHz",
            "Max Clock Speed": f"{psutil.cpu_freq().max:.2f} MHz",
            "L1 Cache": cpu_info.get('l1_data_cache_size', 'N/A'),
            "L2 Cache": cpu_info.get('l2_cache_size', 'N/A'),
            "L3 Cache": cpu_info.get('l3_cache_size', 'N/A')
        }
    except Exception as e:
        return {
            "CPU Name": "N/A",
            "Logical Processors": "N/A",
            "Physical Processors": "N/A",
            "Architecture": "N/A",
            "Current Clock Speed": "N/A",
            "Max Clock Speed": "N/A",
            "L1 Cache": "N/A",
            "L2 Cache": "N/A",
            "L3 Cache": "N/A",
            "Error": str(e)
        }


# Function to get memory information
def get_memory_info():
    memory_info = psutil.virtual_memory()
    return {
        "Total Memory (GB)": f"{memory_info.total / (1024**3):.2f}",
        "Available Memory (GB)": f"{memory_info.available / (1024**3):.2f}",
        "Used Memory (GB)": f"{memory_info.used / (1024**3):.2f}",
        "Memory Usage (%)": memory_info.percent
    }

# Function to get disk information
def get_disk_info():
    partitions = psutil.disk_partitions()
    total_space = used_space = free_space = 0

    disk_info = []
    for partition in partitions:
        if "cdrom" in partition.opts or partition.fstype == '':
            continue

        usage = psutil.disk_usage(partition.mountpoint)
        total_space += usage.total
        used_space += usage.used
        free_space += usage.free

        disk_entry = {
            "Device": partition.device,
            "File System Type": partition.fstype,
            "Total Space (GB)": f"{usage.total / (1024**3):.2f}",
            "Used Space (GB)": f"{usage.used / (1024**3):.2f}",
            "Free Space (GB)": f"{usage.free / (1024**3):.2f}",
            "Usage (%)": usage.percent
        }
        disk_info.append(disk_entry)

    combined_info = {
        "Total Space (GB)": f"{total_space / (1024**3):.2f}",
        "Used Space (GB)": f"{used_space / (1024**3):.2f}",
        "Free Space (GB)": f"{free_space / (1024**3):.2f}",
        "Usage (%)": f"{(used_space / total_space) * 100:.1f}" if total_space > 0 else "N/A"
    }

    return disk_info, combined_info

# Function to get BIOS information
def get_bios_info():
    bios_info = {
        "Vendor": platform.system(),
        "Version": platform.version()
    }
    return bios_info

# Function to get network information
def get_network_info():
    net_info = psutil.net_if_addrs()
    formatted_net_info = {}
    
    af_link = socket.AF_PACKET if hasattr(socket, 'AF_PACKET') else psutil.AF_LINK  # Adjust for platform differences

    for interface, addrs in net_info.items():
        for addr in addrs:
            if addr.family == af_link:
                formatted_net_info.setdefault(interface, {})["MAC Address"] = addr.address
            elif addr.family == socket.AF_INET:
                formatted_net_info.setdefault(interface, {})["IP Address"] = addr.address
    return formatted_net_info

# Function to get motherboard information
def get_motherboard_info():
    # For Linux systems, we can't retrieve specific motherboard information reliably
    return {"Manufacturer": "N/A", "Product": "N/A", "Version": "N/A", "SerialNumber": "N/A"}

# Function to display all information
def display_info():
    system_info = get_system_info()
    cpu_info = get_cpu_info()
    memory_info = get_memory_info()
    disk_info, combined_disk_info = get_disk_info()
    bios_info = get_bios_info()
    network_info = get_network_info()
    motherboard_info = get_motherboard_info()

    # Convert system_info to a dictionary
    system_info_dict = {key: [value] for key, value in system_info.items()}

    # Ensure that all arrays have the same length
    max_length = max(len(system_info_dict), len(cpu_info), len(memory_info), len(disk_info), len(bios_info))

    # Pad arrays with N/A if needed
    system_info_dict = pad_array(system_info_dict, max_length)
    cpu_info = pad_array(cpu_info, max_length)
    memory_info = pad_array(memory_info, max_length)
    bios_info = pad_array(bios_info, max_length)

    # Create DataFrame for overall information
    overall_info_data = {
        "Category": ["Operating System", "Processor", "Memory", "Disk Storage", "Motherboard"],
        "Information": [
            system_info_dict.get("System", ["N/A"])[0],
            cpu_info.get("CPU Name", "N/A"),
            memory_info.get("Total Memory (GB)", "N/A"),
            f"Total Space: {combined_disk_info['Total Space (GB)']} GB<br>"
            f"Used Space: {combined_disk_info['Used Space (GB)']} GB<br>"
            f"Free Space: {combined_disk_info['Free Space (GB)']} GB<br>"
            f"Usage: {combined_disk_info['Usage (%)']}%",
            motherboard_info.get("Manufacturer", "N/A"),
            # Add missing values here for alignment
        ]
    }
    overall_info_df = pd.DataFrame(overall_info_data)
    st.markdown(overall_info_df.to_html(index=False, escape=False), unsafe_allow_html=True)

    # Rest of the function remains unchanged...

    st.subheader("System Information")
    system_info_df = pd.DataFrame(system_info.items(), columns=["Category", "Information"])
    st.markdown(system_info_df.to_html(index=False), unsafe_allow_html=True)

    st.subheader("CPU Information")
    cpu_info_df = pd.DataFrame(cpu_info.items(), columns=["Category", "Information"])
    st.markdown(cpu_info_df.to_html(index=False), unsafe_allow_html=True)

    st.subheader("Memory Information")
    memory_info_df = pd.DataFrame(memory_info.items(), columns=["Category", "Information"])
    st.markdown(memory_info_df.to_html(index=False), unsafe_allow_html=True)

    st.subheader("Disk Information")
    disk_info_df = pd.DataFrame(disk_info)
    st.markdown(disk_info_df.to_html(index=False), unsafe_allow_html=True)

    st.subheader("BIOS Information")
    bios_info_df = pd.DataFrame(bios_info.items(), columns=["Category", "Information"])
    st.markdown(bios_info_df.to_html(index=False), unsafe_allow_html=True)

    st.subheader("Network Information")
    for interface, info in network_info.items():
        st.write(f"**{interface}:**")
        network_info_df = pd.DataFrame(info.items(), columns=["Category", "Information"])
        st.markdown(network_info_df.to_html(index=False), unsafe_allow_html=True)

    st.subheader("Motherboard Information")
    motherboard_info_df = pd.DataFrame(motherboard_info.items(), columns=["Category", "Information"])
    st.markdown(motherboard_info_df.to_html(index=False), unsafe_allow_html=True)

def pad_array(arr, length):
    """Pad array with N/A values to match specified length."""
    if isinstance(arr, list):
        while len(arr) < length:
            arr.append("N/A")
        return arr
    else:
        return ["N/A"] * length

def display_home():
    st.markdown("<div style='text-align:center'><h1 style='font-family:Ink Free; font-size: 54px;'>PC Synapse 💻</h1></div>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center'><marquee behavior='scroll' direction='left'><h3 style='font-family: Lucida Handwriting, cursive; font-style: italic;'>Get your PC info today!!!</h3></marquee></div>", unsafe_allow_html=True)

    image_path = "home_page.jpg"
    st.image(image_path, use_column_width=True)

    if st.button("Get Info", key="circle-button", help="Get your PC info"):
        display_info()

def display_about():
    st.subheader("Credits")
    image_path = "Arnob.jpg"
    st.image(image_path, width=350)  # Specify the width in pixels (e.g., 300)
    st.markdown("""
    **Arnob Aich Anurag**

    Research Intern at AMIR Lab (Advanced Machine Intelligence Research Lab)

    Student at American International University Bangladesh

    Dhaka, Bangladesh

    Email: openworld41@gmail.com
    """)

def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Home", "About"])

    if page == "Home":
        display_home()
    elif page == "About":
        display_about()

    if sys.platform == 'win32':
        ctypes.windll.ole32.CoUninitialize()  # Uninitialize COM

if __name__ == "__main__":
    main()
