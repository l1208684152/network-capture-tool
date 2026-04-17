# Network Capture Tool

A computer-side network packet capture tool with anti-crawler features, allowing users to capture packets for specific processes with a user-friendly interface.

## Features

- **Process-specific packet capture**: Capture network packets for a specific process
- **Anti-crawler tools**: User-Agent management, proxy testing, and browser fingerprinting
- **User-friendly interface**: Tkinter-based GUI with real-time packet display
- **Network interface selection**: Automatically selects the best network interface
- **Detailed packet analysis**: View packet details, statistics, and anti-crawler analysis
- **Cross-platform compatibility**: Works on Windows, macOS, and Linux

## Requirements

- Python 3.7+
- Python packages:
  - psutil
  - pandas
  - requests
  - scapy

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/l1208684152/network-capture-tool.git
   cd network-capture-tool
   ```
2. Run the tool:
   ```bash
   python network_capture_tool/main.py
   ```

**Note**: The tool will automatically install required Python packages if they are not already installed.

## Usage

1. Launch the tool
2. Select a process from the process list
3. Click "Start Capture" to begin capturing packets
4. View captured packets in the results table
5. Use the anti-crawler tools as needed

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License
