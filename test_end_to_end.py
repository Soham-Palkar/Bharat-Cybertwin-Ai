"""
End-to-end test script for Modules 5 & 6
"""
import requests
import time

BASE_URL = "http://localhost:8000"


def main():
    print("=== CyberTwin AI - End-to-End Test ===\n")

    # Step 1: Upload test assets
    print("1. Uploading test assets...")
    assets_data = {
        "assets": [
            {"name": "Critical Server", "asset_type": "server", "ip_address": "10.0.0.10", "criticality": "Critical"},
            {"name": "Low Risk Laptop", "asset_type": "endpoint", "ip_address": "192.168.1.50", "criticality": "Low"}
        ]
    }
    response = requests.post(f"{BASE_URL}/upload-assets", json=assets_data)
    response.raise_for_status()
    asset_ids = response.json()["asset_ids"]
    critical_asset_id = asset_ids[0]
    low_asset_id = asset_ids[1]
    print(f"   - Critical Asset ID: {critical_asset_id}")
    print(f"   - Low Risk Asset ID: {low_asset_id}")

    # Step 2: Simulate a bruteforce attack on the critical asset
    print("\n2. Simulating brute-force attack on Critical Server...")
    response = requests.post(
        f"{BASE_URL}/simulate/bruteforce",
        json={"asset_id": critical_asset_id, "intensity": 100}
    )
    response.raise_for_status()
    print("   - Attack simulated successfully")

    # Step 3: Run detection immediately
    print("\n3. Running detection scan...")
    response = requests.post(f"{BASE_URL}/detect/run-now")
    response.raise_for_status()
    detect_result = response.json()
    print(f"   - Detection complete, created {detect_result['incidents_created']} new incidents")

    # Step 4: Get incidents
    print("\n4. Checking incidents...")
    response = requests.get(f"{BASE_URL}/incidents")
    response.raise_for_status()
    incidents = response.json()
    print(f"   - Found {len(incidents)} total incidents")

    # Step 5: Run risk scan
    print("\n5. Running risk scan...")
    response = requests.post(f"{BASE_URL}/risk/scan")
    response.raise_for_status()
    print("   - Risk scan complete")

    # Step 6: Get ML anomalies
    print("\n6. Getting ML anomaly scores...")
    response = requests.get(f"{BASE_URL}/ml/anomalies")
    response.raise_for_status()
    ml_data = response.json()
    print(f"   - Scored {ml_data['asset_count']} assets")
    for asset in ml_data["assets"]:
        print(f"   - Asset {asset['asset_id']}: Threat Confidence {asset['threat_confidence']:.1f}%")

    # Step 7: Get risk scores
    print("\n7. Getting risk scores...")
    response = requests.get(f"{BASE_URL}/risk")
    response.raise_for_status()
    risk_data = response.json()
    print(f"   - Found {risk_data['asset_count']} assets with risk scores")
    for asset in risk_data["assets"]:
        print(f"\n   - {asset['asset_name']} ({asset['asset_criticality']}):")
        print(f"      Rule Score: {asset['rule_score']}")
        print(f"      ML Score: {asset['ml_score']:.1f}")
        print(f"      Criticality Weight: {asset['criticality_weight']}")
        print(f"      Total Score: {asset['total_score']:.1f}")
        print(f"      Severity: {asset['severity']}")

    print("\n=== Test Complete ===")


if __name__ == "__main__":
    main()
