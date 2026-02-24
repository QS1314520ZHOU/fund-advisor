
import sys
import os

try:
    with open('d:/fund-advisor/update_log.txt', 'r', encoding='utf-8') as f:
        print(f.read())
except Exception as e:
    # Try different encoding
    try:
        with open('d:/fund-advisor/update_log.txt', 'r', encoding='gbk') as f:
            print(f.read())
    except Exception as e2:
        print(f"Error reading log: {e}, {e2}")
