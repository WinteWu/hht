#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import urllib.request # Changed from urllib
# urllib2 is removed in Python 3
import re
import os
# import thread # Changed to threading
import threading
import math
import sys
import time
import requests # Keep requests as it's already used

# Assuming pymysql is installed and Python 3 compatible
# import pymysql.cursors
# import pymysql

class DlHhtRes():
    '''
    Version 1.x
    下载火火免APP 所有 该分类下的 mp3文件并按 类型分类存放
    使用 json 离线下载
    '''

    # 下载线程数
    _onDlNum = 50

    # 已下载文件数
    _fileNum = 0

    # String literals are Unicode by default in Python 3
    _taskName = {
        '1': '下载并保存文件',
        '2': '重新更新数据源'
    }

    # 下载归类使用的文件夹名称
    _categoryName = {
        '1': '儿歌',
        '2': '故事',
        '3': '英语',
        '4': '古诗',
        '5': '伴眠'
    }

    # 当前正在操作的分类所有内容页的链接地址
    _doCategoryIds = [] # This variable doesn't seem to be used

    # 当前正在操作的内容页的所有下载地址 对应文件名称
    _res = []

    # 获取下载链接
    def getDlUrl(self, spName):
        # requests import is already in class scope, but importing here is also fine
        # import requests # Redundant if imported at top
        try:
            # Changed data to a dictionary for requests
            r = requests.post("http://www.alilo.com.cn/gw/resource/music", data={'specialname': spName})
            r.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            
            # print r.text # Debugging print
            
            listJson = r.json() # requests can parse JSON directly

            # Changed has_key to 'in'
            if 'content' in listJson:
                musicList = listJson['content']['musicList']
                # Changed print statement to print function and used f-string
                print(f"{len(musicList)} 's musics in category {spName}")

                if len(musicList) > 0:
                    # 所有下载链接
                    for music in musicList:
                        self._res.append({
                            'res': music['path'],
                            'name': music['name']
                        })
        except requests.exceptions.RequestException as e:
            print(f"Error fetching music list for {spName}: {e}")
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON for {spName}: {e}")
        except KeyError as e:
            print(f"Missing key in JSON response for {spName}: {e}")

    # 获取分类链接
    def getCategoryName(self, catName):
        # requests import is already in class scope, but importing here is also fine
        # import requests # Redundant if imported at top
        try:
            # Changed data to a dictionary for requests
            r = requests.post("http://www.alilo.com.cn/gw/resource/special", data={'classname': catName, 'classid': 0})
            r.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            
            # print r.text # Debugging print
            
            listJson = r.json() # requests can parse JSON directly

            # Changed has_key to 'in'
            if 'content' in listJson:
                specialList = listJson['content']['specialList']
                # 没有数据
                if len(specialList) > 0:
                    # 所有分类写入下载链接
                    for cate in specialList:
                        # Recursive call to getDlUrl for each special category
                        if 'name' in cate:
                            self.getDlUrl(cate['name'])
                        else:
                            print(f"Warning: Missing 'name' key in category data: {cate}")
                else:
                    print(f"No special lists found for category: {catName}")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching special list for {catName}: {e}")
        except json.JSONDecodeError as e:
             print(f"Error decoding JSON for {catName}: {e}")
        except KeyError as e:
            print(f"Missing key in JSON response for {catName}: {e}")

    # 开始执行所有下载操作
    # Added default values for ac and category to make the signature more explicit
    def __init__(self, ac = '1', category=''):
        # The original code had this check inside __init__.
        # It's better to handle user input and calling the class instance outside the class definition,
        # specifically in the `if __name__ == '__main__':` block at the bottom.
        # However, to keep the structure similar, I'll keep this check here, but it means
        # the class *only* runs its main logic when the script is executed directly.

        if __name__ == '__main__':
            # Convert category input to a list for iteration
            categories_to_process = [category] if category and category in self._categoryName else list(self._categoryName.keys()) # Iterate over keys to get '1', '2', etc.

            if category and category in self._categoryName:
                # Use f-string for printing
                print(f'Your insert category is {self._categoryName[category]}')
            elif category and category not in self._categoryName:
                 print(f"Invalid category ID: {category}. Processing all categories.")
                 category = '' # Reset category to process all

            # Firstly, process all categories or the selected one
            for cat_id in categories_to_process:
                # 下载指令
                if '1' == ac: # Download
                    try:
                        self.openJson(cat_id) # Open the json file for this category
                        if len(self._res) > 0:
                            # Get the user-friendly category name from the ID
                            category_name = self._categoryName.get(cat_id, f"Unknown_Category_{cat_id}")
                            # 下载并命名归类文件
                            self.downloadFile(category_name)
                            time.sleep(3) # Wait a bit between categories

                        # The fileNum count is across all categories if processing multiple.
                        # The "Mission complete" print might be better outside this loop.
                        # For now, keep it inside the loop as per original logic structure.
                        print(f"{self._fileNum} files download completed for category {cat_id}, Mission complete.")

                        # Operation completed, consider shutdown (Windows only)
                        # if sys.platform == 'win32':
                        #     # os.system('shutdown -s -t %d' % 1) # Disabled by default
                        #     pass

                    except FileNotFoundError:
                         print(f"Error: JSON file not found for category ID {cat_id}. Please run task type '2' first to update data source.")
                         continue # Move to the next category or finish
                    except Exception as e:
                        print(f"An error occurred during download for category {cat_id}: {e}")
                        # Optional: add more specific error handling here
                        continue

                # 保存 数据
                if '2' == ac: # Update/Save Data Source
                    category_name = self._categoryName.get(cat_id, f"Unknown_Category_{cat_id}")
                    self._res = [] # Clear _res before fetching new data
                    self.getCategoryName(category_name) # Fetch data for this category
                    if len(self._res) > 0:
                        self.saveJson(cat_id) # Save the fetched data
                        # Use f-string for printing
                        print(f"{len(self._res)} datas save completed in ./res/{cat_id}.json for category {category_name}")
                    else:
                         print(f"No data fetched for category {category_name} ({cat_id}). No JSON saved.")
                    time.sleep(3) # Wait a bit between categories

            # Final message if processing all categories
            if not category: # If no specific category was requested
                if ac == '1':
                     print(f"Total files downloaded across all categories: {self._fileNum}. Overall Mission complete.")
                elif ac == '2':
                     print("Data source update process completed for all categories.")

    # 打开数据包
    def openJson(self, catid):
        # Specify encoding for cross-platform compatibility
        with open(f'./res/{catid}.json', 'r', encoding='utf-8') as f:
            self._res = json.load(f)
        # self._res now contains the list of dictionaries

    # 存 json
    def saveJson(self, catid):
        # 创建文件夹
        if not os.path.isdir('res'): # Use 'not' instead of 'False == '
            os.mkdir('res')

        if len(self._res) > 0:
            # 写本分类所有内容至 ./res/catid.json 文件
            # Specify encoding and use indent for readability in json file
            with open(f'./res/{catid}.json', 'w', encoding='utf-8') as f:
                # json.dumps returns a string, so write it
                json.dump(self._res, f, ensure_ascii=False, indent=4) # Use json.dump directly to file, ensure_ascii=False for non-ASCII names

    # 存储所有信息 (Optional: If you use a DB)
    # This function was commented out in the original usage flow, but converted for completeness.
    def saveData(self, category):
        import pymysql.cursors
        import pymysql # Import inside the method if only used here

        # Connect to the database
        # Ensure your pymysql connection details are correct
        try:
            connection = pymysql.connect(host='localhost',
                                     user='root',
                                     password='', # *** Add your password here ***
                                     db='hht',
                                     charset='utf8mb4', # Essential for saving non-ASCII data
                                     cursorclass=pymysql.cursors.DictCursor)
        except pymysql.Error as e:
            print(f"Error connecting to DB: {e}")
            return # Exit the function if connection fails

        try:
            with connection.cursor() as cursor:
                # Read a single record
                sql = "SELECT `id`, `typename`, `py` FROM `type` WHERE `py` = %s"
                cursor.execute(sql, (category,)) # Pass category as a tuple

                typeArr = cursor.fetchone()

                if not typeArr:
                    print(f"Warning: Category '{category}' not found in the 'type' table. Skipping data save.")
                    return

            # Wwrite all content for this category
            if len(self._res) > 0:
                # Use executemany for potentially better performance
                sql = "INSERT INTO `res` (`type_id`, `name`, `link`) VALUES (%s, %s, %s)"
                data_to_insert = [(typeArr['id'], resOne['name'], resOne['res']) for resOne in self._res]
                with connection.cursor() as cursor:
                     cursor.executemany(sql, data_to_insert)

                connection.commit()
                print(f'Insert {len(self._res)} datas with category {typeArr["typename"]}')
            else:
                print(f'No data to insert for category {typeArr["typename"]}.')

        except pymysql.Error as e:
            connection.rollback() # Roll back changes on error
            print(f"Database error during save: {e}")
        finally:
            if 'connection' in locals() and connection:
                 connection.close()


    # 线程状态
    _threadsStatus = {}
    # Download the file
    def downloadFile(self, categoryName):
        # Create folder
        if not os.path.isdir(categoryName): # Use 'not' instead of 'False == '
            os.mkdir(categoryName)

        # Total files to download for this category
        dlNum = len(self._res)
        if dlNum == 0:
            print(f"No files to download in category {categoryName}.")
            return # Exit if no files

        print(f"{categoryName} will be downloaded using up to {self._onDlNum} threads for {dlNum} files.")

        # Use a list to keep track of active threads
        active_threads = []
        # Use a lock for accessing shared resources like _threadsStatus and _fileNum
        status_lock = threading.Lock()

        # Define the download worker function
        def dl_worker(threadName, res):
            # Get file extension
            def getFileExp(file):
                # Added a check for file length and position of '.'
                if '.' in file and len(file) > 3:
                     return '.' + file.split('.')[-1] # Get extension after the last dot
                return '' # No extension or invalid format

            # Download file to category directory and rename
            reg = re.compile(r'[\\/:*?"<>|\r\n]+')
            baseName = res['name'] + getFileExp(res['res'])
            # Use sub() to replace invalid characters directly
            validName = reg.sub("_", baseName) # Replace all occurrences with "_"
            fileName = os.path.join(categoryName, validName) # Use os.path.join for cross-platform paths

            # print(f"{threadName}: Processing {res['name']}") # Debugging print

            if not os.path.isfile(fileName):
                try:
                    # Use urllib.request.urlretrieve in Python 3
                    urllib.request.urlretrieve(res['res'], fileName)
                    # Atomically update shared file counter using a lock
                    with status_lock:
                         self._fileNum += 1
                    # Use f-string for printing
                    print(f"{threadName} Downloaded: {res['name']} ({res['res']})")
                except Exception as e: # Catch any download error
                    print(f"Network Error downloading {res['res']}: {e}")
            else:
                print(f"{threadName} Exists: {res['name']} ({res['res']})")

            # Remove thread from status tracker using a lock
            with status_lock:
                 if threadName in self._threadsStatus:
                     del self._threadsStatus[threadName]

            # In threading, the function simply finishes; no explicit exit needed


        # List of resources to process (make a copy if dl_worker modified _res)
        resources_to_process = list(self._res)
        processed_count = 0
        thread_counter = 0 # Counter to give unique names to threads

        # Start threads up to the limit
        # Loop through resources, starting threads when slots are available
        for dlres in resources_to_process:
             threadName = f'Thread-{thread_counter}'

             # Wait until a thread slot is free
             # Use a loop and lock to check the number of active threads
             while True:
                 with status_lock:
                      if len(self._threadsStatus) < self._onDlNum:
                           # Slot found, mark it as occupied
                           self._threadsStatus[threadName] = dlres # Store info about what this thread is doing
                           break # Exit the while loop, proceed to start thread
                 # If no slot was free, wait a moment before checking again
                 time.sleep(0.1) # Avoid busy-waiting completely, yield CPU

             # Start the new thread
             thread = threading.Thread(target=dl_worker, name=threadName, args=(threadName, dlres))
             active_threads.append(thread) # Keep track of the thread object
             thread.start() # Start the thread's execution

             thread_counter += 1
             # processed_count += 1 # This should be incremented when the thread finishes, not starts.
                                  # The original code used `allThreadNum` for this, which required locking.
                                  # Using `_fileNum` (incremented inside worker) and `dlNum` (total) is clearer.

        # Wait for all threads to complete
        # A simple way is to join all started threads.
        # Alternatively, you could wait for _fileNum to reach dlNum using the lock.
        # The original code waited on len(_threadsStatus) using a busy loop.
        # Let's stick closer to the original's concurrency management logic.
        # Wait until the number of active threads (tracked in _threadsStatus) is zero.
        print(f"All download threads for {categoryName} started. Waiting for them to finish...")
        while True:
            with status_lock:
                if len(self._threadsStatus) == 0 and self._fileNum == dlNum: # Ensure all *started* threads are done and file count matches expected total
                    break
            # If still threads running or files not counted yet, wait
            # print(f"Active threads: {len(self._threadsStatus)}, Downloaded: {self._fileNum}/{dlNum}") # Debugging
            time.sleep(1) # Check status periodically

        # Clear the resource list for the next category if any
        self._res.clear() # Use clear() method

        print(f"{categoryName}: {dlNum} files download process initiated. Check logs for actual completion.")
        # The final 'completed' message was outside the while loop in original.
        # Moving it here ensures it prints after the category batch finishes.


# --- Main Execution Block ---

# Prompts should be standard strings in Python 3
userCate = None
taskType = None

def waitUserCate():
    global userCate
    msg = '请输入分类 序号 开始下载或直接回车下载所有分类文件：' # Standard string
    # Use input() directly in Python 3, it handles console encoding
    userCate = input(msg)

def waitUserTask():
    global  taskType
    msg = '请输入任务类型序号 ：' # Standard string
    # Use input() directly
    taskType = input(msg)

# Use print() function and standard strings
print('::1:: 这里是所有可用分类 ID 以及其对应名称: ')
# Iterate over items() which returns key, value pairs
for py, cName in DlHhtRes._categoryName.items():
    print(f'{py} : {cName}') # Use f-string

# Loop for category input
while userCate not in DlHhtRes._categoryName and userCate != '':
    waitUserCate()
    # No 'pass' needed if waitUserCate handles the input

# If a valid category was entered or it's empty, proceed
print('::2:: 这里是可用的任务类型, 为防止火火兔再次更新接口导致下载器不可用, 目前这一版本已自带数据源一般用户无需 重新更新数据源 直接选择下载并保存文件即可, 如需更新数据源, 请备份 ./res/ 文件夹后 确认已安装 requests (pip install requests) 后执行 重新更新数据源 操作之后再次执行 下载并保存文件 即可')
for py, name in DlHhtRes._taskName.items(): # Iterate over items()
    print(f'{py} : {name}') # Use f-string

# Loop for task type input
while taskType not in DlHhtRes._taskName:
    waitUserTask()
    # No 'pass' needed

# Start the main process by creating an instance of the class
# The __init__ method will then execute the logic based on the inputs
DlHhtRes(taskType, userCate)
