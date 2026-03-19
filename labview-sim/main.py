import os
import datetime
import json
import requests
from flask import Flask, request, Response, redirect, jsonify
from waitress import serve
import time

from flask_cors import CORS

from setup_logging import get_logger

# for local dev, load env vars from a .env file
from dotenv import load_dotenv
load_dotenv()

service_url = os.getenv("Quix__Deployment__Network__PublicUrl")
data_api_endpoint = os.getenv("data_api_endpoint", "")
test_api_url = os.getenv("TEST_API_URL", "http://localhost:3000/api/v1/tests")
ecu_api_url = os.getenv("ECU_API_URL", "http://localhost:3001/api/ecu")
api_token = os.getenv("API_TOKEN", "")

logger = get_logger()

app = Flask(__name__)

# Enable CORS for all routes and origins by default
CORS(app)

app.static_folder = '.'
app.static_url_path = ''

# Store the current test ID
current_test_id = "TEST-001"

def increment_test_id(test_id):
    """Extract number from test ID, increment it, and return new ID"""
    parts = test_id.split('-')
    if len(parts) == 2 and parts[1].isdigit():
        number = int(parts[1]) + 1
        return f"{parts[0]}-{number:03d}"
    return test_id

@app.route("/image_1.png")
def serve_image():
    return app.send_static_file('image_1.png')

@app.route("/video.mp4")
def serve_video():
    return app.send_static_file('video.mp4')

@app.route("/", methods=['GET'])
def home_page():
    global current_test_id
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Data Entry Form</title>
        <style>
            body {{
                font-family: 'MS Sans Serif', Arial, sans-serif;
                background-color: #c0c0c0;
                margin: 0;
                padding: 20px;
            }}
            
            .form-container {{
                background-color: #c0c0c0;
                border: 2px outset #dfdfdf;
                border-right-color: #808080;
                border-bottom-color: #808080;
                padding: 8px;
                width: 450px;
                box-shadow: 1px 1px 0 #ffffff inset, -1px -1px 0 #808080 inset;
                height: fit-content;
            }}
            
            .title-bar {{
                background: linear-gradient(to right, #000080, #1084d7);
                color: white;
                padding: 2px 2px;
                margin: -8px -8px 8px -8px;
                font-weight: bold;
                font-size: 11px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            
            .form-group {{
                margin-bottom: 10px;
                display: flex;
                align-items: center;
            }}
            
            label {{
                width: 140px;
                font-size: 11px;
                color: #000000;
                font-weight: normal;
            }}
            
            input[type="text"],
            input[type="number"] {{
                width: 250px;
                padding: 3px 2px;
                font-family: 'MS Sans Serif', Arial, sans-serif;
                font-size: 11px;
                border: 2px inset #dfdfdf;
                border-right-color: #808080;
                border-bottom-color: #808080;
                background-color: #ffffff;
            }}

            input[type="text"]:focus,
            input[type="number"]:focus {{
                outline: none;
            }}

            /* Combo box styling */
            .combo-box {{
                display: inline-flex;
                position: relative;
                width: 250px;
            }}

            .combo-box input {{
                width: 100%;
                padding: 3px 2px;
                font-family: 'MS Sans Serif', Arial, sans-serif;
                font-size: 11px;
                border: 2px inset #dfdfdf;
                border-right-color: #808080;
                border-bottom-color: #808080;
                background-color: #ffffff;
                box-sizing: border-box;
            }}

            .combo-box .combo-btn {{
                width: 18px;
                min-width: 18px;
                height: auto;
                margin: 0;
                padding: 0;
                font-size: 9px;
                border: 2px outset #dfdfdf;
                border-right-color: #808080;
                border-bottom-color: #808080;
                background-color: #c0c0c0;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
            }}

            .combo-box .combo-btn:active {{
                border-style: inset;
            }}

            .combo-dropdown {{
                display: none;
                position: absolute;
                top: 100%;
                left: 0;
                width: 100%;
                max-height: 150px;
                overflow-y: auto;
                background-color: #ffffff;
                border: 1px solid #808080;
                z-index: 1000;
                box-sizing: border-box;
            }}

            .combo-dropdown.open {{
                display: block;
            }}

            .combo-dropdown div {{
                padding: 2px 4px;
                font-family: 'MS Sans Serif', Arial, sans-serif;
                font-size: 11px;
                cursor: pointer;
                white-space: nowrap;
            }}

            .combo-dropdown div:hover {{
                background-color: #000080;
                color: #ffffff;
            }}
            
            button {{
                width: 90px;
                height: 28px;
                font-family: 'MS Sans Serif', Arial, sans-serif;
                font-size: 11px;
                background-color: #c0c0c0;
                border: 2px outset #dfdfdf;
                border-right-color: #808080;
                border-bottom-color: #808080;
                color: #000000;
                cursor: pointer;
                font-weight: bold;
                margin-top: 15px;
                margin-right: 5px;
            }}
            
            button:active {{
                border-style: inset;
                border-top-color: #808080;
                border-left-color: #808080;
                border-right-color: #dfdfdf;
                border-bottom-color: #dfdfdf;
            }}
            
            .button-group {{
                text-align: center;
                margin-top: 20px;
            }}
            
            .main-container {{
                display: flex;
                gap: 20px;
            }}
            
            .image-container {{
                flex-shrink: 0;
            }}
            
            .image-container img {{
                border: 2px outset #dfdfdf;
                border-right-color: #808080;
                border-bottom-color: #808080;
                background-color: #c0c0c0;
                max-width: 500px;
                height: auto;
            }}

            .video-container {{
                flex-shrink: 0;
                display: none;
            }}

            .video-container video {{
                border: 2px outset #dfdfdf;
                border-right-color: #808080;
                border-bottom-color: #808080;
                background-color: #000000;
                max-width: 500px;
                height: auto;
            }}

            .media-links {{
                margin-top: 15px;
                padding: 8px;
                background-color: #c0c0c0;
                border: 2px inset #dfdfdf;
                border-right-color: #808080;
                border-bottom-color: #808080;
            }}

            .media-links ul {{
                list-style-type: disc;
                margin: 0;
                padding-left: 20px;
                font-size: 11px;
            }}

            .media-links li {{
                margin-bottom: 5px;
            }}

            .media-links a {{
                color: #0000FF;
                text-decoration: underline;
                cursor: pointer;
            }}

            .media-links a:hover {{
                color: #FF0000;
            }}

            #status-message {{
                margin-top: 10px;
                padding: 8px;
                font-size: 11px;
                display: none;
                border: 2px inset #dfdfdf;
                border-right-color: #808080;
                border-bottom-color: #808080;
            }}

            #status-message.success {{
                background-color: #90EE90;
                color: #008000;
                display: block;
            }}

            #status-message.error {{
                background-color: #FFB6C6;
                color: #8B0000;
                display: block;
            }}
        </style>
    </head>
    <body>
        <h1>LabTECH</h1>
        <div class="main-container">
            <div class="form-container">
            <div class="title-bar">
                <span>Test Data Entry</span>
                <span>_</span>
            </div>
            <form id="testForm">
                <div class="form-group">
                    <label for="testid">Test ID:</label>
                    <input type="text" id="testid" name="testid" value="{current_test_id}" required>
                </div>

                <div class="form-group">
                    <label for="campaignid">Campaign ID:</label>
                    <div class="combo-box">
                        <input type="text" id="campaignid" name="campaignid" value="CAMP-2024-001" required>
                        <button type="button" class="combo-btn" data-combo="campaignid">&#9660;</button>
                        <div class="combo-dropdown" data-for="campaignid">
                            <div data-value="CAMP-2024-001">CAMP-2024-001</div>
                            <div data-value="CAMP-2024-002">CAMP-2024-002</div>
                            <div data-value="CAMP-2024-003">CAMP-2024-003</div>
                            <div data-value="CAMP-2025-001">CAMP-2025-001</div>
                        </div>
                    </div>
                </div>

                <div class="form-group">
                    <label for="sampleid">Sample ID:</label>
                    <div class="combo-box">
                        <input type="text" id="sampleid" name="sampleid" value="Device-HP-001" required>
                        <button type="button" class="combo-btn" data-combo="sampleid">&#9660;</button>
                        <div class="combo-dropdown" data-for="sampleid">
                            <div data-value="Device-HP-001">Device-HP-001</div>
                            <div data-value="Device-HP-002">Device-HP-002</div>
                            <div data-value="Device-HP-003">Device-HP-003</div>
                            <div data-value="Device-HP-004">Device-HP-004</div>
                            <div data-value="Device-GB-001">Device-GB-001</div>
                            <div data-value="Device-HP-005">Device-HP-005</div>
                            <div data-value="Device-HP-006">Device-HP-006</div>
                            <div data-value="Device-GB-002">Device-GB-002</div>
                        </div>
                    </div>
                </div>

                <div class="form-group">
                    <label for="environmentid">Environment ID:</label>
                    <div class="combo-box">
                        <input type="text" id="environmentid" name="environmentid" value="Lab-A-01" required>
                        <button type="button" class="combo-btn" data-combo="environmentid">&#9660;</button>
                        <div class="combo-dropdown" data-for="environmentid">
                            <div data-value="Lab-A-01">Lab-A-01</div>
                            <div data-value="Lab-A-02">Lab-A-02</div>
                            <div data-value="Lab-A-03">Lab-A-03</div>
                            <div data-value="Lab-B-01">Lab-B-01</div>
                            <div data-value="Lab-B-02">Lab-B-02</div>
                            <div data-value="Lab-B-03">Lab-B-03</div>
                            <div data-value="TestBench-01">TestBench-01</div>
                            <div data-value="TestBench-02">TestBench-02</div>
                            <div data-value="TestBench-03">TestBench-03</div>
                            <div data-value="TestBench-04">TestBench-04</div>
                            <div data-value="Station-101">Station-101</div>
                            <div data-value="Station-102">Station-102</div>
                            <div data-value="DevLab-1">DevLab-1</div>
                            <div data-value="DevLab-2">DevLab-2</div>
                            <div data-value="QA-Room-1">QA-Room-1</div>
                            <div data-value="QA-Room-2">QA-Room-2</div>
                        </div>
                    </div>
                </div>

                <div class="form-group">
                    <label for="batteryid">Battery ID:</label>
                    <div class="combo-box">
                        <input type="text" id="batteryid" name="batteryid" value="BATT-LI-001" required>
                        <button type="button" class="combo-btn" data-combo="batteryid">&#9660;</button>
                        <div class="combo-dropdown" data-for="batteryid">
                            <div data-value="BATT-LI-001">BATT-LI-001</div>
                            <div data-value="BATT-LI-002">BATT-LI-002</div>
                            <div data-value="BATT-PB-001">BATT-PB-001</div>
                        </div>
                    </div>
                </div>

                <div class="form-group">
                    <label for="fanid">Fan ID:</label>
                    <div class="combo-box">
                        <input type="text" id="fanid" name="fanid" value="FAN-AX-001" required>
                        <button type="button" class="combo-btn" data-combo="fanid">&#9660;</button>
                        <div class="combo-dropdown" data-for="fanid">
                            <div data-value="FAN-AX-001">FAN-AX-001</div>
                            <div data-value="FAN-AX-002">FAN-AX-002</div>
                            <div data-value="FAN-CF-001">FAN-CF-001</div>
                        </div>
                    </div>
                </div>

                <div class="form-group">
                    <label for="motorid">Motor ID:</label>
                    <div class="combo-box">
                        <input type="text" id="motorid" name="motorid" value="MOT-BL-001" required>
                        <button type="button" class="combo-btn" data-combo="motorid">&#9660;</button>
                        <div class="combo-dropdown" data-for="motorid">
                            <div data-value="MOT-BL-001">MOT-BL-001</div>
                            <div data-value="MOT-BL-002">MOT-BL-002</div>
                            <div data-value="MOT-ST-001">MOT-ST-001</div>
                        </div>
                    </div>
                </div>

                <div class="form-group">
                    <label for="shroudid">Shroud ID:</label>
                    <div class="combo-box">
                        <input type="text" id="shroudid" name="shroudid" value="SHR-AL-001" required>
                        <button type="button" class="combo-btn" data-combo="shroudid">&#9660;</button>
                        <div class="combo-dropdown" data-for="shroudid">
                            <div data-value="SHR-AL-001">SHR-AL-001</div>
                            <div data-value="SHR-AL-002">SHR-AL-002</div>
                            <div data-value="SHR-CF-001">SHR-CF-001</div>
                        </div>
                    </div>
                </div>

                <div class="form-group">
                    <label for="throttle">Throttle %:</label>
                    <input type="number" id="throttle" name="throttle" min="0" max="100" value="50" required>
                </div>

                <div class="form-group">
                    <label for="operator">Operator Name:</label>
                    <div class="combo-box">
                        <input type="text" id="operator" name="operator" value="John Smith" required>
                        <button type="button" class="combo-btn" data-combo="operator">&#9660;</button>
                        <div class="combo-dropdown" data-for="operator">
                            <div data-value="John Smith">John Smith</div>
                            <div data-value="Sarah Connor">Sarah Connor</div>
                            <div data-value="Michael Chen">Michael Chen</div>
                            <div data-value="Anna Mueller">Anna Mueller</div>
                            <div data-value="David Park">David Park</div>
                        </div>
                    </div>
                </div>

                <div class="form-group">
                    <label for="holdtime">Hold Time:</label>
                    <div class="combo-box">
                        <input type="text" id="holdtime" name="holdtime" value="30000" required>
                        <button type="button" class="combo-btn" data-combo="holdtime">&#9660;</button>
                        <div class="combo-dropdown" data-for="holdtime">
                            <div data-value="6000">6000 (6 sec)</div>
                            <div data-value="15000">15000 (15 sec)</div>
                            <div data-value="30000">30000 (30 sec)</div>
                            <div data-value="60000">60000 (60 sec)</div>
                            <div data-value="120000">120000 (2 min)</div>
                        </div>
                    </div>
                </div>
                
                <div id="status-message"></div>
                
                <div class="button-group">
                    <button type="button" id="runBtn">Run Test</button>
                    <button type="reset">Clear</button>
                </div>
            </form>
            </div>
            
            <div class="image-container" id="imageContainer">
                <img src="/image_1.png" alt="Test Image">
                <div class="media-links">
                    <ul>
                        <li><a target="_blank" href="https://query-ui-quixers-testrigdemodatawarehouse-prod.az-france-0.app.quix.io/?token=sdk-5de13ff9d5f644b2a614adc6c5b9ac7a">Data warehouse</a></li>
                        <li><a target="_blank" href="https://portal.cloud.quix.io/data?workspace=quixers-testrigdemomeasurementdata-prod">Data lake</a></li>
                        <li><a target="_blank" href="https://portal.cloud.quix.io/pipeline?workspace=quixers-testrigdemomeasurementdata-prod">Measurement data</a></li>
                        <li><a target="_blank" href="https://frontend-quixers-quixtestmanager-new.az-france-0.app.quix.io/">Test Manager</a></li>
                        <li><a target="_blank" href="https://marimo-analysis-quixers-testrigdemoadvancedanalytics-prod.az-france-0.app.quix.io">Full Analysis</a></li>
                        <li><a target="_blank" href="https://simplemarimo-c42ffa5-quixers-testrigdemoadvancedanalytics-prod.az-france-0.app.quix.io">Simple Analysis</a></li>
                    </ul>
                </div>
            </div>

            <div class="video-container" id="videoContainer">
                <video id="testVideo" controls autoplay>
                    <source src="/video.mp4" type="video/mp4">
                    Your browser does not support the video tag.
                </video>
                <div class="media-links">
                    <ul>
                        <li><a target="_blank" href="https://query-ui-quixers-testrigdemodatawarehouse-prod.az-france-0.app.quix.io/?token=sdk-5de13ff9d5f644b2a614adc6c5b9ac7a">Data warehouse</a></li>
                        <li><a target="_blank" href="https://portal.cloud.quix.io/data?workspace=quixers-testrigdemomeasurementdata-prod">Data lake</a></li>
                        <li><a target="_blank" href="https://portal.cloud.quix.io/pipeline?workspace=quixers-testrigdemomeasurementdata-prod">Measurement data</a></li>
                        <li><a target="_blank" href="https://frontend-quixers-quixtestmanager-new.az-france-0.app.quix.io/">Test Manager</a></li>
                        <li><a target="_blank" href="https://marimo-analysis-quixers-testrigdemoadvancedanalytics-prod.az-france-0.app.quix.io">Full Analysis</a></li>
                        <li><a target="_blank" href="https://simplemarimo-c42ffa5-quixers-testrigdemoadvancedanalytics-prod.az-france-0.app.quix.io">Simple Analysis</a></li>
                    </ul>
                </div>
            </div>
        </div>

        <script>
            // Combo box behavior
            document.querySelectorAll('.combo-btn').forEach(function(btn) {{
                btn.addEventListener('click', function(e) {{
                    e.preventDefault();
                    e.stopPropagation();
                    var targetId = btn.getAttribute('data-combo');
                    var dropdown = document.querySelector('.combo-dropdown[data-for="' + targetId + '"]');
                    // Close all other dropdowns
                    document.querySelectorAll('.combo-dropdown.open').forEach(function(d) {{
                        if (d !== dropdown) d.classList.remove('open');
                    }});
                    dropdown.classList.toggle('open');
                }});
            }});

            document.querySelectorAll('.combo-dropdown div').forEach(function(item) {{
                item.addEventListener('click', function() {{
                    var dropdown = item.parentElement;
                    var targetId = dropdown.getAttribute('data-for');
                    var input = document.getElementById(targetId);
                    input.value = item.getAttribute('data-value');
                    dropdown.classList.remove('open');
                }});
            }});

            // Close dropdowns when clicking outside
            document.addEventListener('click', function(e) {{
                if (!e.target.closest('.combo-box')) {{
                    document.querySelectorAll('.combo-dropdown.open').forEach(function(d) {{
                        d.classList.remove('open');
                    }});
                }}
            }});

            function incrementTestId(testId) {{
                const parts = testId.split('-');
                if (parts.length === 2 && /^\\d+$/.test(parts[1])) {{
                    const number = parseInt(parts[1]) + 1;
                    return parts[0] + '-' + String(number).padStart(3, '0');
                }}
                return testId;
            }}

            document.getElementById('runBtn').addEventListener('click', async function(e) {{
                e.preventDefault();
                
                const formData = new FormData(document.getElementById('testForm'));
                const data = {{
                    testid: formData.get('testid'),
                    campaignid: formData.get('campaignid'),
                    sampleid: formData.get('sampleid'),
                    environmentid: formData.get('environmentid'),
                    batteryid: formData.get('batteryid'),
                    fanid: formData.get('fanid'),
                    motorid: formData.get('motorid'),
                    shroudid: formData.get('shroudid'),
                    throttle: formData.get('throttle'),
                    operator: formData.get('operator'),
                    holdtime: formData.get('holdtime')
                }};
                
                try {{
                    const response = await fetch('/api/submit-test', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify(data)
                    }});
                    
                    const result = await response.json();
                    const statusMsg = document.getElementById('status-message');
                    
                    if (response.ok) {{
                        statusMsg.className = 'success';
                        statusMsg.textContent = 'Test submitted successfully!';
                        
                        // Increment the test ID on the client side
                        const currentId = document.getElementById('testid').value;
                        document.getElementById('testid').value = incrementTestId(currentId);

                        // Show video and hide image immediately
                        document.getElementById('imageContainer').style.display = 'none';
                        document.getElementById('videoContainer').style.display = 'block';
                        document.getElementById('testVideo').play();
                        
                    }} else {{
                        statusMsg.className = 'error';
                        statusMsg.textContent = 'Error: ' + (result.error || 'Failed to submit test');
                    }}
                }} catch (error) {{
                    const statusMsg = document.getElementById('status-message');
                    statusMsg.className = 'error';
                    statusMsg.textContent = 'Error: ' + error.message;
                }}
            }});
        </script>
    </body>
    </html>
    """
    return Response(html, mimetype='text/html', status=200)

@app.route("/api/submit-test", methods=['POST'])
def api_submit_test():
    # Handle the AJAX form submission
    global current_test_id
    try:
        data = request.get_json()
        
        # Get or create device and fetch its latest version
        sample_id = data.get('sampleid')
        device_version = None

        headers = {'Content-Type': 'application/json'}
        if api_token:
            headers['Authorization'] = f'Bearer {api_token}'

        try:
            # Try to get the device first
            device_url = f"{test_api_url.rsplit('/tests', 1)[0]}/devices/{sample_id}"
            device_response = requests.get(device_url, headers=headers, timeout=10)

            if device_response.status_code == 404:
                # Device doesn't exist, create it
                logger.info(f"Device {sample_id} not found, creating it")
                device_data = {
                    "device_id": sample_id,
                    "manufacturer": "Siemens",
                    "product_category": "Electronics",
                    "product_name": "SGT-800",
                    "sample_type": "PFP",
                    "location": data.get('environmentid', 'Lab-A-01'),
                    "creator": data.get('operator', 'John Smith')
                }
                create_device_url = f"{test_api_url.rsplit('/tests', 1)[0]}/devices"
                create_response = requests.post(create_device_url, json=device_data, headers=headers, timeout=10)

                if create_response.status_code not in [200, 201]:
                    logger.warning(f"Failed to create device. Status: {create_response.status_code}, Response: {create_response.text}")
                    return jsonify({"error": f"Failed to create device: {create_response.text}"}), 400

            # Get the latest journal entry (device version)
            journal_url = f"{test_api_url.rsplit('/tests', 1)[0]}/devices/{sample_id}/journal"
            journal_response = requests.get(journal_url, headers=headers, timeout=10)

            if journal_response.status_code == 200:
                journal_entries = journal_response.json()
                if journal_entries and len(journal_entries) > 0:
                    # Journal entries are sorted newest first
                    device_version = journal_entries[0].get('device_version')
                    logger.info(f"Using device version: {device_version}")

            if not device_version:
                logger.warning(f"Could not get device version for {sample_id}")
                return jsonify({"error": "Could not retrieve device version"}), 400

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get/create device: {str(e)}")
            return jsonify({"error": "Failed to get or create device"}), 500

        # Format the data according to the API specification
        configuration = {
            "test_id": data.get('testid'),
            "campaign_id": data.get('campaignid'),
            "environment_id": data.get('environmentid'),
            "operator": data.get('operator'),
            "devices": [
                {
                    "device_id": sample_id,
                    "device_version": device_version
                }
            ],
            "sensors": {
                "throttle": {
                    "value": data.get('throttle')
                },
                "hold_time": {
                    "value": data.get('holdtime')
                },
                "battery": {
                    "id": data.get('batteryid')
                },
                "motor": {
                    "id": data.get('motorid')
                },
                "shroud": {
                    "id": data.get('shroudid')
                },
                "fan": {
                    "id": data.get('fanid')
                }
            }
        }

        logger.info(f"Test data formatted: {json.dumps(configuration)}")
        
        # Post test data to the HTTP API
        try:
            headers = {'Content-Type': 'application/json'}
            if api_token:
                headers['Authorization'] = f'Bearer {api_token}'

            response = requests.post(
                test_api_url,
                json=configuration,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 409:
                logger.warning(f"Test API returned status code 409. Response: {response.text}")
                return jsonify({"error": f"Test ID '{data.get('testid')}' already exists. Please use a different Test ID."}), 409
            
            if response.status_code not in [200, 201]:
                logger.warning(f"Test API returned status code {response.status_code}. Response: {response.text}")
                return jsonify({"error": f"Test API failed with status {response.status_code}"}), 400
            
            logger.info(f"Test data posted successfully. Response: {response.text}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to post test data to API: {str(e)}")
            return jsonify({"error": "Failed to submit test data"}), 500
        
        # Post ECU data to a different API
        try:
            ecu_data = {
                "test_id": data.get('testid'),
                "speeds": [data.get('throttle')],
                "ramp_delay": data.get('holdtime')
            }
            
            logger.info(f"ECU data formatted: {json.dumps(ecu_data)}")
            
            ecu_response = requests.post(
                ecu_api_url,
                json=ecu_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if ecu_response.status_code not in [200, 201, 202]:
                logger.warning(f"ECU API returned status code {ecu_response.status_code}. Response: {ecu_response.text}")
                return jsonify({"error": f"ECU API failed with status {ecu_response.status_code}"}), 400
            
            logger.info(f"ECU data posted successfully. Response: {ecu_response.text}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to post ECU data to API: {str(e)}")
            return jsonify({"error": "Failed to submit ECU data"}), 500
        
        # Only increment test ID after both API calls succeed
        current_test_id = increment_test_id(current_test_id)
        
        return jsonify({"success": True, "next_test_id": current_test_id}), 200
    
    except Exception as e:
        logger.error(f"Error submitting test: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    serve(app, host="0.0.0.0", port=80)