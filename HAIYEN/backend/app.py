from flask import Flask, jsonify, send_from_directory, request, Response
from flask_cors import CORS
import os
import json
import glob
import cv2
import time
from datetime import datetime

app = Flask(__name__)
CORS(app)

# =========================
# BASE DIR - FIX PATH
# =========================
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Các thư mục evidence - SỬA ĐƯỜNG DẪN CHO ĐÚNG
EVIDENCE_IMAGE_DIR = os.path.join(BASE_DIR, "evidence", "images")
EVIDENCE_VIDEO_DIR = os.path.join(BASE_DIR, "evidence", "videos")  # ĐÂY RỒI!
EVIDENCE_LOG_DIR = os.path.join(BASE_DIR, "evidence", "logs", "log1")

# Nếu không tìm thấy, thử các đường dẫn khác
if not os.path.exists(EVIDENCE_VIDEO_DIR):
    # Thử tìm trong các vị trí khác có thể
    possible_video_dirs = [
        os.path.join(BASE_DIR, "evidence", "videos"),
        os.path.join(BASE_DIR, "evidence", "video"),
        os.path.join(BASE_DIR, "videos"),
        os.path.join(BASE_DIR, "video"),
        os.path.join(BASE_DIR, "docs", "evidence", "videos"),
        os.path.join(BASE_DIR, "docs", "evidence", "video"),
    ]
    
    for video_dir in possible_video_dirs:
        if os.path.exists(video_dir):
            EVIDENCE_VIDEO_DIR = video_dir
            print(f"Found videos in: {EVIDENCE_VIDEO_DIR}")
            break

# Tạo thư mục nếu chưa tồn tại
os.makedirs(EVIDENCE_IMAGE_DIR, exist_ok=True)
os.makedirs(EVIDENCE_VIDEO_DIR, exist_ok=True)
os.makedirs(EVIDENCE_LOG_DIR, exist_ok=True)

print("=" * 60)
print("SYSTEM PATHS CONFIGURED:")
print(f"📁 BASE_DIR: {BASE_DIR}")
print(f"🖼️  IMAGE_DIR: {EVIDENCE_IMAGE_DIR}")
print(f"🎥 VIDEO_DIR: {EVIDENCE_VIDEO_DIR}")
print(f"📝 LOG_DIR: {EVIDENCE_LOG_DIR}")
print("=" * 60)

# =========================
# ROUTES FOR DASHBOARD
# =========================
@app.route("/")
def dashboard_home():
    return send_from_directory("../dashboard", 'index.html')

@app.route("/video")
def video_monitoring():
    return send_from_directory("../dashboard", 'video.html')

@app.route("/test")
def test_page():
    return send_from_directory("../dashboard", 'test.html')

@app.route("/<path:filename>")
def dashboard_files(filename):
    return send_from_directory("../dashboard", filename)

# =========================
# API: SCAN AND GET ALL VIDEOS
# =========================
@app.route("/api/videos", methods=["GET"])
def get_videos():
    """Lấy danh sách tất cả video trong thư mục videos"""
    print(f"🔍 Scanning video directory: {EVIDENCE_VIDEO_DIR}")
    
    if not os.path.exists(EVIDENCE_VIDEO_DIR):
        print(f"❌ Video directory does not exist: {EVIDENCE_VIDEO_DIR}")
        # Tạo thư mục nếu không tồn tại
        os.makedirs(EVIDENCE_VIDEO_DIR, exist_ok=True)
        print(f"✅ Created video directory: {EVIDENCE_VIDEO_DIR}")
        return jsonify([])
    
    videos = []
    video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv', '.m4v')
    
    try:
        files = os.listdir(EVIDENCE_VIDEO_DIR)
        print(f"📂 Found {len(files)} files in video directory")
        
        for file in sorted(files):
            file_lower = file.lower()
            if file_lower.endswith(video_extensions):
                file_path = os.path.join(EVIDENCE_VIDEO_DIR, file)
                
                try:
                    stat = os.stat(file_path)
                    
                    # Lấy thông tin cơ bản
                    video_info = {
                        "name": file,
                        "size": stat.st_size,
                        "size_formatted": format_size(stat.st_size),
                        "created": stat.st_ctime,
                        "created_formatted": datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                        "modified": stat.st_mtime,
                        "path": f"/evidence/videos/{file}",
                        "url": f"http://localhost:5000/evidence/videos/{file}",
                        "type": "video"
                    }
                    
                    # Thử lấy duration từ video
                    try:
                        cap = cv2.VideoCapture(file_path)
                        if cap.isOpened():
                            fps = cap.get(cv2.CAP_PROP_FPS)
                            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                            
                            if fps > 0:
                                duration = frame_count / fps
                                video_info["duration"] = duration
                                video_info["duration_formatted"] = format_duration(duration)
                                video_info["fps"] = fps
                                video_info["frames"] = frame_count
                            
                            # Lấy thumbnail (frame đầu tiên)
                            ret, frame = cap.read()
                            if ret:
                                # Lưu thumbnail
                                thumb_dir = os.path.join(EVIDENCE_IMAGE_DIR, "thumbnails")
                                os.makedirs(thumb_dir, exist_ok=True)
                                thumb_path = os.path.join(thumb_dir, f"{os.path.splitext(file)[0]}.jpg")
                                
                                if not os.path.exists(thumb_path):
                                    cv2.imwrite(thumb_path, frame)
                                    print(f"✅ Created thumbnail: {thumb_path}")
                                
                                video_info["thumbnail"] = f"/evidence/images/thumbnails/{os.path.splitext(file)[0]}.jpg"
                            
                            cap.release()
                    except Exception as e:
                        print(f"⚠️  Could not extract video info for {file}: {e}")
                        video_info["duration"] = 0
                        video_info["duration_formatted"] = "00:00"
                    
                    # Đếm số vi phạm trong video này
                    video_base = os.path.splitext(file)[0]
                    violation_count = count_violations_for_video(video_base)
                    video_info["violation_count"] = violation_count
                    
                    videos.append(video_info)
                    print(f"✅ Added video: {file} ({format_size(stat.st_size)}) - {violation_count} violations")
                    
                except Exception as e:
                    print(f"❌ Error processing video {file}: {e}")
    
    except Exception as e:
        print(f"❌ Error listing video directory: {e}")
    
    print(f"🎬 Total videos found: {len(videos)}")
    return jsonify(videos)

# =========================
# API: GET ALL VIOLATIONS
# =========================
@app.route("/api/violations", methods=["GET"])
def get_violations():
    """Lấy tất cả vi phạm từ log files"""
    results = []
    
    if not os.path.exists(EVIDENCE_LOG_DIR):
        print(f"📝 Log directory not found: {EVIDENCE_LOG_DIR}")
        # Thử tìm trong các vị trí khác
        possible_log_dirs = [
            os.path.join(BASE_DIR, "evidence", "logs", "log1"),
            os.path.join(BASE_DIR, "evidence", "logs"),
            os.path.join(BASE_DIR, "logs"),
            os.path.join(BASE_DIR, "docs", "evidence", "logs", "log1"),
        ]
        
        for log_dir in possible_log_dirs:
            if os.path.exists(log_dir):
                EVIDENCE_LOG_DIR = log_dir
                print(f"📝 Found logs in: {EVIDENCE_LOG_DIR}")
                break
        else:
            return jsonify([])
    
    print(f"🔍 Scanning log directory: {EVIDENCE_LOG_DIR}")
    
    try:
        log_files = os.listdir(EVIDENCE_LOG_DIR)
        print(f"📄 Found {len(log_files)} log files")
        
        for file in sorted(log_files):
            if file.endswith(".json"):
                file_path = os.path.join(EVIDENCE_LOG_DIR, file)
                print(f"📖 Processing log file: {file}")
                
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        
                        if isinstance(data, list):
                            for i, violation in enumerate(data):
                                # Đảm bảo có các trường bắt buộc
                                violation_id = f"{file}_{i}_{int(time.time())}"
                                violation["id"] = violation_id
                                violation["log_file"] = file
                                
                                # Thêm URL cho ảnh
                                if "image" in violation and violation["image"]:
                                    violation["image_url"] = f"/evidence/images/{violation['image']}"
                                
                                # Thêm URL cho video
                                video_name = file.replace('.json', '.mp4')
                                violation["video"] = video_name
                                violation["video_url"] = f"/evidence/videos/{video_name}"
                                
                                # Format thời gian
                                if "time" in violation:
                                    try:
                                        # Cố gắng parse thời gian
                                        if isinstance(violation["time"], (int, float)):
                                            violation["time_formatted"] = datetime.fromtimestamp(violation["time"]).strftime('%Y-%m-%d %H:%M:%S')
                                        else:
                                            violation["time_formatted"] = violation["time"]
                                    except:
                                        violation["time_formatted"] = violation.get("time", "N/A")
                                
                                # Thêm timestamp nếu chưa có
                                if "timestamp" not in violation:
                                    violation["timestamp"] = time.time()
                            
                            results.extend(data)
                            print(f"✅ Added {len(data)} violations from {file}")
                        
                except Exception as e:
                    print(f"❌ Error reading {file}: {e}")
                    import traceback
                    traceback.print_exc()
    
    except Exception as e:
        print(f"❌ Error accessing log directory: {e}")
    
    print(f"🚨 Total violations found: {len(results)}")
    return jsonify(results)

# =========================
# API: GET VIOLATIONS BY VIDEO
# =========================
@app.route("/api/video/<video_name>/violations", methods=["GET"])
def get_video_violations(video_name):
    """Lấy vi phạm theo video"""
    video_base = os.path.splitext(video_name)[0]
    violations = []
    
    if not os.path.exists(EVIDENCE_LOG_DIR):
        return jsonify([])
    
    print(f"🔍 Looking for violations in video: {video_name}")
    
    try:
        for file in os.listdir(EVIDENCE_LOG_DIR):
            if file.endswith(".json"):
                # Kiểm tra xem log file có match với video không
                log_base = os.path.splitext(file)[0]
                
                # So sánh tên file (có thể có prefix/suffix khác)
                if video_base in log_base or log_base in video_base or file.replace('.json', '') == video_base:
                    file_path = os.path.join(EVIDENCE_LOG_DIR, file)
                    
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                for violation in data:
                                    violation['log_file'] = file
                                    violation['video'] = video_name
                                    violations.append(violation)
                        
                        print(f"✅ Found {len(data)} violations in log: {file}")
                        
                    except Exception as e:
                        print(f"❌ Error reading log {file}: {e}")
    
    except Exception as e:
        print(f"❌ Error scanning logs: {e}")
    
    print(f"🎯 Found {len(violations)} violations for video {video_name}")
    return jsonify(violations)

# =========================
# SERVE MEDIA FILES
# =========================
@app.route("/evidence/images/<path:filename>")
def serve_evidence_image(filename):
    """Phục vụ file ảnh"""
    return send_from_directory(EVIDENCE_IMAGE_DIR, filename)

@app.route("/evidence/videos/<path:filename>")
def serve_evidence_video(filename):
    """Phục vụ file video"""
    print(f"🎬 Serving video: {filename}")
    
    # Kiểm tra nhiều vị trí có thể
    possible_paths = [
        os.path.join(EVIDENCE_VIDEO_DIR, filename),
        os.path.join(BASE_DIR, "evidence", "videos", filename),
        os.path.join(BASE_DIR, "videos", filename),
    ]
    
    for video_path in possible_paths:
        if os.path.exists(video_path):
            print(f"✅ Video found at: {video_path}")
            return send_from_directory(os.path.dirname(video_path), os.path.basename(video_path))
    
    print(f"❌ Video not found: {filename}")
    return jsonify({"error": "Video file not found", "filename": filename}), 404

# =========================
# API: GET SYSTEM INFO
# =========================
@app.route("/api/system/info", methods=["GET"])
def get_system_info():
    """Thông tin hệ thống"""
    return jsonify({
        "base_dir": BASE_DIR,
        "image_dir": EVIDENCE_IMAGE_DIR,
        "video_dir": EVIDENCE_VIDEO_DIR,
        "log_dir": EVIDENCE_LOG_DIR,
        "image_count": count_files(EVIDENCE_IMAGE_DIR, ('.jpg', '.jpeg', '.png', '.bmp')),
        "video_count": count_files(EVIDENCE_VIDEO_DIR, ('.mp4', '.avi', '.mov', '.mkv')),
        "log_count": count_files(EVIDENCE_LOG_DIR, ('.json',)),
        "timestamp": datetime.now().isoformat(),
        "api_endpoints": {
            "videos": "http://localhost:5000/api/videos",
            "violations": "http://localhost:5000/api/violations",
            "health": "http://localhost:5000/api/health",
            "system_info": "http://localhost:5000/api/system/info"
        }
    })

# =========================
# HEALTH CHECK
# =========================
@app.route("/api/health", methods=["GET"])
def health():
    """Kiểm tra trạng thái hệ thống"""
    return jsonify({
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "service": "Traffic Violation API",
        "version": "1.0.0",
        "directories": {
            "images": {
                "path": EVIDENCE_IMAGE_DIR,
                "exists": os.path.exists(EVIDENCE_IMAGE_DIR),
                "count": count_files(EVIDENCE_IMAGE_DIR, ('.jpg', '.jpeg', '.png', '.bmp'))
            },
            "videos": {
                "path": EVIDENCE_VIDEO_DIR,
                "exists": os.path.exists(EVIDENCE_VIDEO_DIR),
                "count": count_files(EVIDENCE_VIDEO_DIR, ('.mp4', '.avi', '.mov', '.mkv'))
            },
            "logs": {
                "path": EVIDENCE_LOG_DIR,
                "exists": os.path.exists(EVIDENCE_LOG_DIR),
                "count": count_files(EVIDENCE_LOG_DIR, ('.json',))
            }
        }
    })

# =========================
# API: GET DIRECTORY LISTING
# =========================
@app.route("/api/directory/<path:subpath>", methods=["GET"])
def list_directory(subpath=""):
    """Liệt kê thư mục (debug)"""
    target_dir = os.path.join(BASE_DIR, subpath)
    
    if not os.path.exists(target_dir):
        return jsonify({"error": "Directory not found", "path": target_dir}), 404
    
    items = []
    for item in os.listdir(target_dir):
        item_path = os.path.join(target_dir, item)
        items.append({
            "name": item,
            "type": "directory" if os.path.isdir(item_path) else "file",
            "size": os.path.getsize(item_path) if os.path.isfile(item_path) else 0,
            "path": item_path
        })
    
    return jsonify({
        "path": target_dir,
        "items": items,
        "count": len(items)
    })

# =========================
# UTILITY FUNCTIONS
# =========================
def count_violations_for_video(video_base):
    """Đếm số vi phạm cho video cụ thể"""
    count = 0
    if not os.path.exists(EVIDENCE_LOG_DIR):
        return 0
    
    for file in os.listdir(EVIDENCE_LOG_DIR):
        if file.endswith(".json"):
            log_base = os.path.splitext(file)[0]
            # Kiểm tra tương quan giữa video và log
            if video_base in log_base or log_base in video_base or file.replace('.json', '') == video_base:
                file_path = os.path.join(EVIDENCE_LOG_DIR, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            count += len(data)
                except:
                    pass
    return count

def count_files(directory, extensions):
    """Đếm file với extension cụ thể"""
    if not os.path.exists(directory):
        return 0
    
    count = 0
    for file in os.listdir(directory):
        if file.lower().endswith(extensions):
            count += 1
    return count

def format_size(size_in_bytes):
    """Định dạng kích thước file"""
    if size_in_bytes == 0:
        return "0 Bytes"
    
    units = ['Bytes', 'KB', 'MB', 'GB', 'TB']
    i = 0
    while size_in_bytes >= 1024 and i < len(units) - 1:
        size_in_bytes /= 1024
        i += 1
    
    return f"{size_in_bytes:.2f} {units[i]}"

def format_duration(seconds):
    """Định dạng thời lượng video"""
    if seconds == 0:
        return "00:00"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"

# =========================
# DEBUG ENDPOINT
# =========================
@app.route("/api/debug/paths", methods=["GET"])
def debug_paths():
    """Debug endpoint - hiển thị tất cả đường dẫn"""
    return jsonify({
        "base_dir": BASE_DIR,
        "evidence_video_dir": EVIDENCE_VIDEO_DIR,
        "evidence_image_dir": EVIDENCE_IMAGE_DIR,
        "evidence_log_dir": EVIDENCE_LOG_DIR,
        "video_dir_exists": os.path.exists(EVIDENCE_VIDEO_DIR),
        "video_dir_contents": os.listdir(EVIDENCE_VIDEO_DIR) if os.path.exists(EVIDENCE_VIDEO_DIR) else [],
        "image_dir_exists": os.path.exists(EVIDENCE_IMAGE_DIR),
        "log_dir_exists": os.path.exists(EVIDENCE_LOG_DIR),
        "current_working_dir": os.getcwd(),
        "script_dir": os.path.dirname(os.path.abspath(__file__))
    })

# =========================
# MAIN
# =========================
if __name__ == "__main__":
    print("=" * 70)
    print("🚦 TRAFFIC VIOLATION MONITORING SYSTEM - API SERVER")
    print("=" * 70)
    print(f"📁 Base Directory: {BASE_DIR}")
    print(f"🖼️  Images Directory: {EVIDENCE_IMAGE_DIR}")
    print(f"🎥 Videos Directory: {EVIDENCE_VIDEO_DIR}")
    print(f"📝 Logs Directory: {EVIDENCE_LOG_DIR}")
    print("-" * 70)
    print(f"🌐 Dashboard URL: http://localhost:5000")
    print(f"🎬 Video Monitoring: http://localhost:5000/video")
    print(f"🔧 API Base: http://localhost:5000/api")
    print(f"🐞 Debug Paths: http://localhost:5000/api/debug/paths")
    print("=" * 70)
    
    # Kiểm tra thư mục video
    if os.path.exists(EVIDENCE_VIDEO_DIR):
        videos = [f for f in os.listdir(EVIDENCE_VIDEO_DIR) if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))]
        print(f"\n🎥 Found {len(videos)} videos in {EVIDENCE_VIDEO_DIR}:")
        for video in videos[:10]:  # Hiển thị 10 video đầu tiên
            print(f"  • {video}")
        if len(videos) > 10:
            print(f"  ... and {len(videos) - 10} more")
    else:
        print(f"\n❌ Video directory not found: {EVIDENCE_VIDEO_DIR}")
        print("💡 Please create the directory and add video files")
    
    print("\n🚀 Starting server...")
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)