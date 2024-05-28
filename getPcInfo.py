import subprocess
import sys

# Upgrade pip
subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])

# Continue with the rest of your imports
import pandas as pd
import streamlit as st

# Conditional imports for Windows-specific packages
if sys.platform == 'win32':
    try:
        import pythoncom
        pythoncom.CoInitialize()
        import wmi
        import win32com.client
    except ImportError:
        st.warning("Required Windows modules not found. Please ensure pywin32 and wmi are installed.")

# Function to get system information
def get_system_info():
    system_info = platform.uname()
    user_info = subprocess.check_output('whoami').decode().strip()
    # Retrieve product ID (Windows specific)
    product_id = ""
    opengl_version = ""
    try:
        wmi_obj = wmi.WMI()
        for os in wmi_obj.Win32_OperatingSystem():
            product_id = os.SerialNumber
            break
        for item in wmi_obj.Win32_OperatingSystem():
            directx_version = item.OSArchitecture
            opengl_version = item.Version
    except Exception as e:
        product_id = str(e)

    return {
        "System": system_info.system,
        "Device Name": system_info.node,
        "Release": system_info.release,
        "Version": system_info.version,
        "Machine": system_info.machine,
        "Processor": system_info.processor,
        "User Name": user_info,
        "Product ID": product_id,  # Add product ID to the dictionary
        "OpenGL Version": opengl_version  # Add OpenGL Version to the dictionary
    }



# Function to get audio information (Windows specific)
def get_audio_info():
    audio_info = {}
    try:
        wmi_obj = wmi.WMI()
        for controller in wmi_obj.Win32_SoundDevice():
            audio_info["Audio Device"] = controller.Name
            break  # Only need information from one audio device
    except Exception as e:
        audio_info['Error'] = str(e)
    return audio_info


# Function to get CPU information
def get_cpu_info():
    try:
        cpu_info = cpuinfo.get_cpu_info()
        serial_number = ""
        # Retrieving CPU serial number (Windows specific)
        try:
            wmi_obj = wmi.WMI()
            for processor in wmi_obj.Win32_Processor():
                serial_number = processor.ProcessorId
                break
        except Exception as e:
            serial_number = str(e)
        
        return {
            "CPU Name": cpu_info.get('brand_raw', 'N/A'),
            "Serial Number": serial_number,  # Add Serial Number to the dictionary
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

# Function to get BIOS information (Windows specific)

def get_bios_info():
    bios_info = {"Category": [], "Information": []}
    try:
        result = subprocess.check_output("wmic bios get /value", shell=True).decode().strip()
        lines = result.split('\n')
        properties = ["Manufacturer", "SMBIOSBIOSVersion"]
        for line in lines:
            line = line.rstrip('\r')  # Strip '\r' character
            prop, _, value = line.partition('=')
            if prop in properties:
                bios_info["Category"].append(prop.strip())  # Strip leading/trailing whitespace
                bios_info["Information"].append(value.strip())  # Strip leading/trailing whitespace
    except Exception as e:
        bios_info["Property"].extend(["Manufacturer", "SMBIOSBIOSVersion"])
        bios_info["Value"].extend([str(e)] * 2)
    return bios_info

# Function to get network information
def get_network_info():
    net_info = psutil.net_if_addrs()
    formatted_net_info = {}
    for interface, addrs in net_info.items():
        for addr in addrs:
            if addr.family == socket.AF_LINK:
                formatted_net_info.setdefault(interface, {})["MAC Address"] = addr.address
            elif addr.family == socket.AF_INET:
                formatted_net_info.setdefault(interface, {})["IP Address"] = addr.address
    return formatted_net_info

# Function to get motherboard information (Windows specific)
def get_motherboard_info():
    motherboard_info = {}
    try:
        wmi_obj = wmi.WMI()
        for board in wmi_obj.Win32_BaseBoard():
            motherboard_info["Manufacturer"] = board.Manufacturer
            motherboard_info["Product"] = board.Product
            motherboard_info["Version"] = board.Version
            motherboard_info["SerialNumber"] = board.SerialNumber
    except Exception as e:
        motherboard_info['Error'] = str(e)
    return motherboard_info

# Function to get connected peripherals (Mouse, Keyboard, etc.) (Windows specific)
def get_peripherals_info():
    peripherals_info = {}
    try:
        result = subprocess.check_output("wmic path Win32_PointingDevice get Name", shell=True).decode().strip()
        peripherals_info['Mouse'] = result.split('\n')[1].strip()
        result = subprocess.check_output("wmic path Win32_Keyboard get Name", shell=True).decode().strip()
        peripherals_info['Keyboard'] = result.split('\n')[1].strip()
    except Exception as e:
        peripherals_info['Error'] = str(e)
    return peripherals_info

# Function to get video information (using PowerShell)
def get_video_info():
    video_info = []
    try:
        result = subprocess.check_output(["powershell", "-Command", 
            "Get-WmiObject Win32_VideoController | Select-Object Name,VideoProcessor,AdapterRAM,DriverVersion | Format-List"], shell=True).decode().strip()
        blocks = result.split("\n\n")
        for block in blocks:
            info = {}
            for line in block.split("\n"):
                if line.strip():
                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip()
                    # Handling empty or missing fields
                    if key == "AdapterRAM" and value:
                        value = f"{int(value) / (1024**3):.2f} GB"
                    info[key] = value
            if info:
                # Check if all required keys are present
                if all(key in info for key in ["Name", "VideoProcessor", "AdapterRAM", "DriverVersion"]):
                    video_info.append(info)
    except Exception as e:
        video_info.append({"Error": str(e)})
    return video_info



# Function to get monitor information (using PowerShell)
def get_monitor_info():
    monitor_info = []
    try:
        result = subprocess.check_output(["powershell", "-Command", 
            "Get-WmiObject Win32_DesktopMonitor | Select-Object Name,ScreenHeight,ScreenWidth,Status | Format-List"], shell=True).decode().strip()
        blocks = result.split("\n\n")
        for block in blocks:
            info = {}
            for line in block.split("\n"):
                if line.strip():
                    key, value = line.split(":", 1)
                    info[key.strip()] = value.strip()
            if info:
                monitor_info.append(info)
    except Exception as e:
        monitor_info.append({"Error": str(e)})
    return monitor_info

# Function to display all information
def display_info():
    system_info = get_system_info()
    cpu_info = get_cpu_info()
    memory_info = get_memory_info()
    disk_info, combined_disk_info = get_disk_info()
    bios_info = get_bios_info()
    network_info = get_network_info()
    motherboard_info = get_motherboard_info()
    peripherals_info = get_peripherals_info()
    video_info = get_video_info()
    monitor_info = get_monitor_info()
    audio_info = get_audio_info()  

    # Center tables and adjust font sizes
    custom_css = """
    <style>
    table {margin-left:auto; margin-right:auto; font-size:25px;} 
    th {font-size:31 px;} 
    td {font-size:28 px;} 
    .css-2trqyj {font-size: 33px;} 
    .stButton button {font-size: 28px;} 
    h1, h2, h3, h4, h5, h6 {font-size: 38px;} 
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)


    st.subheader("Overall Information")
    overall_info_data = {
        "Category": ["Operating System", "Processor", "Memory", "Disk Storage", "Audio", "Motherboard", "Mouse", "Keyboard"],
        "Information": [
            system_info.get("System", "N/A"), 
            cpu_info.get("CPU Name", "N/A"), 
            memory_info.get("Total Memory (GB)", "N/A"), 
            f"Total Space: {combined_disk_info['Total Space (GB)']} GB<br>"
            f"Used Space: {combined_disk_info['Used Space (GB)']} GB<br>"
            f"Free Space: {combined_disk_info['Free Space (GB)']} GB<br>"
                f"Usage: {combined_disk_info['Usage (%)']}%",
            audio_info.get("Audio Device", "N/A"), 
            motherboard_info.get("Product", "N/A"), 
            peripherals_info.get("Mouse", "N/A"),
            peripherals_info.get("Keyboard", "N/A")
        ]
    }
    overall_info_df = pd.DataFrame(overall_info_data)
    st.markdown(overall_info_df.to_html(index=False, escape=False), unsafe_allow_html=True)

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
    bios_info_df = pd.DataFrame(bios_info, index=[0, 0])

    st.markdown(bios_info_df.to_html(index=False), unsafe_allow_html=True)

    st.subheader("Network Information")
    for interface, info in network_info.items():
        st.write(f"**{interface}:**")
        network_info_df = pd.DataFrame(info.items(), columns=["Category", "Information"])
        st.markdown(network_info_df.to_html(index=False), unsafe_allow_html=True)

    st.subheader("Motherboard Information")
    motherboard_info_df = pd.DataFrame(motherboard_info.items(), columns=["Category", "Information"])
    st.markdown(motherboard_info_df.to_html(index=False), unsafe_allow_html=True)

    st.subheader("Peripherals Information")
    peripherals_info_df = pd.DataFrame(peripherals_info.items(), columns=["Category", "Information"])
    st.markdown(peripherals_info_df.to_html(index=False), unsafe_allow_html=True)

    st.subheader("Video Information")
    for video in video_info:
        video_info_df = pd.DataFrame(video.items(), columns=["Category", "Information"])
        st.markdown(video_info_df.to_html(index=False), unsafe_allow_html=True)

    st.subheader("Monitor Information")
    for monitor in monitor_info:
        monitor_info_df = pd.DataFrame(monitor.items(), columns=["Category", "Information"])
        st.markdown(monitor_info_df.to_html(index=False), unsafe_allow_html=True)
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

    pythoncom.CoUninitialize()  # Uninitialize COM

if __name__ == "__main__":
    main()
