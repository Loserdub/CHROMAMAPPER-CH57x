#!/usr/bin/env python3
import sys
import argparse
import time

# Custom ANSI styling codes for modern CLI aesthetics
COLOR_CYAN = "\033[36m"
COLOR_PINK = "\033[95m"
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_RED = "\033[91m"
COLOR_RESET = "\033[0m"
COLOR_BOLD = "\033[1m"

def print_header():
    header = f"""
{COLOR_CYAN}{COLOR_BOLD}   ______ __                                ___  ___                                     
  / ____// /_   _____ ____   ____ ___   __ _/  |/  | ____ _ ____   ____   ___   _____
 / /    / __ \\ / ___// __ \\ / __ `__ \\ / __ `/|_/| |/ __ `// __ \\ / __ \\ / _ \\ / ___/
/ /___ / / / // /   / /_/ // / / / / // /_/ / /  / // /_/ // /_/ // /_/ //  __// /    
\\____//_/ /_//_/    \\____//_/ /_/ /_/ \\__,_/_/  /_/ \\__,_// .___// .___/ \\___//_/     
                                                        /_/    /_/                   
{COLOR_PINK}                             - CH57x Hardware Configurator -{COLOR_RESET}
"""
    print(header)

def check_hid_library():
    try:
        import hid
        return True, hid
    except ImportError:
        print(f"{COLOR_YELLOW}[Warning] Python 'hidapi' library is not installed.{COLOR_RESET}")
        print(f"To run this native backup programmer locally, please execute:")
        print(f"  {COLOR_BOLD}pip install hidapi{COLOR_RESET}\n")
        return False, None

# Device USB IDs
VENDOR_ID = 0x1189
PRODUCT_IDS = [0x8842, 0x8840, 0x8890]

# Key mappings logic derived from k884x reverse-engineered code
def to_key_id(is_knob, index, action=None):
    MAX_NUMBER_OF_BUTTONS = 15
    if not is_knob:
        if index >= 12:
            raise ValueError("Invalid button index (0-11 for 12-key pad)")
        return index + 1
    else:
        # action must be ccw, press, or cw
        action_offsets = {"ccw": 0, "press": 1, "cw": 2}
        if action not in action_offsets:
            raise ValueError("Knob action must be 'ccw', 'press', or 'cw'")
        
        offset = action_offsets[action]
        if index >= 3:
            raise ValueError("Invalid knob index (0-2 for 12k 3dial pad)")
        return MAX_NUMBER_OF_BUTTONS + 1 + 3 * index + offset

def send_message(device, data):
    # Padding report payload to exactly 64 bytes (the first byte is the Report ID 0x03)
    buf = [0] * 65 # hidapi expects Report ID at buf[0] followed by 64 bytes on Windows
    buf[0] = 0x03  # Report ID
    for i, b in enumerate(data):
        if i < 64:
            buf[i + 1] = b
    
    # Debug print
    hex_str = " ".join(f"{b:02x}" for b in buf[1:17]).upper()
    print(f"{COLOR_CYAN}  TX -> [Report 0x03] {hex_str} ... [64 bytes]{COLOR_RESET}")
    
    device.write(buf)
    time.sleep(0.04) # brief sleep to let microcontroller write to flash

def calculate_led_code(mode, color_name):
    modes = {
        "off": 0,
        "backlight": 1,
        "shock": 2,
        "shock2": 3,
        "press": 4
    }
    colors = {
        "white": 0,
        "red": 1,
        "orange": 2,
        "yellow": 3,
        "green": 4,
        "cyan": 5,
        "blue": 6,
        "purple": 7
    }

    if mode not in modes:
        raise ValueError(f"Invalid LED Mode. Choices: {list(modes.keys())}")
    if color_name not in colors:
        raise ValueError(f"Invalid LED Color. Choices: {list(colors.keys())}")

    m_code = modes[mode]
    c_code = colors[color_name]

    if mode == "backlight" and color_name == "white":
        m_code = 5
        c_code = 0

    return (c_code << 4) | m_code

def commit_transaction(device):
    # Packet 1: [0xaa, 0xaa]
    send_message(device, [0xaa, 0xaa])
    # Packet 2: [0xfd, 0xfe, 0xff]
    send_message(device, [0xfd, 0xfe, 0xff])
    # Packet 3: [0xaa, 0xaa]
    send_message(device, [0xaa, 0xaa])

def main():
    print_header()
    has_hid, hid = check_hid_library()

    parser = argparse.ArgumentParser(description="ChromaMapper CLI - Backup Python Utility for CH57x Programmable Keyboards")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # LED Command
    led_parser = subparsers.add_parser("led", help="Configure layer RGB backlight animation")
    led_parser.add_argument("--layer", type=int, default=1, choices=[1, 2, 3], help="Target memory bank layer (1-3)")
    led_parser.add_argument("--mode", type=str, default="backlight", choices=["off", "backlight", "shock", "shock2", "press"], help="LED effect mode")
    led_parser.add_argument("--color", type=str, default="cyan", choices=["white", "red", "orange", "yellow", "green", "cyan", "blue", "purple"], help="Backlight color preset")

    # Bind Key Command
    bind_parser = subparsers.add_parser("bind", help="Bind standard keyboard keys or macros to hardware")
    bind_parser.add_argument("--layer", type=int, default=1, choices=[1, 2, 3], help="Target layer (1-3)")
    bind_parser.add_argument("--type", type=str, default="button", choices=["button", "knob"], help="Input hardware element type")
    bind_parser.add_argument("--index", type=int, required=True, help="Element index (0-11 for buttons, 0-2 for knobs)")
    bind_parser.add_argument("--action", type=str, choices=["ccw", "press", "cw"], help="Knob action trigger (required if element is knob)")
    bind_parser.add_argument("--key", type=str, required=True, help="Standard keyboard char (e.g. 'a', 'b') or HID keycode (e.g. '4' for A)")
    bind_parser.add_argument("--ctrl", action="store_true", help="Include Ctrl modifier")
    bind_parser.add_argument("--shift", action="store_true", help="Include Shift modifier")
    bind_parser.add_argument("--alt", action="store_true", help="Include Alt modifier")
    bind_parser.add_argument("--win", action="store_true", help="Include Win modifier")
    bind_parser.add_argument("--delay", type=int, default=0, help="Delay in ms before execution (max 6000)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if not has_hid:
        print(f"{COLOR_RED}[Error] Native USB communication requires 'hidapi'. Use our beautiful index.html WebHID browser configurator instead, or install 'hidapi' globally.{COLOR_RESET}")
        sys.exit(1)

    # Search for connected target macropad
    print(f"Scanning USB bus for CH57x Macropad device (VID 0x1189)...")
    target_device = None
    
    for device_info in hid.enumerate(VENDOR_ID):
        if device_info['product_id'] in PRODUCT_IDS:
            # We want to target the vendor-defined interface (usually interface 0 or MI_00)
            # The configuration endpoint is MI_00, standard HID keyboards are MI_01
            # interface_number 0 corresponds to raw configuration pipe
            if device_info['interface_number'] == 0 or device_info['interface_number'] == -1:
                target_device = device_info
                break

    if not target_device:
        print(f"{COLOR_RED}[Error] CH57x macro keyboard device not found!{COLOR_RESET}")
        print("Please check that the USB cable is connected securely and try again.")
        sys.exit(1)

    print(f"{COLOR_GREEN}Found Keyboard Interface: {target_device['product_string']} (Path: {target_device['path'].decode()}){COLOR_RESET}")
    
    try:
        dev = hid.device()
        dev.open_path(target_device['path'])
        dev.set_nonblocking(True)
        print("Opened device interface successfully. Executing write transaction...")

        # Handshake: send 64-byte initialization packet (all zeroes)
        send_message(dev, [0] * 64)

        if args.command == "led":
            layer = args.layer
            code = calculate_led_code(args.mode, args.color)
            
            print(f"Writing LED: Layer={layer}, Mode={args.mode}, Color={args.color} (Code=0x{code:02x})...")
            
            led_report = [0] * 64
            led_report[0] = 0xfe
            led_report[1] = 0xb0
            led_report[2] = layer
            led_report[3] = 0x08
            led_report[9] = 0x01
            led_report[11] = code

            send_message(dev, led_report)
            
            # Commit sequence [0xfd, 0xfe, 0xff]
            send_message(dev, [0xfd, 0xfe, 0xff])
            
            print(f"{COLOR_GREEN}SUCCESS: LED Settings saved successfully to device flash.{COLOR_RESET}")

        elif args.command == "bind":
            layer = args.layer
            is_knob = (args.type == "knob")
            
            if is_knob and not args.action:
                print(f"{COLOR_RED}[Error] Knob index requires an action trigger (--action ccw/press/cw).{COLOR_RESET}")
                sys.exit(1)
                
            key_id = to_key_id(is_knob, args.index, args.action)
            print(f"Resolved target key ID: {key_id} (Hex: 0x{key_id:02x} if applicable)")
            
            # Resolve keycode
            # If a single character, translate to standard HID code. Otherwise parse integer.
            target_code = 0
            if len(args.key) == 1:
                char = args.key.lower()
                # Basic standard layouts mappings
                if 'a' <= char <= 'z':
                    target_code = 4 + (ord(char) - ord('a'))
                elif '1' <= char <= '9':
                    target_code = 30 + (ord(char) - ord('1'))
                elif char == '0':
                    target_code = 39
                else:
                    try:
                        target_code = int(args.key)
                    except ValueError:
                        print(f"{COLOR_RED}[Error] Unrecognized key character '{args.key}'. Use standard integer HID scan codes.{COLOR_RESET}")
                        sys.exit(1)
            else:
                try:
                    target_code = int(args.key)
                except ValueError:
                    print(f"{COLOR_RED}[Error] Key must be a single letter/digit or an integer HID scan code.{COLOR_RESET}")
                    sys.exit(1)

            # Build modifier bitmask
            mod_mask = 0
            if args.ctrl:  mod_mask |= 0x01
            if args.shift: mod_mask |= 0x02
            if args.alt:   mod_mask |= 0x04
            if args.win:   mod_mask |= 0x08

            print(f"Binding Key: ID={key_id}, Keycode={target_code}, ModMask=0x{mod_mask:02x}, Delay={args.delay}ms...")

            # Packet 1: Bind start packet
            bind_report = [0] * 64
            bind_report[0] = 0xfe
            bind_report[1] = key_id
            bind_report[2] = layer
            bind_report[3] = 0x01  # Macro type: Keyboard
            bind_report[9] = 0x01  # Length: 1 press
            bind_report[10] = mod_mask
            bind_report[11] = target_code
            send_message(dev, bind_report)

            # Packet 2: Optional delay packet
            if args.delay > 0:
                if args.delay > 6000:
                    print(f"{COLOR_RED}[Error] Delay exceeds maximum supported limit of 6000ms.{COLOR_RESET}")
                    sys.exit(1)
                delay_report = [0] * 64
                delay_report[0] = 0xfe
                delay_report[1] = key_id
                delay_report[2] = layer
                delay_report[3] = 0x05  # Type: Delay
                delay_report[4] = args.delay & 0xff
                delay_report[5] = (args.delay >> 8) & 0xff
                send_message(dev, delay_report)

            # Commit sequence
            print("Committing flash transaction changes to device memory...")
            commit_transaction(dev)
            
            print(f"{COLOR_GREEN}SUCCESS: Key command mapped and flashed successfully to device memory!{COLOR_RESET}")

        dev.close()
    except Exception as e:
        print(f"{COLOR_RED}[Error] Transaction failed - {e}{COLOR_RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main()
