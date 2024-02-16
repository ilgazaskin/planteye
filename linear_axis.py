import canopen
import time
import matplotlib.pyplot as plt
import mplcursors


# Drive to the first target position 
first_target_position = -100000#-230000

# Drive to the second target position
second_target_position = 0

# CANOpen setup
network = canopen.Network()
network.connect(channel='can0', bustype='socketcan')
node = network.add_node(10, '/home/thorvald/EDS-Dateien/Dunker_BG45ci.eds')

# Motor Parameters
EncoderLines = 500  
EncoderResolution = 4 * EncoderLines

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
node.sdo[0x4340][1].raw = 1800 # VEL_Acc_dV (velocity in rpm)
node.sdo[0x4341][1].raw = 1000 # VEL_Acc_dT (time in ms)
node.sdo[0x4342][1].raw = 1800 # Vel_Dec_dV (velocity in rpm)
node.sdo[0x4343][1].raw = 1000 # Vel_Dec_dt (time in ms)

# Position Following Error - Window
node.sdo[0x4732][1].raw = 1000 # Position following error - window

# Device Mode
node.sdo[0x4003][1].raw = 7 # Device mode "position mode"

# Desired Velocity
node.sdo[0x4300][1].raw = 750 # Desired velocity in rpm

# Start of the Test Program
node.sdo[0x4000][1].raw = 1 # Reset error register
node.sdo[0x4004][1].raw = 1 # Enable power stage
time.sleep(0.1) # 100ms delay for power stage to be enabled
node.sdo[0x4150][1].raw = 1 # Open brake (just in case)

# Function to check if the position is within the target allowance
def is_within_target(actual, target, allowance=1):
    return target - allowance <= actual <= target + allowance

# Data collection
positions = []
times = []
speeds = []

node.sdo[0x4790][1].raw = first_target_position

start_time = time.time()
actual_position = node.sdo[0x4762][1].raw
last_position = actual_position

while not is_within_target(actual_position, first_target_position):
    current_time = time.time() - start_time
    actual_position = node.sdo[0x4762][1].raw
    times.append(current_time)
    positions.append(actual_position)
    print("Actual position = ", actual_position)
    # Calculate speed
    delta_position = actual_position - last_position
    delta_time = current_time - (times[-2] if len(times) > 1 else 0)
    speeds.append(delta_position / delta_time if delta_time else 0)
    last_position = actual_position

    time.sleep(0.1)  # Sampling interval

# Wait 2 seconds
time.sleep(2)


node.sdo[0x4790][1].raw = second_target_position
actual_position = node.sdo[0x4762][1].raw

while not is_within_target(actual_position, second_target_position):
    current_time = time.time() - start_time
    actual_position = node.sdo[0x4762][1].raw
    times.append(current_time)
    positions.append(actual_position)
    print("Actual position = ", actual_position)
    # Calculate speed
    delta_position = actual_position - last_position
    delta_time = current_time - times[-2]
    speeds.append(delta_position / delta_time if delta_time else 0)
    last_position = actual_position

    time.sleep(0.1)  # Sampling interval

# Append final time and set final speed to 0
final_time = time.time() - start_time
times.append(final_time)
speeds.append(0)

# Disconnect from the CANOpen network
network.disconnect()

# Plotting
fig, ax = plt.subplots()
ax.plot(times, speeds)
ax.set_xlabel('Time (s)')
ax.set_ylabel('Speed (counts/s)')
ax.set_title('Speed-Time Curve of Linear Axis Movement')
ax.grid(True)

# Adding cursor functionality
cursor = mplcursors.cursor(hover=True)
cursor.connect(
    "add", 
    lambda sel: sel.annotation.set_text(
        'Time: {:.2f}s, Speed: {:.2f} counts/s'.format(times[int(sel.index)], speeds[int(sel.index)])
    )
)

plt.show()
