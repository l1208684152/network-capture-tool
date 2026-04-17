@echo off

REM 设置Wireshark路径
set WIRESHARK_PATH=F:\Wireshark
set TSHARK_PATH=%WIRESHARK_PATH%\tshark.exe

echo 测试tshark命令行工具...
echo TSHARK_PATH: %TSHARK_PATH%

REM 检查tshark是否存在
if not exist "%TSHARK_PATH%" (
    echo 错误: tshark不存在于路径 %TSHARK_PATH%
    pause
    exit /b 1
)

echo tshark存在，路径正确

REM 列出可用网络接口
echo 列出可用网络接口...
"%TSHARK_PATH%" -D

REM 测试抓包（使用第一个接口，捕获10个数据包）
echo.
echo 开始捕获数据包，将捕获10个数据包，超时10秒...
echo 请在此期间进行网络活动，例如打开网页或刷新页面
"%TSHARK_PATH%" -i 1 -c 10 -T fields -e frame.time -e ip.src -e ip.dst -e tcp.srcport -e tcp.dstport -e udp.srcport -e udp.dstport -e frame.len

echo.
echo 抓包测试完成
pause
