import canopen
from pynput import keyboard
import time

# CANOpen setup
network = canopen.Network()
network.connect(channel='can0', bustype='socketcan')
node = network.add_node(10, '/home/thorvald/EDS-Dateien/Dunker_BG45ci.eds')

# Motor Parameters
EncoderLines = 500  
EncoderResolution = 4 * EncoderLines

MOVE_INCREMENT = 5000  # Adjust if needed

# Controller Feedback (Encoder)
node.sdo[0x4350][1].raw = 0x96A  # Encoder feedback for the velocity controller
node.sdo[0x4550][1].raw = 0x96A  # Encoder feedback for the secondary velocity controller
node.sdo[0x4962][1].raw = EncoderResolution  # Encoder resolution

# Controller Parameters
node.sdo[0x4310][1].raw = 100  # PID Vel Kp
node.sdo[0x4311][1].raw = 0    # PID Vel Ki
node.sdo[0x4312][1].raw = 0    # PID Vel Kd
node.sdo[0x4313][1].raw = 0    # PID Vel KiLimit
node.sdo[0x4314][1].raw = 1000 # PID Vel Kvff

# Secondary Velocity Controller
node.sdo[0x4510][1].raw = 100 # PI SVel Kp
node.sdo[0x4511][1].raw = 100 # PI SVel Ki
node.sdo[0x4517][1].raw = 0 # SVel IxR factor

# Current Controller
node.sdo[0x4210][1].raw = 100 # PI Current controller Kp
node.sdo[0x4211][1].raw = 100 # PI Current controller Ki

# Current Limits
node.sdo[0x4221][1].raw = 4000 # Current limit - max. positive in mA
node.sdo[0x4223][1].raw = 4000 # Current limit - max. negative in mA

# Ramps
node.sdo[0x4340][1].raw = 3000 # VEL_Acc_dV (velocity in rpm)
node.sdo[0x4341][1].raw = 1000 # VEL_Acc_dT (time in ms)
node.sdo[0x4342][1].raw = 3000 # Vel_Dec_dV (velocity in rpm)
node.sdo[0x4343][1].raw = 1000 # Vel_Dec_dt (time in ms)

# Position Following Error - Window
node.sdo[0x4732][1].raw = 1000 # Position following error - window

# Device Mode
node.sdo[0x4003][1].raw = 7 # Device mode "position mode"

# Desired Velocity
Velocity = node.sdo[0x4300][1].raw = 500 # Desired velocity in rpm

# Start of the Test Program
node.sdo[0x4000][1].raw = 1 # Reset error register
node.sdo[0x4004][1].raw = 1 # Enable power stage
time.sleep(0.1) # 100ms delay for power stage to be enabled
node.sdo[0x4150][1].raw = 1 # Open brake (just in case)

# Function to move the linear axis relatively
def move_relative(distance):
    try:
        node.sdo[0x4791][1].raw = distance
        # Wait for the move to complete; adjust the delay as necessary based on your system's response time
        time.sleep(Velocity / MOVE_INCREMENT)
        # Read and print the actual position after the movement
        actual_position = node.sdo[0x4762][1].raw
        print(f"Actual position after move: {actual_position}")
    except Exception as e:
        print(f"Error moving: {e}")

def reset_position():
    try:
        # Reset the current position
        node.sdo[0x4000][0x12].raw = 0  # Desired position set to 0
        
        # Toggle command if it has been previously used
        node.sdo[0x4000][2].raw = 0x00
        time.sleep(0.1)  # Short delay to ensure the toggle takes effect

        # Command to set the position, effectively resetting it
        node.sdo[0x4000][2].raw = 0x58

        # Wait for the operation to complete
        time.sleep(0.1)  # Adjust delay as necessary based on your system's response time

        # Optionally, read back and print the actual position to confirm reset
        actual_position = node.sdo[0x4762][1].raw
        print(f"Position reset to 0. Actual position: {actual_position}")
    except Exception as e:
        print(f"Error resetting position: {e}")

# Keyboard event handler
def on_press(key):
    if key == keyboard.Key.left:
        move_relative(MOVE_INCREMENT)
    elif key == keyboard.Key.right:
        move_relative(-MOVE_INCREMENT)
    elif key == keyboard.Key.up:
        reset_position()

# Function to safely close the network connection
def close_network_connection():
    network.disconnect()
    print("Network connection closed successfully.")

# Main function to start the listener
def main():
    print("Control the linear axis with left and right arrow keys. Press up to reset position.")
    listener = keyboard.Listener(on_press=on_press)
    try:
        listener.start()
        listener.join()
    except KeyboardInterrupt:
        print("\nCtrl+C pressed. Exiting...")
        close_network_connection()

if __name__ == "__main__":
    main()