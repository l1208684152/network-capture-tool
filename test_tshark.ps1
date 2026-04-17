# 设置Wireshark路径
$wireSharkPath = "F:\Wireshark"
$tsharkPath = "$wireSharkPath\tshark.exe"

Write-Host "测试tshark命令行工具..."
Write-Host "TSHARK_PATH: $tsharkPath"

# 检查tshark是否存在
if (-not (Test-Path $tsharkPath))
{
    Write-Host "错误: tshark不存在于路径 $tsharkPath" -ForegroundColor Red
    Read-Host "按Enter键退出"
    exit 1
}

Write-Host "tshark存在，路径正确" -ForegroundColor Green

# 列出可用网络接口
Write-Host "列出可用网络接口..."
& $tsharkPath -D

# 测试抓包（使用第一个接口，捕获10个数据包）
Write-Host ""
Write-Host "开始捕获数据包，将捕获10个数据包，超时10秒..."
Write-Host "请在此期间进行网络活动，例如打开网页或刷新页面"
& $tsharkPath -i 1 -c 10 -T fields -e frame.time -e ip.src -e ip.dst -e tcp.srcport -e tcp.dstport -e udp.srcport -e udp.dstport -e frame.len

Write-Host ""
Write-Host "抓包测试完成"
Read-Host "按Enter键退出"
