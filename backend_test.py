import requests
import sys
import json
from datetime import datetime

class CrossSkillSchedulerTester:
    def __init__(self, base_url="https://sla-scheduler-pro.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.schedule_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}" if endpoint else self.base_url
        headers = {}
        if data and not files:
            headers['Content-Type'] = 'application/json'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, timeout=60)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=60)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test root API endpoint"""
        success, response = self.run_test(
            "Root API Endpoint",
            "GET",
            "",
            200
        )
        return success

    def test_default_requirements(self):
        """Test default requirements endpoint"""
        success, response = self.run_test(
            "Default Requirements",
            "GET",
            "default-requirements",
            200
        )
        if success:
            # Validate response structure
            if 'english' in response and 'language' in response:
                print("   ✓ Response contains english and language data")
                # Check if Monday data exists
                if 'Monday' in response['english'] and 'Monday' in response['language']:
                    print("   ✓ Monday data found in both english and language")
                    return True
                else:
                    print("   ❌ Missing Monday data")
                    return False
            else:
                print("   ❌ Invalid response structure")
                return False
        return success

    def test_run_schedule_default(self):
        """Test running schedule with default data (no files)"""
        success, response = self.run_test(
            "Run Schedule (Default Data)",
            "POST",
            "run-schedule",
            200
        )
        if success:
            # Validate response structure
            required_keys = ['id', 'shiftwise', 'gap_analysis', 'roster', 'sla', 'summary']
            missing_keys = [key for key in required_keys if key not in response]
            if not missing_keys:
                print("   ✓ All required response keys present")
                self.schedule_id = response['id']
                print(f"   ✓ Schedule ID: {self.schedule_id}")
                
                # Validate summary data
                summary = response['summary']
                if summary.get('total_agents') == 212:
                    print("   ✓ Correct total agents (212)")
                else:
                    print(f"   ❌ Expected 212 agents, got {summary.get('total_agents')}")
                
                if summary.get('shift_patterns') == 9:
                    print("   ✓ Correct shift patterns (9)")
                else:
                    print(f"   ❌ Expected 9 shift patterns, got {summary.get('shift_patterns')}")
                
                # Validate shiftwise data
                shiftwise = response['shiftwise']
                if len(shiftwise) == 10:  # 9 shifts + TOTAL row
                    print("   ✓ Correct shiftwise rows (9 shifts + TOTAL)")
                else:
                    print(f"   ❌ Expected 10 shiftwise rows, got {len(shiftwise)}")
                
                # Validate roster data
                roster = response['roster']
                if len(roster) == 212:
                    print("   ✓ Correct roster size (212 agents)")
                else:
                    print(f"   ❌ Expected 212 roster entries, got {len(roster)}")
                
                return True
            else:
                print(f"   ❌ Missing keys: {missing_keys}")
                return False
        return success

    def test_list_schedules(self):
        """Test listing schedules"""
        success, response = self.run_test(
            "List Schedules",
            "GET",
            "schedules",
            200
        )
        if success and isinstance(response, list):
            print(f"   ✓ Found {len(response)} schedules")
            return True
        return success

    def test_get_schedule(self):
        """Test getting specific schedule"""
        if not self.schedule_id:
            print("❌ No schedule ID available for testing")
            return False
            
        success, response = self.run_test(
            "Get Specific Schedule",
            "GET",
            f"schedule/{self.schedule_id}",
            200
        )
        if success:
            required_keys = ['id', 'shiftwise', 'gap_analysis', 'roster', 'sla', 'summary']
            missing_keys = [key for key in required_keys if key not in response]
            if not missing_keys:
                print("   ✓ All required response keys present")
                return True
            else:
                print(f"   ❌ Missing keys: {missing_keys}")
                return False
        return success

    def test_export_csv(self):
        """Test CSV export functionality"""
        if not self.schedule_id:
            print("❌ No schedule ID available for testing")
            return False
        
        export_types = ['shiftwise', 'roster', 'gap', 'sla']
        all_passed = True
        
        for export_type in export_types:
            success, response = self.run_test(
                f"Export CSV ({export_type})",
                "GET",
                f"export/{self.schedule_id}/{export_type}",
                200
            )
            if success:
                # Check if response looks like CSV
                if isinstance(response, str) and ',' in response:
                    print(f"   ✓ CSV export for {export_type} successful")
                else:
                    print(f"   ❌ Invalid CSV response for {export_type}")
                    all_passed = False
            else:
                all_passed = False
        
        return all_passed

def main():
    """Run all backend tests"""
    print("🚀 Starting Cross-Skill Scheduler Backend Tests")
    print("=" * 60)
    
    tester = CrossSkillSchedulerTester()
    
    # Run all tests
    tests = [
        tester.test_root_endpoint,
        tester.test_default_requirements,
        tester.test_run_schedule_default,
        tester.test_list_schedules,
        tester.test_get_schedule,
        tester.test_export_csv,
    ]
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
    
    # Print results
    print("\n" + "=" * 60)
    print(f"📊 Backend Tests Summary:")
    print(f"   Tests Run: {tester.tests_run}")
    print(f"   Tests Passed: {tester.tests_passed}")
    print(f"   Success Rate: {(tester.tests_passed/tester.tests_run*100):.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All backend tests passed!")
        return 0
    else:
        print("⚠️  Some backend tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())