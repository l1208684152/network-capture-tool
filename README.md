# Network Capture Tool

## ⚠️ 安全警告 ⚠️

**重要安全提示：本工具仅用于本地测试，禁止在生产环境或公网使用！**

- **CA证书风险**：生成的CA证书仅用于本地抓包测试，**禁止安装到系统或浏览器的信任证书存储**
- **私钥安全**：CA私钥已加密存储，但仍应注意保护
- **敏感数据**：抓包可能会捕获到密码、token等敏感信息，请谨慎使用
- **使用后清理**：使用完成后请确保停止代理并清理生成的证书文件
- **法律合规**：请确保在合法范围内使用本工具，遵守相关法律法规

---

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

### Security Warning

**IMPORTANT: CA Certificate Security**
- The CA certificate is only intended for local packet capture testing
- Do NOT install the CA certificate into your system or browser's trusted certificate store
- After testing, please delete the generated CA certificate files
- Using the CA certificate in a production environment or on public networks poses serious security risks
- If you have previously installed the CA certificate, please remove it immediately

**Security Risk**: If the CA private key is compromised, attackers can:
1. Create fraudulent HTTPS certificates for any website
2. Perform man-in-the-middle attacks to intercept encrypted traffic
3. Steal sensitive information including passwords, payment details, and personal data

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 安全使用指南

### 如何安全生成/删除CA证书

**生成CA证书**：
1. 启动工具，点击"启动代理"按钮
2. 工具会自动生成加密存储的CA证书和私钥
3. 不要将生成的CA证书安装到系统或浏览器的信任区

**删除CA证书**：
1. 点击"停止代理"按钮，工具会自动清理所有证书文件
2. 如果需要手动清理，请删除 `network_capture_tool/core/certs/` 目录下的所有文件
3. 从浏览器或系统中移除已安装的CA证书（如果有）

### 如何限制抓包范围

**只抓特定进程**：
1. 在"进程选择"下拉菜单中选择目标进程
2. 点击"开始抓包"按钮，只抓取该进程的网络流量

**只抓特定接口**：
1. 在"接口选择"下拉菜单中选择目标网络接口
2. 建议选择本地回环接口（127.0.0.1）以减少捕获的流量

**只抓特定协议**：
1. 在"协议过滤"选项中选择目标协议（HTTP/HTTPS）
2. 这样可以只捕获感兴趣的协议流量

### 安全最佳实践

1. **最小权限**：仅使用必要的权限运行工具
2. **敏感数据**：避免在公共场所使用本工具，防止敏感信息泄露
3. **定期更新**：定期更新依赖库，确保使用安全版本
4. **网络隔离**：在测试环境中使用，避免在生产网络中使用
5. **日志管理**：定期清理抓包日志，避免敏感信息长期存储

## 依赖与安全

### 依赖库

- **pyOpenSSL**: 用于生成和管理证书
- **cryptography**: 用于加密存储CA私钥
- **scapy**: 用于网络数据包捕获和分析
- **psutil**: 用于进程管理
- **tkinter**: 用于GUI界面

### 安全版本建议

- pyOpenSSL >= 23.2.0
- cryptography >= 41.0.0
- scapy >= 2.5.0
- psutil >= 5.9.0

### 漏洞扫描

建议定期使用以下工具扫描依赖漏洞：
- `pip audit`
- `safety check`

## License

MIT License
