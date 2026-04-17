import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import pandas as pd
import os
import threading
from queue import Queue
import sys
import logging
from datetime import datetime

from core.dependency_manager import DependencyManager
from core.capture_engine import CaptureEngine
from core.anti_crawler_tool import AntiCrawlerTool

class NetworkCaptureTool:
    """网络抓包工具主类"""
    
    def __init__(self, root):
        # 设置tcl/tk路径
        if hasattr(sys, 'frozen'):
            os.environ['TCL_LIBRARY'] = os.path.join(os.path.dirname(sys.executable), 'tcl', 'tcl8.6')
            os.environ['TK_LIBRARY'] = os.path.join(os.path.dirname(sys.executable), 'tcl', 'tk8.6')
        else:
            # 尝试获取Python安装路径
            python_path = sys.executable.replace('python.exe', '')
            os.environ['TCL_LIBRARY'] = os.path.join(python_path, 'tcl', 'tcl8.6')
            os.environ['TK_LIBRARY'] = os.path.join(python_path, 'tcl', 'tk8.6')
        
        self.root = root
        self.root.title("电脑端网络抓包工具")
        self.root.geometry("1200x800")
        
        # 核心状态属性
        self.running = False
        self.paused = False
        self.queue = Queue()
        self.captured_packets = []
        self.processes = []
        self.selected_processes = []
        
        # 性能优化相关属性
        self.max_packets = 10000  # 最大保存的数据包数量
        self.batch_update_size = 10  # 批量更新UI的数据包数量
        self.packet_batch = []  # 批量更新的数据包
        self.ui_update_pending = False  # UI更新标志
        
        # 数据包存储字典，用于通过item ID快速查找数据包
        self.packet_dict = {}
        
        # 初始化组件
        self.dependency_manager = DependencyManager()
        self.capture_engine = CaptureEngine(self.queue)
        self.anti_crawler_tool = AntiCrawlerTool()
        
        # 设置UI
        self.setup_ui()
        # 加载进程列表
        self.load_processes()
    
    def setup_ui(self):
        """设置用户界面"""
        # 设置窗口图标
        try:
            # 尝试设置窗口图标
            pass
        except:
            pass
        
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 顶部：进程选择区域
        process_frame = ttk.LabelFrame(main_frame, text="进程选择", padding=(5, 5))
        process_frame.pack(fill=tk.X, pady=5)
        
        # 进程搜索框
        search_frame = ttk.Frame(process_frame)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(search_frame, text="搜索进程：").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40)
        self.search_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.search_entry.bind('<KeyRelease>', self.filter_processes)
        
        # 刷新进程按钮
        ttk.Button(search_frame, text="刷新进程", command=self.load_processes).pack(side=tk.RIGHT, padx=5)
        
        # 进程列表
        self.process_tree = ttk.Treeview(process_frame, columns=('pid', 'name', 'cpu', 'memory', 'path', 'create_time'), show='headings', selectmode='browse')
        self.process_tree.heading('pid', text='进程ID')
        self.process_tree.heading('name', text='进程名')
        self.process_tree.heading('cpu', text='CPU%')
        self.process_tree.heading('memory', text='内存%')
        self.process_tree.heading('path', text='进程路径')
        self.process_tree.heading('create_time', text='启动时间')
        self.process_tree.column('pid', width=80, anchor=tk.CENTER)
        self.process_tree.column('name', width=200, anchor=tk.W)
        self.process_tree.column('cpu', width=80, anchor=tk.CENTER)
        self.process_tree.column('memory', width=80, anchor=tk.CENTER)
        self.process_tree.column('path', width=300, anchor=tk.W)
        self.process_tree.column('create_time', width=150, anchor=tk.CENTER)
        
        # 添加进程列表的右键菜单
        self.process_tree.bind('<Button-3>', self.show_process_context_menu)
        
        scrollbar = ttk.Scrollbar(process_frame, orient=tk.VERTICAL, command=self.process_tree.yview)
        self.process_tree.configure(yscroll=scrollbar.set)
        
        self.process_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        # 中间：控制按钮区域
        control_frame = ttk.LabelFrame(main_frame, text="抓包控制", padding=(5, 5))
        control_frame.pack(fill=tk.X, pady=5)
        
        # 状态显示
        status_container = ttk.Frame(control_frame)
        status_container.pack(side=tk.LEFT, padx=10, pady=5, fill=tk.X, expand=True)
        
        ttk.Label(status_container, text="状态：").pack(side=tk.LEFT, padx=5)
        self.status_var = tk.StringVar(value="就绪")
        self.status_label = ttk.Label(status_container, textvariable=self.status_var, font=('Arial', 10, 'bold'))
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # 数据包计数
        self.packet_count_var = tk.StringVar(value="数据包：0")
        ttk.Label(status_container, textvariable=self.packet_count_var).pack(side=tk.RIGHT, padx=10)
        
        # 按钮区域
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(side=tk.RIGHT, padx=10, pady=5)
        
        # 开始抓包按钮
        self.start_btn = ttk.Button(button_frame, text="开始抓包", command=self.start_capture, style='Primary.TButton')
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        # 暂停按钮
        self.pause_btn = ttk.Button(button_frame, text="暂停", command=self.pause_capture, state=tk.DISABLED)
        self.pause_btn.pack(side=tk.LEFT, padx=5)
        
        # 停止按钮
        self.stop_btn = ttk.Button(button_frame, text="停止", command=self.stop_capture, state=tk.DISABLED, style='Danger.TButton')
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # 保存结果按钮
        self.save_btn = ttk.Button(button_frame, text="保存结果", command=self.save_capture, state=tk.DISABLED, style='Success.TButton')
        self.save_btn.pack(side=tk.LEFT, padx=5)
        
        # 主题切换按钮
        self.theme_btn = ttk.Button(button_frame, text="切换主题", command=self.toggle_theme)
        self.theme_btn.pack(side=tk.LEFT, padx=5)
        
        # 反爬虫工具区域
        anti_crawler_frame = ttk.LabelFrame(main_frame, text="反爬虫工具", padding=(5, 5))
        anti_crawler_frame.pack(fill=tk.X, pady=5)
        
        # 创建一个容器来放置三个子框架
        anti_crawler_container = ttk.Frame(anti_crawler_frame)
        anti_crawler_container.pack(fill=tk.X, padx=5, pady=5)
        
        # UA管理
        ua_frame = ttk.LabelFrame(anti_crawler_container, text="User-Agent管理", padding=(5, 5))
        ua_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        ttk.Label(ua_frame, text="常用UA：").grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)
        self.ua_combobox = ttk.Combobox(ua_frame, width=40)
        self.ua_combobox.grid(row=0, column=1, padx=5, pady=2, sticky=tk.W)
        self.load_common_ua()
        
        ttk.Button(ua_frame, text="随机生成UA", command=self.generate_random_ua).grid(row=1, column=0, padx=5, pady=2, sticky=tk.W)
        ttk.Button(ua_frame, text="复制UA", command=self.copy_ua).grid(row=1, column=1, padx=5, pady=2, sticky=tk.W)
        
        # 代理管理
        proxy_frame = ttk.LabelFrame(anti_crawler_container, text="代理管理", padding=(5, 5))
        proxy_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        ttk.Label(proxy_frame, text="代理地址：").grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)
        self.proxy_entry = ttk.Entry(proxy_frame, width=25)
        self.proxy_entry.grid(row=0, column=1, padx=5, pady=2, sticky=tk.W)
        ttk.Button(proxy_frame, text="测试代理", command=self.test_proxy).grid(row=0, column=2, padx=5, pady=2)
        
        # 浏览器指纹和请求头管理
        fingerprint_frame = ttk.LabelFrame(anti_crawler_container, text="浏览器指纹和请求头", padding=(5, 5))
        fingerprint_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        ttk.Button(fingerprint_frame, text="生成浏览器指纹", command=self.generate_browser_fingerprint).grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)
        ttk.Button(fingerprint_frame, text="生成请求头模板", command=self.generate_request_headers).grid(row=0, column=1, padx=5, pady=2, sticky=tk.W)
        ttk.Button(fingerprint_frame, text="复制请求头", command=self.copy_request_headers).grid(row=1, column=0, padx=5, pady=2, sticky=tk.W)
        
        # 请求头显示区域
        self.headers_text = scrolledtext.ScrolledText(fingerprint_frame, wrap=tk.WORD, height=3, font=('Consolas', 9))
        self.headers_text.grid(row=2, column=0, columnspan=2, padx=5, pady=2, sticky=tk.W+tk.E)
        
        # 底部：抓包结果显示区域
        result_frame = ttk.LabelFrame(main_frame, text="抓包结果", padding=(5, 5))
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 抓包结果表格
        self.result_tree = ttk.Treeview(result_frame, columns=(
            'no', 'time', 'src', 'dst', 'proto', 'src_port', 'dst_port', 'length', 'info'
        ), show='headings')
        
        # 设置列标题和宽度
        self.result_tree.heading('no', text='序号', command=lambda: self.sort_treeview('no', False))
        self.result_tree.heading('time', text='时间', command=lambda: self.sort_treeview('time', False))
        self.result_tree.heading('src', text='源IP', command=lambda: self.sort_treeview('src', False))
        self.result_tree.heading('dst', text='目标IP', command=lambda: self.sort_treeview('dst', False))
        self.result_tree.heading('proto', text='协议', command=lambda: self.sort_treeview('proto', False))
        self.result_tree.heading('src_port', text='源端口', command=lambda: self.sort_treeview('src_port', False))
        self.result_tree.heading('dst_port', text='目标端口', command=lambda: self.sort_treeview('dst_port', False))
        self.result_tree.heading('length', text='长度', command=lambda: self.sort_treeview('length', False))
        self.result_tree.heading('info', text='信息', command=lambda: self.sort_treeview('info', False))
        
        self.result_tree.column('no', width=50, anchor=tk.CENTER)
        self.result_tree.column('time', width=150, anchor=tk.CENTER)
        self.result_tree.column('src', width=120, anchor=tk.CENTER)
        self.result_tree.column('dst', width=120, anchor=tk.CENTER)
        self.result_tree.column('proto', width=60, anchor=tk.CENTER)
        self.result_tree.column('src_port', width=80, anchor=tk.CENTER)
        self.result_tree.column('dst_port', width=80, anchor=tk.CENTER)
        self.result_tree.column('length', width=60, anchor=tk.CENTER)
        self.result_tree.column('info', width=300, anchor=tk.W)
        
        # 添加结果列表的右键菜单
        self.result_tree.bind('<Button-3>', self.show_result_context_menu)
        
        # 添加滚动条
        y_scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        x_scrollbar = ttk.Scrollbar(result_frame, orient=tk.HORIZONTAL, command=self.result_tree.xview)
        self.result_tree.configure(yscroll=y_scrollbar.set, xscroll=x_scrollbar.set)
        
        # 放置控件
        self.result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X, padx=5)
        
        # 数据包详情区域
        detail_frame = ttk.LabelFrame(result_frame, text="数据包详情", padding=(5, 5))
        detail_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)
        
        # 详情标签页
        self.notebook = ttk.Notebook(detail_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 原始详情
        self.raw_detail_text = scrolledtext.ScrolledText(self.notebook, wrap=tk.WORD, height=5, font=('Consolas', 9))
        self.notebook.add(self.raw_detail_text, text="原始数据")
        
        # 内容解析
        self.content_detail_text = scrolledtext.ScrolledText(self.notebook, wrap=tk.WORD, height=5, font=('Consolas', 9))
        self.notebook.add(self.content_detail_text, text="内容解析")
        
        # 反爬虫分析
        self.anti_crawler_text = scrolledtext.ScrolledText(self.notebook, wrap=tk.WORD, height=5, font=('Consolas', 9))
        self.notebook.add(self.anti_crawler_text, text="反爬虫分析")
        
        # 统计信息
        self.stats_text = scrolledtext.ScrolledText(self.notebook, wrap=tk.WORD, height=5, font=('Consolas', 9))
        self.notebook.add(self.stats_text, text="统计信息")
        
        # 数据包过滤
        filter_frame = ttk.Frame(detail_frame)
        filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(filter_frame, text="过滤条件：").pack(side=tk.LEFT, padx=5)
        self.filter_var = tk.StringVar()
        self.filter_entry = ttk.Entry(filter_frame, textvariable=self.filter_var, width=50)
        self.filter_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(filter_frame, text="应用过滤", command=self.apply_filter).pack(side=tk.RIGHT, padx=5)
        
        self.result_tree.bind('<<TreeviewSelect>>', self.show_packet_detail)
        # 添加双击事件处理
        self.result_tree.bind('<Double-1>', self.on_packet_double_click)
        
        # 状态栏
        self.status_bar = ttk.Label(self.root, text="就绪 - 等待用户操作", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 初始化右键菜单
        self.setup_context_menus()
        
        # 主题设置
        self.theme = 'light'
        self.set_theme('light')
    
    def load_processes(self):
        """加载所有运行中的进程"""
        import psutil
        
        self.processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'exe', 'create_time']):
            try:
                # 获取进程路径
                exe_path = proc.info['exe'] if proc.info['exe'] else 'N/A'
                # 获取进程启动时间
                create_time = datetime.fromtimestamp(proc.info['create_time']).strftime('%Y-%m-%d %H:%M:%S') if proc.info['create_time'] else 'N/A'
                
                self.processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'cpu': proc.info['cpu_percent'],
                    'memory': proc.info['memory_percent'],
                    'path': exe_path,
                    'create_time': create_time
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # 按进程名排序
        self.processes.sort(key=lambda x: x['name'])
        # 更新进程列表
        self.update_process_list()
    
    def update_process_list(self):
        """更新进程列表显示"""
        # 清空现有列表
        for item in self.process_tree.get_children():
            self.process_tree.delete(item)
        
        # 添加进程到列表
        for proc in self.processes:
            self.process_tree.insert('', tk.END, values=(
                proc['pid'], proc['name'], f"{proc['cpu']:.1f}%", f"{proc['memory']:.1f}%",
                proc['path'], proc['create_time']
            ))
    
    def filter_processes(self, event=None):
        """根据搜索条件过滤进程"""
        search_term = self.search_var.get().lower()
        if not search_term:
            self.update_process_list()
            return
        
        # 清空现有列表
        for item in self.process_tree.get_children():
            self.process_tree.delete(item)
        
        # 添加匹配的进程
        for proc in self.processes:
            if (search_term in proc['name'].lower() or 
                search_term in str(proc['pid']) or 
                search_term in proc['path'].lower()):
                self.process_tree.insert('', tk.END, values=(
                    proc['pid'], proc['name'], f"{proc['cpu']:.1f}%", f"{proc['memory']:.1f}%",
                    proc['path'], proc['create_time']
                ))
    
    def start_capture(self):
        """开始抓包"""
        # 获取选中的进程
        selected_items = self.process_tree.selection()
        if not selected_items:
            messagebox.showwarning("提示", "请先选择一个进程！")
            return
        
        # 获取选中进程的PID
        selected_item = selected_items[0]
        proc_pid = int(self.process_tree.item(selected_item)['values'][0])
        proc_name = self.process_tree.item(selected_item)['values'][1]
        
        self.selected_processes = [{"pid": proc_pid, "name": proc_name}]
        
        # 设置状态
        self.running = True
        self.paused = False
        self.captured_packets = []
        
        # 更新UI
        self.start_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.NORMAL)
        self.save_btn.config(state=tk.DISABLED)
        self.status_var.set(f"正在抓包：{proc_name} (PID: {proc_pid})")
        
        # 清空结果列表
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        
        # 启动抓包线程
        self.capture_engine.start_capture(proc_pid)
        
        # 开始处理队列
        self.root.after(100, self.process_queue)
    
    def pause_capture(self):
        """暂停抓包"""
        self.paused = not self.paused
        self.capture_engine.pause_capture(self.paused)
        
        if self.paused:
            self.pause_btn.config(text="继续")
            self.status_var.set(f"抓包已暂停：{self.selected_processes[0]['name']} (PID: {self.selected_processes[0]['pid']})")
        else:
            self.pause_btn.config(text="暂停")
            self.status_var.set(f"正在抓包：{self.selected_processes[0]['name']} (PID: {self.selected_processes[0]['pid']})")
    
    def stop_capture(self):
        """停止抓包"""
        self.running = False
        self.capture_engine.stop_capture()
        
        # 更新UI
        self.start_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED, text="暂停")
        self.stop_btn.config(state=tk.DISABLED)
        self.save_btn.config(state=tk.NORMAL)
        self.status_var.set(f"抓包已停止，共捕获 {len(self.captured_packets)} 个数据包")
    
    def process_queue(self):
        """处理队列中的数据包"""
        try:
            while True:
                item = self.queue.get_nowait()
                
                if isinstance(item, tuple) and item[0] == 'error':
                    messagebox.showerror("抓包错误", f"抓包过程中发生错误：{item[1]}")
                    self.stop_capture()
                elif isinstance(item, tuple) and item[0] == 'update':
                    # 更新状态信息
                    self.status_var.set(item[1])
                elif isinstance(item, dict):
                    # 只有字典类型的item才是数据包
                    # 添加到数据包列表
                    self.captured_packets.append(item)
                    
                    # 数据包自动清理
                    if len(self.captured_packets) > self.max_packets:
                        # 保留最近的数据包
                        self.captured_packets = self.captured_packets[-self.max_packets:]
                        logging.info(f"数据包数量超过上限，已清理到 {self.max_packets} 个")
                    
                    # 批量更新UI
                    self.packet_batch.append(item)
                    if len(self.packet_batch) >= self.batch_update_size and not self.ui_update_pending:
                        self.ui_update_pending = True
                        # 调整更新间隔，根据数据包数量动态调整
                        update_interval = max(20, min(100, 100 - len(self.packet_batch) * 2))
                        self.root.after(update_interval, self.update_ui_batch)
        except:
            pass
        
        # 继续监听队列
        if self.running:
            self.root.after(50, self.process_queue)
    
    def update_ui_batch(self):
        """批量更新UI"""
        if not self.packet_batch:
            self.ui_update_pending = False
            return
        
        try:
            # 批量插入数据包
            for item in self.packet_batch:
                # 插入数据包并获取item ID
                item_id = self.result_tree.insert('', tk.END, values=(
                    item['no'], item['time'], item['src'], item['dst'], 
                    item['proto'], item['src_port'], item['dst_port'], 
                    item['length'], item['info']
                ))
                # 将数据包存储在字典中，使用item ID作为键
                self.packet_dict[item_id] = item
            
            # 更新数据包计数
            self.packet_count_var.set(f"数据包：{len(self.captured_packets)}")
            
            # 滚动到最后一行
            self.result_tree.yview_moveto(1.0)
            
            # 清空批次
            self.packet_batch = []
        except Exception as e:
            logging.error(f"更新UI失败: {str(e)}")
        finally:
            self.ui_update_pending = False
    
    def load_common_ua(self):
        """加载常用User-Agent列表"""
        self.ua_combobox['values'] = self.anti_crawler_tool.common_ua
        if self.anti_crawler_tool.common_ua:
            self.ua_combobox.current(0)
    
    def generate_random_ua(self):
        """生成随机User-Agent"""
        ua = self.anti_crawler_tool.generate_random_ua()
        self.ua_combobox.set(ua)
    
    def copy_ua(self):
        """复制当前UA到剪贴板"""
        ua = self.ua_combobox.get()
        if ua:
            self.root.clipboard_clear()
            self.root.clipboard_append(ua)
            messagebox.showinfo("成功", "UA已复制到剪贴板！")
    
    def generate_browser_fingerprint(self):
        """生成浏览器指纹"""
        user_agent = self.ua_combobox.get()
        if not user_agent:
            user_agent = self.anti_crawler_tool.common_ua[0]
        
        fingerprint = self.anti_crawler_tool.generate_browser_fingerprint(user_agent)
        
        # 显示指纹信息
        fingerprint_info = "=== 浏览器指纹 ===\n"
        for key, value in fingerprint.items():
            fingerprint_info += f"{key}: {value}\n"
        
        messagebox.showinfo("浏览器指纹", fingerprint_info)
        logging.info(f"生成浏览器指纹: {fingerprint['browser']} {fingerprint['browser_version']}")
    
    def generate_request_headers(self):
        """生成请求头模板"""
        user_agent = self.ua_combobox.get()
        if not user_agent:
            user_agent = self.anti_crawler_tool.common_ua[0]
        
        headers = self.anti_crawler_tool.generate_request_headers(user_agent)
        
        # 转换为字符串格式
        headers_str = """
# 请求头模板
headers = {
"""
        
        for key, value in headers.items():
            headers_str += f'    "{key}": "{value}",\n'
        
        headers_str += "}"
        
        # 显示请求头
        self.headers_text.delete(1.0, tk.END)
        self.headers_text.insert(tk.END, headers_str)
        
        logging.info("生成请求头模板")
    
    def copy_request_headers(self):
        """复制请求头到剪贴板"""
        headers_text = self.headers_text.get(1.0, tk.END).strip()
        if headers_text:
            self.root.clipboard_clear()
            self.root.clipboard_append(headers_text)
            messagebox.showinfo("成功", "请求头已复制到剪贴板！")
            logging.info("请求头已复制到剪贴板")
    
    def test_proxy(self):
        """测试代理是否可用"""
        proxy = self.proxy_entry.get().strip()
        if not proxy:
            messagebox.showwarning("提示", "请先输入代理地址！")
            return
        
        def proxy_test_thread():
            success, message = self.anti_crawler_tool.test_proxy(proxy)
            if success:
                messagebox.showinfo("测试成功", message)
            else:
                messagebox.showerror("测试失败", message)
        
        # 启动线程测试代理
        threading.Thread(target=proxy_test_thread, daemon=True).start()
    
    def toggle_theme(self):
        """切换主题"""
        if self.theme == 'light':
            self.set_theme('dark')
        else:
            self.set_theme('light')
    
    def setup_context_menus(self):
        """设置右键菜单"""
        # 进程列表右键菜单
        self.process_menu = tk.Menu(self.root, tearoff=0)
        self.process_menu.add_command(label="刷新进程", command=self.load_processes)
        self.process_menu.add_command(label="开始抓包", command=self.start_capture)
        self.process_menu.add_separator()
        self.process_menu.add_command(label="查看进程详情", command=self.show_process_detail)
        
        # 结果列表右键菜单
        self.result_menu = tk.Menu(self.root, tearoff=0)
        self.result_menu.add_command(label="清空结果", command=self.clear_results)
        self.result_menu.add_command(label="保存结果", command=self.save_capture)
        self.result_menu.add_separator()
        self.result_menu.add_command(label="复制选中项", command=self.copy_selected_result)
        self.result_menu.add_command(label="查看详细信息", command=self.show_packet_detail)
        self.result_menu.add_separator()
        self.result_menu.add_command(label="应用过滤", command=self.apply_filter)
    
    def show_process_context_menu(self, event):
        """显示进程列表右键菜单"""
        item = self.process_tree.identify_row(event.y)
        if item:
            self.process_tree.selection_set(item)
            self.process_menu.post(event.x_root, event.y_root)
    
    def show_result_context_menu(self, event):
        """显示结果列表右键菜单"""
        item = self.result_tree.identify_row(event.y)
        if item:
            self.result_tree.selection_set(item)
            self.result_menu.post(event.x_root, event.y_root)
    
    def clear_results(self):
        """清空结果列表"""
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        self.captured_packets = []
        self.packet_dict = {}  # 清空数据包字典
        self.packet_count_var.set("数据包：0")
        self.raw_detail_text.delete(1.0, tk.END)
        self.anti_crawler_text.delete(1.0, tk.END)
        self.stats_text.delete(1.0, tk.END)
    
    def copy_selected_result(self):
        """复制选中的结果项"""
        selected_items = self.result_tree.selection()
        if not selected_items:
            return
        
        selected_item = selected_items[0]
        values = self.result_tree.item(selected_item, 'values')
        if values:
            result_text = '\t'.join(str(v) for v in values)
            self.root.clipboard_clear()
            self.root.clipboard_append(result_text)
    
    def show_process_detail(self):
        """显示进程详情"""
        selected_items = self.process_tree.selection()
        if not selected_items:
            return
        
        selected_item = selected_items[0]
        values = self.process_tree.item(selected_item, 'values')
        if values:
            pid, name, cpu, memory, path, create_time = values
            detail = f"进程ID: {pid}\n"
            detail += f"进程名: {name}\n"
            detail += f"CPU使用率: {cpu}\n"
            detail += f"内存使用率: {memory}\n"
            detail += f"进程路径: {path}\n"
            detail += f"启动时间: {create_time}\n"
            messagebox.showinfo("进程详情", detail)
    
    def apply_filter(self):
        """应用过滤条件"""
        filter_text = self.filter_var.get().lower()
        if not filter_text:
            # 没有过滤条件，显示所有结果
            for item in self.result_tree.get_children():
                self.result_tree.item(item, tags=())
            return
        
        # 应用过滤
        for item in self.result_tree.get_children():
            values = self.result_tree.item(item, 'values')
            if values:
                # 检查是否匹配过滤条件
                match = any(filter_text in str(v).lower() for v in values)
                if match:
                    self.result_tree.item(item, tags=('matched',))
                else:
                    self.result_tree.item(item, tags=('unmatched',))
    
    def set_theme(self, theme):
        """设置主题"""
        self.theme = theme
        
        # 定义主题颜色
        if theme == 'dark':
            bg_color = '#2d2d2d'
            fg_color = '#ffffff'
            frame_bg = '#3a3a3a'
            entry_bg = '#4a4a4a'
            button_bg = '#5a5a5a'
            primary_bg = '#3498db'
            success_bg = '#27ae60'
            danger_bg = '#e74c3c'
        else:
            bg_color = '#ffffff'
            fg_color = '#000000'
            frame_bg = '#f0f0f0'
            entry_bg = '#ffffff'
            button_bg = '#e0e0e0'
            primary_bg = '#3498db'
            success_bg = '#27ae60'
            danger_bg = '#e74c3c'
        
        # 设置根窗口颜色
        self.root.configure(bg=bg_color)
        
        # 重新配置样式
        style = ttk.Style()
        style.configure('Custom.TLabelFrame', background=frame_bg)
        style.configure('Custom.TFrame', background=frame_bg)
        style.configure('TButton', background=button_bg, foreground=fg_color)
        style.configure('TEntry', fieldbackground=entry_bg, foreground=fg_color)
        style.configure('TLabel', background=bg_color, foreground=fg_color)
        style.configure('Treeview', background=entry_bg, foreground=fg_color, fieldbackground=entry_bg)
        style.configure('Treeview.Heading', background=button_bg, foreground=fg_color)
        
        # 自定义按钮样式
        style.configure('Primary.TButton', background=primary_bg, foreground='white')
        style.configure('Success.TButton', background=success_bg, foreground='white')
        style.configure('Danger.TButton', background=danger_bg, foreground='white')
        
        # 过滤结果样式
        style.configure('Treeview.tag.matched', background=entry_bg, foreground=fg_color)
        style.configure('Treeview.tag.unmatched', background='#ffcccc', foreground=fg_color)
        
        # 更新所有框架的颜色
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.LabelFrame):
                widget.configure(style='Custom.TLabelFrame')
            elif isinstance(widget, ttk.Frame):
                widget.configure(style='Custom.TFrame')
        
        # 更新状态栏
        self.status_bar.configure(background=frame_bg, foreground=fg_color)
        
        # 更新文本框
        text_widgets = [self.raw_detail_text, self.anti_crawler_text, self.headers_text, self.stats_text]
        for text_widget in text_widgets:
            text_widget.configure(bg=entry_bg, fg=fg_color)
        
        # 更新状态标签颜色
        if theme == 'dark':
            self.status_label.configure(foreground='#3498db')
        else:
            self.status_label.configure(foreground='#3498db')
        
        logging.info(f"主题已切换为: {theme}")
    
    def sort_treeview(self, column, reverse):
        """排序表格"""
        # 获取所有数据
        items = [(self.result_tree.set(k, column), k) for k in self.result_tree.get_children('')]
        
        # 排序
        items.sort(reverse=reverse)
        
        # 重新插入数据
        for index, (val, k) in enumerate(items):
            self.result_tree.move(k, '', index)
        
        # 切换排序方向
        self.result_tree.heading(column, command=lambda: self.sort_treeview(column, not reverse))
        
        logging.info(f"表格已按 {column} 排序")
    
    def show_packet_detail(self, event=None):
        """显示数据包详情"""
        selected_items = self.result_tree.selection()
        if not selected_items:
            return
        
        selected_item = selected_items[0]
        # 从packet_dict中获取数据包
        packet = self.packet_dict.get(selected_item)
        if packet:
            
            # 显示原始数据
            self.raw_detail_text.delete(1.0, tk.END)
            self.raw_detail_text.insert(tk.END, packet['raw'])
            
            # 显示内容解析
            content_detail = "=== 内容解析 ===\n"
            try:
                if 'content' in packet:
                    content = packet['content']
                    if content:
                        content_type = content.get('type', 'Unknown')
                        content_detail += f"类型: {content_type}\n\n"
                        
                        if content_type == 'HTTP Request':
                            content_detail += "HTTP请求信息:\n"
                            if 'method' in content:
                                content_detail += f"方法: {content['method']}\n"
                            if 'path' in content:
                                content_detail += f"路径: {content['path']}\n"
                            if 'version' in content:
                                content_detail += f"版本: {content['version']}\n"
                            if 'headers' in content:
                                content_detail += "\n请求头:\n"
                                for key, value in content['headers'].items():
                                    content_detail += f"  {key}: {value}\n"
                            if 'body' in content:
                                content_detail += "\n请求体:\n"
                                content_detail += content['body'][:1000] + ("..." if len(content['body']) > 1000 else "")
                        
                        elif content_type == 'HTTP Response':
                            content_detail += "HTTP响应信息:\n"
                            if 'version' in content:
                                content_detail += f"版本: {content['version']}\n"
                            if 'status' in content:
                                content_detail += f"状态码: {content['status']}\n"
                            if 'reason' in content:
                                content_detail += f"原因: {content['reason']}\n"
                            if 'headers' in content:
                                content_detail += "\n响应头:\n"
                                for key, value in content['headers'].items():
                                    content_detail += f"  {key}: {value}\n"
                            if 'body' in content:
                                content_detail += "\n响应体:\n"
                                content_detail += content['body'][:1000] + ("..." if len(content['body']) > 1000 else "")
                        
                        elif content_type == 'DNS Query':
                            content_detail += "DNS查询信息:\n"
                            if 'qname' in content:
                                content_detail += f"查询域名: {content['qname']}\n"
                            if 'qtype' in content:
                                content_detail += f"查询类型: {content['qtype']}\n"
                            if 'qclass' in content:
                                content_detail += f"查询类: {content['qclass']}\n"
                        
                        elif content_type == 'DNS Response':
                            content_detail += "DNS响应信息:\n"
                            if 'qr' in content:
                                content_detail += f"QR: {content['qr']}\n"
                            if 'rcode' in content:
                                content_detail += f"响应码: {content['rcode']}\n"
                            if 'ancount' in content:
                                content_detail += f"回答数: {content['ancount']}\n"
                        
                        elif content_type == 'Raw Data':
                            content_detail += "原始数据:\n"
                            if 'payload' in content:
                                content_detail += content['payload'][:1000] + ("..." if len(content['payload']) > 1000 else "")
                        
                        elif content_type == 'Binary Data':
                            content_detail += "二进制数据:\n"
                            if 'length' in content:
                                content_detail += f"长度: {content['length']} bytes\n"
                                content_detail += "（二进制数据已省略）"
                        
                        elif content_type == 'Basic Packet':
                            content_detail += "基本数据包信息:\n"
                            if 'protocol' in content:
                                content_detail += f"协议: {content['protocol']}\n"
                            if 'src_port' in content:
                                content_detail += f"源端口: {content['src_port']}\n"
                            if 'dst_port' in content:
                                content_detail += f"目标端口: {content['dst_port']}\n"
                    else:
                        content_detail += "Content为空字典\n"
                else:
                    content_detail += "无Content字段\n"
            except Exception as e:
                content_detail += f"显示内容解析失败: {str(e)}\n"
            
            self.content_detail_text.delete(1.0, tk.END)
            self.content_detail_text.insert(tk.END, content_detail)
            
            # 显示反爬虫分析（基于原始数据）
            analysis = "=== 反爬虫分析 ===\n"
            analysis += "基于原始数据的分析：\n"
            if 'HTTP' in packet['info']:
                analysis += "检测到HTTP流量\n"
            elif 'DNS' in packet['info']:
                analysis += "检测到DNS流量\n"
            analysis += f"协议: {packet['proto']}\n"
            analysis += f"源IP: {packet['src']}\n"
            analysis += f"目标IP: {packet['dst']}\n"
            self.anti_crawler_text.delete(1.0, tk.END)
            self.anti_crawler_text.insert(tk.END, analysis)
            
            # 显示统计信息
            stats = f"=== 数据包统计 ===\n"
            stats += f"序号: {packet['no']}\n"
            stats += f"时间: {packet['time']}\n"
            stats += f"源IP: {packet['src']}\n"
            stats += f"目标IP: {packet['dst']}\n"
            stats += f"协议: {packet['proto']}\n"
            stats += f"源端口: {packet['src_port']}\n"
            stats += f"目标端口: {packet['dst_port']}\n"
            stats += f"长度: {packet['length']}\n"
            stats += f"信息: {packet['info']}\n"
            
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(tk.END, stats)
    
    def on_packet_double_click(self, event):
        """处理数据包双击事件"""
        # 获取双击的项目
        item = self.result_tree.identify_row(event.y)
        if not item:
            return
        
        # 选中该项目
        self.result_tree.selection_set(item)
        
        # 从packet_dict中获取数据包
        packet = self.packet_dict.get(item)
        if packet:
            # 创建数据包详情弹窗
            PacketDetailWindow(self.root, packet)
    
    def save_capture(self):
        """保存抓包结果"""
        if not self.captured_packets:
            messagebox.showinfo("提示", "没有可保存的数据包！")
            return
        
        # 弹出文件保存对话框
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")],
            initialfile=f"capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        
        if not file_path:
            return
        
        try:
            # 准备数据
            data = []
            for packet in self.captured_packets:
                data.append({
                    '序号': packet['no'],
                    '时间': packet['time'],
                    '源IP': packet['src'],
                    '目标IP': packet['dst'],
                    '协议': packet['proto'],
                    '源端口': packet['src_port'],
                    '目标端口': packet['dst_port'],
                    '长度': packet['length'],
                    '信息': packet['info']
                })
            
            # 创建DataFrame并保存
            df = pd.DataFrame(data)
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            
            messagebox.showinfo("保存成功", f"抓包结果已保存到: {file_path}")
            logging.info(f"抓包结果已保存到: {file_path}")
        except Exception as e:
            messagebox.showerror("保存失败", f"保存抓包结果失败: {str(e)}")
            logging.error(f"保存抓包结果失败: {str(e)}")

class PacketDetailWindow:
    """数据包详情弹窗类"""
    
    def __init__(self, parent, packet):
        self.parent = parent
        self.packet = packet
        
        # 创建弹窗
        self.window = tk.Toplevel(parent)
        self.window.title(f"数据包详情 - 序号: {packet['no']}")
        self.window.geometry("900x700")
        self.window.transient(parent)  # 设置为父窗口的临时窗口
        self.window.grab_set()  # 模态窗口，禁止操作父窗口
        
        # 设置布局
        self.setup_ui()
    
    def setup_ui(self):
        """设置弹窗界面"""
        # 主框架
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 标签页
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 基本信息标签页
        basic_frame = ttk.Frame(notebook)
        notebook.add(basic_frame, text="基本信息")
        
        # 基本信息内容
        basic_text = scrolledtext.ScrolledText(basic_frame, wrap=tk.WORD, font=('Consolas', 9))
        basic_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        basic_info = f"=== 基本信息 ===\n"
        basic_info += f"序号: {self.packet['no']}\n"
        basic_info += f"时间: {self.packet['time']}\n"
        basic_info += f"源IP: {self.packet['src']}\n"
        basic_info += f"目标IP: {self.packet['dst']}\n"
        basic_info += f"协议: {self.packet['proto']}\n"
        basic_info += f"源端口: {self.packet['src_port']}\n"
        basic_info += f"目标端口: {self.packet['dst_port']}\n"
        basic_info += f"长度: {self.packet['length']}\n"
        basic_info += f"信息: {self.packet['info']}\n"
        
        basic_text.insert(tk.END, basic_info)
        
        # 原始数据标签页
        raw_frame = ttk.Frame(notebook)
        notebook.add(raw_frame, text="原始数据")
        
        raw_text = scrolledtext.ScrolledText(raw_frame, wrap=tk.WORD, font=('Consolas', 9))
        raw_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        raw_text.insert(tk.END, self.packet['raw'])
        
        # 内容解析标签页
        content_frame = ttk.Frame(notebook)
        notebook.add(content_frame, text="内容解析")
        
        content_text = scrolledtext.ScrolledText(content_frame, wrap=tk.WORD, font=('Consolas', 9))
        content_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        content_detail = "=== 内容解析 ===\n"
        try:
            if 'content' in self.packet:
                content = self.packet['content']
                if content:
                    content_type = content.get('type', 'Unknown')
                    content_detail += f"类型: {content_type}\n\n"
                    
                    if content_type == 'HTTP Request':
                        content_detail += "HTTP请求信息:\n"
                        if 'method' in content:
                            content_detail += f"方法: {content['method']}\n"
                        if 'path' in content:
                            content_detail += f"路径: {content['path']}\n"
                        if 'version' in content:
                            content_detail += f"版本: {content['version']}\n"
                        if 'headers' in content:
                            content_detail += "\n请求头:\n"
                            for key, value in content['headers'].items():
                                content_detail += f"  {key}: {value}\n"
                        if 'body' in content:
                            content_detail += "\n请求体:\n"
                            content_detail += content['body'] + ("..." if len(content['body']) > 5000 else "")
                    
                    elif content_type == 'HTTP Response':
                        content_detail += "HTTP响应信息:\n"
                        if 'version' in content:
                            content_detail += f"版本: {content['version']}\n"
                        if 'status' in content:
                            content_detail += f"状态码: {content['status']}\n"
                        if 'reason' in content:
                            content_detail += f"原因: {content['reason']}\n"
                        if 'headers' in content:
                            content_detail += "\n响应头:\n"
                            for key, value in content['headers'].items():
                                content_detail += f"  {key}: {value}\n"
                        if 'body' in content:
                            content_detail += "\n响应体:\n"
                            content_detail += content['body'] + ("..." if len(content['body']) > 5000 else "")
                    
                    elif content_type == 'DNS Query':
                        content_detail += "DNS查询信息:\n"
                        if 'qname' in content:
                            content_detail += f"查询域名: {content['qname']}\n"
                        if 'qtype' in content:
                            content_detail += f"查询类型: {content['qtype']}\n"
                        if 'qclass' in content:
                            content_detail += f"查询类: {content['qclass']}\n"
                    
                    elif content_type == 'DNS Response':
                        content_detail += "DNS响应信息:\n"
                        if 'qr' in content:
                            content_detail += f"QR: {content['qr']}\n"
                        if 'rcode' in content:
                            content_detail += f"响应码: {content['rcode']}\n"
                        if 'ancount' in content:
                            content_detail += f"回答数: {content['ancount']}\n"
                    
                    elif content_type == 'Raw Data':
                        content_detail += "原始数据:\n"
                        if 'payload' in content:
                            content_detail += content['payload'] + ("..." if len(content['payload']) > 5000 else "")
                    
                    elif content_type == 'Binary Data':
                        content_detail += "二进制数据:\n"
                        if 'length' in content:
                            content_detail += f"长度: {content['length']} bytes\n"
                            content_detail += "（二进制数据已省略）"
                    
                    elif content_type == 'Basic Packet':
                        content_detail += "基本数据包信息:\n"
                        if 'protocol' in content:
                            content_detail += f"协议: {content['protocol']}\n"
                        if 'src_port' in content:
                            content_detail += f"源端口: {content['src_port']}\n"
                        if 'dst_port' in content:
                            content_detail += f"目标端口: {content['dst_port']}\n"
                else:
                    content_detail += "Content为空字典\n"
            else:
                content_detail += "无Content字段\n"
        except Exception as e:
            content_detail += f"显示内容解析失败: {str(e)}\n"
        
        content_text.insert(tk.END, content_detail)
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="复制内容", command=self.copy_content).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="关闭", command=self.window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def copy_content(self):
        """复制内容到剪贴板"""
        # 复制基本信息
        basic_info = f"序号: {self.packet['no']}\n"
        basic_info += f"时间: {self.packet['time']}\n"
        basic_info += f"源IP: {self.packet['src']}\n"
        basic_info += f"目标IP: {self.packet['dst']}\n"
        basic_info += f"协议: {self.packet['proto']}\n"
        basic_info += f"源端口: {self.packet['src_port']}\n"
        basic_info += f"目标端口: {self.packet['dst_port']}\n"
        basic_info += f"长度: {self.packet['length']}\n"
        basic_info += f"信息: {self.packet['info']}\n"
        
        # 复制到剪贴板
        self.window.clipboard_clear()
        self.window.clipboard_append(basic_info)
        
        # 显示提示
        messagebox.showinfo("成功", "内容已复制到剪贴板！")