import threading
import time
import requests
import statistics

TARGET_URL = "https://erp.elmrkz.cloud/api/method/maintenance_management.api.get_maintenance_kpis"
NUM_THREADS = 20
REQUESTS_PER_THREAD = 10

latencies = []
success_count = 0
error_count = 0
lock = threading.Lock()

def make_request():
    global success_count, error_count
    start_time = time.time()
    try:
        resp = requests.get(TARGET_URL, timeout=10)
        duration = (time.time() - start_time) * 1000 # ms
        with lock:
            if resp.status_code == 200:
                success_count += 1
                latencies.append(duration)
            else:
                error_count += 1
    except Exception as e:
        with lock:
            error_count += 1

def worker():
    for _ in range(REQUESTS_PER_THREAD):
        make_request()
        time.sleep(0.05)

def run_stress_test():
    print(f"=== STARTING STRESS TEST: {NUM_THREADS} threads, {REQUESTS_PER_THREAD} reqs/thread ===")
    start_all = time.time()
    
    threads = []
    for _ in range(NUM_THREADS):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    total_time = time.time() - start_all
    total_requests = success_count + error_count
    
    print(f"=== STRESS TEST COMPLETED IN {round(total_time, 2)}s ===")
    print(f"Total Requests: {total_requests}")
    print(f"Success Count: {success_count}")
    print(f"Error Count: {error_count}")
    if latencies:
        print(f"Avg Latency: {round(statistics.mean(latencies), 2)} ms")
        print(f"Median Latency: {round(statistics.median(latencies), 2)} ms")
        print(f"Max Latency: {round(max(latencies), 2)} ms")
        print(f"Min Latency: {round(min(latencies), 2)} ms")
    print(f"Requests/sec: {round(total_requests / total_time, 2)}")

if __name__ == "__main__":
    run_stress_test()
