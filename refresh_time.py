import os
import datetime
import win32file
import pywintypes
import pytz
import time  # 添加时间模块用于重试

class FileHandleContextManager:
    def __init__(self, path):
        self.path = path
        self.handle = None

    def __enter__(self):
        # 添加 FILE_FLAG_BACKUP_SEMANTICS 标志以支持目录操作
        flags = win32file.FILE_ATTRIBUTE_NORMAL | win32file.FILE_FLAG_BACKUP_SEMANTICS
        try:
            self.handle = win32file.CreateFile(
                self.path,
                win32file.GENERIC_WRITE,
                0,
                None,
                win32file.OPEN_EXISTING,
                flags,
                None
            )
            return self.handle
        except pywintypes.error as e:
            if e.winerror == 32:  # ERROR_SHARING_VIOLATION
                print(f"文件被占用: {self.path}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.handle:
            self.handle.close()

def modifyFileTime(file_path, new_creation_time, new_access_time, new_modification_time):
    """修改单个文件/目录的时间属性（带重试机制）"""
    retries = 3
    delay = 1  # 重试间隔（秒）
    
    for attempt in range(retries):
        try:
            with FileHandleContextManager(file_path) as handle:
                # 将Python的datetime对象转换为pywintypes的时间对象
                times = map(pywintypes.Time, [new_creation_time, new_access_time, new_modification_time])
                new_creation_time, new_access_time, new_modification_time = times
                # 设置文件/目录时间
                win32file.SetFileTime(handle, new_creation_time, new_access_time, new_modification_time)
            return True
        except Exception as e:
            if attempt < retries - 1:
                print(f"重试 {attempt+1}/{retries} - {file_path}")
                time.sleep(delay)  # 等待后重试
            else:
                print(f"更新 {file_path} 时间时发生错误: {e}")
                return False
    return False

def get_file_times(path):
    """获取文件/目录的时间属性（创建时间、访问时间、修改时间）"""
    try:
        with FileHandleContextManager(path) as handle:
            create_time, access_time, modify_time = win32file.GetFileTime(handle)
            # 转换为datetime对象并添加UTC时区信息
            create_dt = pywintypes.Time(create_time).replace(tzinfo=pytz.UTC)
            access_dt = pywintypes.Time(access_time).replace(tzinfo=pytz.UTC)
            modify_dt = pywintypes.Time(modify_time).replace(tzinfo=pytz.UTC)
            return create_dt, access_dt, modify_dt
    except Exception as e:
        print(f"读取 {path} 时间时发生错误: {e}")
        return None, None, None

def find_earliest_time(path):
    """递归查找文件夹及其所有子项中的最早时间"""
    earliest_time = None
    
    if os.path.isfile(path):
        # 单个文件
        create_time, access_time, modify_time = get_file_times(path)
        if create_time and access_time and modify_time:
            file_min = min(create_time, access_time, modify_time)
            if earliest_time is None or file_min < earliest_time:
                earliest_time = file_min
        return earliest_time
    
    # 遍历目录
    for root, dirs, files in os.walk(path):
        # 处理当前目录
        create_time, access_time, modify_time = get_file_times(root)
        if create_time and access_time and modify_time:
            dir_min = min(create_time, access_time, modify_time)
            if earliest_time is None or dir_min < earliest_time:
                earliest_time = dir_min
        
        # 处理文件
        for file in files:
            file_path = os.path.join(root, file)
            create_time, access_time, modify_time = get_file_times(file_path)
            if create_time and access_time and modify_time:
                file_min = min(create_time, access_time, modify_time)
                if earliest_time is None or file_min < earliest_time:
                    earliest_time = file_min
    
    return earliest_time

def adjust_directory_times(path, custom=None):
    """
    调整文件夹及其所有子项的时间，保持时间差结构
    
    参数:
    path (str): 目标路径
    custom (datetime): 目标基准时间（如果不提供则使用当前时间）
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"路径不存在: {path}")
    
    # 1. 找到最早的时间
    earliest_time = find_earliest_time(path)
    if earliest_time is None:
        raise RuntimeError(f"无法获取 {path} 的时间信息")
    
    # 2. 确定目标基准时间
    # 确保所有时间都是时区感知的
    if custom:
        # 如果提供了自定义时间，确保它是时区感知的
        if custom.tzinfo is None or custom.tzinfo.utcoffset(custom) is None:
            # 添加系统本地时区
            local_tz = datetime.datetime.now().astimezone().tzinfo
            custom = custom.replace(tzinfo=local_tz)
    else:
        # 使用当前时间（带时区）
        custom = datetime.datetime.now().astimezone()
    
    # 确保最早时间也是时区感知的（使用UTC时区）
    if earliest_time.tzinfo is None:
        earliest_time = earliest_time.replace(tzinfo=pytz.UTC)
    
    # 3. 计算时间差
    time_diff = custom - earliest_time
    
    # 4. 验证调整后的时间不会超过当前时间
    current_time = datetime.datetime.now().astimezone()
    max_allowed_diff = current_time - earliest_time
    
    if time_diff > max_allowed_diff:
        raise ValueError(
            f"调整时间差 {time_diff} 超过了允许的最大值 {max_allowed_diff}\n"
            f"最大允许调整时间为: {earliest_time + max_allowed_diff}"
        )
    
    print(f"最早时间: {earliest_time}")
    print(f"目标时间: {custom}")
    print(f"时间差: {time_diff}")
    
    # 5. 递归修改时间
    def adjust_item(item_path):
        """调整单个项目的时间"""
        create_time, access_time, modify_time = get_file_times(item_path)
        if create_time and access_time and modify_time:
            # 确保所有时间都是时区感知的
            if create_time.tzinfo is None:
                create_time = create_time.replace(tzinfo=pytz.UTC)
            if access_time.tzinfo is None:
                access_time = access_time.replace(tzinfo=pytz.UTC)
            if modify_time.tzinfo is None:
                modify_time = modify_time.replace(tzinfo=pytz.UTC)
            
            new_create = create_time + time_diff
            new_access = access_time + time_diff
            new_modify = modify_time + time_diff
            
            # 确保不超过当前时间
            new_create = min(new_create, current_time)
            new_access = min(new_access, current_time)
            new_modify = min(new_modify, current_time)
            
            return modifyFileTime(item_path, new_create, new_access, new_modify)
        return False
    
    total_count = 0
    success_count = 0
    
    if os.path.isfile(path):
        # 单个文件
        total_count = 1
        if adjust_item(path):
            success_count = 1
    else:
        # 遍历目录
        for root, dirs, files in os.walk(path, topdown=False):
            # 先处理文件
            for file in files:
                file_path = os.path.join(root, file)
                total_count += 1
                try:
                    if adjust_item(file_path):
                        success_count += 1
                except Exception as e:
                    print(f"处理文件 {file_path} 时出错: {e}")
            
            # 处理目录（包括当前目录）
            dirs_to_adjust = [root] + [os.path.join(root, d) for d in dirs]
            for dir_path in dirs_to_adjust:
                total_count += 1
                try:
                    if adjust_item(dir_path):
                        success_count += 1
                except Exception as e:
                    print(f"处理目录 {dir_path} 时出错: {e}")
    
    if total_count > 0:
        print(f"已完成时间调整: {success_count}/{total_count} 个项目成功")
    else:
        print("没有找到可调整的项目")
    
    return success_count, total_count

def set_directory_times_uniformly(path, custom_time):
    """
    将文件夹及其所有子项的时间统一设置为指定时间（带根目录重试机制）
    
    参数:
    path (str): 目标路径
    custom_time (datetime): 目标时间
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"路径不存在: {path}")
    
    total_count = 0
    success_count = 0
    failed_items = []
    
    def set_item_time(item_path):
        """设置单个项目的时间"""
        nonlocal total_count, success_count, failed_items
        total_count += 1
        try:
            if modifyFileTime(item_path, custom_time, custom_time, custom_time):
                success_count += 1
                return True
            else:
                failed_items.append(item_path)
                return False
        except Exception as e:
            print(f"设置 {item_path} 时间时出错: {str(e)}")
            failed_items.append(item_path)
            return False
    
    # 首先处理所有子项
    if os.path.isdir(path):
        # 遍历目录（先处理子项）
        for root, dirs, files in os.walk(path):
            # 处理文件
            for file in files:
                file_path = os.path.join(root, file)
                set_item_time(file_path)
            
            # 处理子目录（不包括根目录）
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                set_item_time(dir_path)
    
    # 最后处理根目录（尝试多次）
    root_retries = 3
    for attempt in range(root_retries):
        if set_item_time(path):
            break
        elif attempt < root_retries - 1:
            print(f"重试根目录 {attempt+1}/{root_retries}")
            time.sleep(1)
    
    return success_count, total_count