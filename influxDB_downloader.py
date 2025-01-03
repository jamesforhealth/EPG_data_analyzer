import requests
import json
import os 
from datetime import datetime
import re
def sanitize_filename(filename):
    # 使用正則表達式替換無效字元
    sanitized_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
    return sanitized_name

def format_timestamp(timestamp):
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H-%M-%S')
# base_url = "https://mrqhn4tot3.execute-api.ap-northeast-1.amazonaws.com/api/database/v1/"
base_url = "http://192.168.1.109:8000/v1"

# 獲取所有用戶列表
def get_all_users():
    url = f"{base_url}/list-users"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error getting user list: {response.status_code}")
        return None

# 獲取指定用戶的所有session資訊
def get_user_sessions(user_id):
    url = f"{base_url}/sessions/{user_id}?recent_first=true"
    headers = {"Accept": "application/json"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error getting user sessions: {response.status_code}")
        return None

# 獲取指定session的原始資料
def get_session_data(user_id, timestamp, macaddress):
    url = f"{base_url}/session-data/{user_id}/{timestamp}/{macaddress}?data_format=with_timestamp&delivery_type=full-on-demand&delivery_method=cached"
    headers = {"Accept": "application/json"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data_url = response.json()["url"]
        data_response = requests.get(data_url)
        if data_response.status_code == 200:
            return data_response.json()
        else:
            print(f"Error getting session data: {data_response.status_code}")
            return None
    else:
        print(f"Error getting session data URL: {response.status_code}")
        return None

# 主程式
def main():
    base_dir = "DB"  # 資料夾名稱
    users = get_all_users()
    if users is not None:
        os.makedirs(base_dir, exist_ok=True)  # 建立資料夾

        all_data = []
        # for user in users:
        #     user_id = user["idusers"]
        user_id = 202
        user_dir = os.path.join(base_dir, str(user_id))
        os.makedirs(user_dir, exist_ok=True)  # 為每個用戶建立資料夾
        sessions = get_user_sessions(user_id)
        if sessions is not None:
            for idx, timestamp in enumerate(sessions["timestamp"]):
                
                macaddress = sessions["session_data"]["BLE_MAC_ADDRESS"][idx]
                session_data = get_session_data(user_id, timestamp, macaddress)
                if session_data is not None:
                    note = sessions["session_data"]["session_notes"][idx]
                    
                    note_lower = sessions["session_data"]["session_notes"][idx].lower()
                    keywords = ["ICP", "TCCP", "TICP"]
                    if 'ekg' in note_lower:
                        data_type = 'EKG'
                    else:
                        data_type = 'TICP' if any(keyword.lower() in note_lower for keyword in keywords) else 'EPG'
                    
                    session_info = {
                        "user_id": user_id,
                        "timestamp": timestamp,
                        "macaddress": macaddress,
                        "sample_rate": sessions["session_data"]["sample_rate"][idx],
                        "session_note": note,
                        "raw_data": session_data["data"]["data"],
                        "dataType" : data_type
                    }
                    all_data.append(session_info)
                    file_name = f"({format_timestamp(timestamp)}),({sanitize_filename(note)}).json"
                    file_path = os.path.join(user_dir, file_name)
                    with open(file_path, "w") as file:
                        json.dump(session_info, file)
                    print(f"Data saved to {file_path}")

    else:
        print("Failed to retrieve data")

if __name__ == "__main__":
    main()