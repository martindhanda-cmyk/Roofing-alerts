import requests
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# CONFIGURATION: Add your paying clients and the states they want to monitor.
CLIENTS_DATABASE = [
    {
        "contractor_name": "Apex Roofing LLC",
        "phone": "+15550192834",
        "target_state": "TX", 
        "monitored_keywords": ["Severe Thunderstorm Warning", "Tornado Warning"]
    }
]

HEADERS = {"User-Agent": "(RoofingAlertSystem, admin@yourdomain.com)"}

def check_active_alerts():
    processed_alerts = set()
    while True:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Polling National Weather Service...")
        for client in CLIENTS_DATABASE:
            state = client["target_state"]
            url = f"https://api.weather.gov/alerts/active?area={state}"
            try:
                response = requests.get(url, headers=HEADERS)
                if response.status_code == 200:
                    features = response.json().get("features", [])
                    for feature in features:
                        properties = feature.get("properties", {})
                        alert_id = properties.get("id")
                        event_type = properties.get("event")
                        
                        if event_type in client["monitored_keywords"] and alert_id not in processed_alerts:
                            alert_payload = (
                                f"🚨 HAIL ALERT FOR {client['contractor_name'].upper()} 🚨\n"
                                f"EVENT: {event_type}\n"
                                f"LOCATION: {properties.get('areaDesc')}\n"
                                f"DETAILS: {properties.get('headline')}"
                            )
                            print(f"\n[TEXT SENT TO {client['phone']}]:\n{alert_payload}\n")
                            processed_alerts.add(alert_id)
            except Exception as e:
                print(f"Error checking {state}: {str(e)}")
        time.sleep(300) # Check every 5 minutes

# This tiny block keeps the server alive on Render's Free Tier
class HealthCheckServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Engine is online.")

if __name__ == "__main__":
    # Start the weather monitor in the background
    monitor_thread = threading.Thread(target=check_active_alerts, daemon=True)
    monitor_thread.start()
    
    # Start a basic web server on port 10000 (Render's default) so the free tier stays alive
    server = HTTPServer(('0.0.0.0', 10000), HealthCheckServer)
    print("Web server listening on port 10000...")
    server.serve_forever()
