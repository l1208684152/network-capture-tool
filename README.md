# Network Capture Tool

A computer-side network packet capture tool with anti-crawler features, allowing users to capture packets for specific processes with a user-friendly interface.

## Features

- **Process-specific packet capture**: Capture network packets for a specific process
- **Anti-crawler tools**: User-Agent management, proxy testing, and browser fingerprinting
- **User-friendly interface**: Tkinter-based GUI with real-time packet display
- **Network interface selection**: Automatically selects the best network interface
- **Detailed packet analysis**: View packet details, statistics, and anti-crawler analysis
- **HTTPS decryption**: MITM proxy for decrypting HTTPS traffic
- **Cross-platform compatibility**: Works on Windows, macOS, and Linux

## Requirements

- Python 3.7+
- Python packages:
  - psutil
  - pandas
  - requests
  - scapy
  - pyOpenSSL

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

### Basic Usage
1. Launch the tool
2. Select a process from the process list
3. Click "Start Capture" to begin capturing packets
4. View captured packets in the results table
5. Use the anti-crawler tools as needed

### HTTPS Decryption
1. In the "HTTPS解密" section, check "启用HTTPS解密"
2. Set the proxy port (default: 8888)
3. Click "启动代理" to start the MITM proxy
4. Follow the instructions to install the CA certificate in your browser
5. Configure your browser to use the proxy: `https://127.0.0.1:8888`
6. Start capturing packets - you will now see decrypted HTTPS content

**Note**: The CA certificate is generated automatically and stored in the `network_capture_tool/core/certs/` directory.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License
