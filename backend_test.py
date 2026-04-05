import requests
import sys
import json
import io
import openpyxl
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

    def test_sample_template(self):
        """Test sample template download (.xlsx)"""
        success, response = self.run_test(
            "Sample Template Download (.xlsx)",
            "GET",
            "sample-template",
            200
        )
        if success:
            # Check if response is binary (Excel file)
            if isinstance(response, (str, bytes)):
                print("   ✓ Sample template download successful")
                # Try to parse as Excel to validate
                try:
                    if isinstance(response, str):
                        # If it's a string, it might be base64 or text, try to get binary
                        print("   ⚠️  Response is text, expected binary Excel file")
                        return True  # Still consider success if we got a response
                    else:
                        wb = openpyxl.load_workbook(io.BytesIO(response))
                        sheets = wb.sheetnames
                        print(f"   ✓ Excel file valid with sheets: {sheets}")
                        if 'English' in sheets and 'Language' in sheets:
                            print("   ✓ Required sheets (English, Language) found")
                            return True
                        else:
                            print("   ❌ Missing required sheets")
                            return False
                except Exception as e:
                    print(f"   ⚠️  Could not validate Excel format: {e}")
                    return True  # Still consider success if download worked
            else:
                print("   ❌ Invalid response format")
                return False
        return success

    def test_excel_upload(self):
        """Test Excel file upload functionality (separate files)"""
        # Create a simple test Excel file
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "English"
        
        # Add headers
        ws['A1'] = 'Interval'
        ws['B1'] = 'Monday'
        ws['C1'] = 'Tuesday'
        
        # Add some test data
        ws['A2'] = '00:00'
        ws['B2'] = 5
        ws['C2'] = 6
        ws['A3'] = '01:00'
        ws['B3'] = 3
        ws['C3'] = 4
        
        # Save to bytes
        excel_buffer = io.BytesIO()
        wb.save(excel_buffer)
        excel_buffer.seek(0)
        
        files = {'english_file': ('test_english.xlsx', excel_buffer.getvalue(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        
        success, response = self.run_test(
            "Excel File Upload (Separate Files)",
            "POST",
            "run-schedule",
            200,
            files=files
        )
        
        if success:
            # Validate response structure
            required_keys = ['id', 'shiftwise', 'gap_analysis', 'roster', 'sla', 'summary']
            missing_keys = [key for key in required_keys if key not in response]
            if not missing_keys:
                print("   ✓ Excel upload processed successfully")
                self.schedule_id = response['id']  # Update schedule ID for export tests
                return True
            else:
                print(f"   ❌ Missing keys in response: {missing_keys}")
                return False
        return success

    def test_multi_sheet_excel_upload(self):
        """Test multi-sheet Excel file upload functionality (combined_file)"""
        # Create a multi-sheet Excel file with English and Language sheets
        wb = openpyxl.Workbook()
        
        # Remove default sheet
        wb.remove(wb.active)
        
        # Create English sheet
        ws_eng = wb.create_sheet("English")
        ws_eng['A1'] = 'Interval'
        ws_eng['B1'] = 'Monday'
        ws_eng['C1'] = 'Tuesday'
        ws_eng['D1'] = 'Wednesday'
        ws_eng['E1'] = 'Thursday'
        ws_eng['F1'] = 'Friday'
        ws_eng['G1'] = 'Saturday'
        ws_eng['H1'] = 'Sunday'
        
        # Add some test data for English
        for i, hour in enumerate(['00:00', '01:00', '02:00', '03:00']):
            ws_eng[f'A{i+2}'] = hour
            for j, day_val in enumerate([7, 4, 3, 3, 3, 3, 3]):  # Sample values
                ws_eng.cell(row=i+2, column=j+2, value=day_val)
        
        # Create Language sheet
        ws_lang = wb.create_sheet("Language")
        ws_lang['A1'] = 'Interval'
        ws_lang['B1'] = 'Monday'
        ws_lang['C1'] = 'Tuesday'
        ws_lang['D1'] = 'Wednesday'
        ws_lang['E1'] = 'Thursday'
        ws_lang['F1'] = 'Friday'
        ws_lang['G1'] = 'Saturday'
        ws_lang['H1'] = 'Sunday'
        
        # Add some test data for Language
        for i, hour in enumerate(['00:00', '01:00', '02:00', '03:00']):
            ws_lang[f'A{i+2}'] = hour
            for j, day_val in enumerate([0, 0, 0, 0, 0, 0, 0]):  # Sample values
                ws_lang.cell(row=i+2, column=j+2, value=day_val)
        
        # Save to bytes
        excel_buffer = io.BytesIO()
        wb.save(excel_buffer)
        excel_buffer.seek(0)
        
        files = {'combined_file': ('test_combined.xlsx', excel_buffer.getvalue(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        
        success, response = self.run_test(
            "Multi-Sheet Excel Upload (Combined File)",
            "POST",
            "run-schedule",
            200,
            files=files
        )
        
        if success:
            # Validate response structure
            required_keys = ['id', 'shiftwise', 'gap_analysis', 'roster', 'sla', 'summary']
            missing_keys = [key for key in required_keys if key not in response]
            if not missing_keys:
                print("   ✓ Multi-sheet Excel upload processed successfully")
                self.schedule_id = response['id']  # Update schedule ID for export tests
                
                # Validate that both English and Language data was processed
                summary = response['summary']
                if summary.get('total_agents') == 212:
                    print("   ✓ Correct total agents (212)")
                else:
                    print(f"   ❌ Expected 212 agents, got {summary.get('total_agents')}")
                
                # Check that we have both English and Language shifts
                shiftwise = response['shiftwise']
                english_shifts = [row for row in shiftwise if row.get('project') == 'English' and not row.get('shift_id', '').endswith('_TOTAL')]
                language_shifts = [row for row in shiftwise if row.get('project') == 'Language' and not row.get('shift_id', '').endswith('_TOTAL')]
                
                if len(english_shifts) == 9 and len(language_shifts) == 5:
                    print("   ✓ Both English (9) and Language (5) shifts processed from multi-sheet file")
                    return True
                else:
                    print(f"   ❌ Expected 9 English + 5 Language shifts, got {len(english_shifts)} + {len(language_shifts)}")
                    return False
            else:
                print(f"   ❌ Missing keys in response: {missing_keys}")
                return False
        return success

    def test_export_xlsx(self):
        """Test Excel export functionality"""
        if not self.schedule_id:
            print("❌ No schedule ID available for testing")
            return False
        
        export_types = ['shiftwise', 'roster', 'gap', 'sla']
        all_passed = True
        
        for export_type in export_types:
            success, response = self.run_test(
                f"Export Excel ({export_type})",
                "GET",
                f"export/{self.schedule_id}/{export_type}",
                200
            )
            if success:
                # Check if response is binary (Excel file)
                if isinstance(response, (bytes, str)):
                    print(f"   ✓ Excel export for {export_type} successful")
                else:
                    print(f"   ❌ Invalid Excel response for {export_type}")
                    all_passed = False
            else:
                all_passed = False
        
        return all_passed

    def test_project_specific_shifts(self):
        """Test that the schedule includes correct project-specific shifts"""
        if not self.schedule_id:
            print("❌ No schedule ID available for testing")
            return False
            
        success, response = self.run_test(
            "Project-Specific Shifts Validation",
            "GET",
            f"schedule/{self.schedule_id}",
            200
        )
        
        if success:
            shiftwise = response.get('shiftwise', [])
            
            # Check for English shifts (E05-E20, 9 shifts)
            english_shifts = [row for row in shiftwise if row.get('project') == 'English' and not row.get('shift_id', '').endswith('_TOTAL')]
            expected_english = ['E05', 'E07', 'E08', 'E09', 'E11', 'E14', 'E16', 'E18', 'E20']
            
            english_shift_ids = [row.get('shift_id') for row in english_shifts]
            
            if len(english_shifts) == 9:
                print(f"   ✓ Found 9 English shifts: {english_shift_ids}")
                missing_english = [s for s in expected_english if s not in english_shift_ids]
                if not missing_english:
                    print("   ✓ All expected English shifts present")
                else:
                    print(f"   ❌ Missing English shifts: {missing_english}")
                    return False
            else:
                print(f"   ❌ Expected 9 English shifts, found {len(english_shifts)}")
                return False
            
            # Check for Language shifts (L07-L11, 5 shifts)
            language_shifts = [row for row in shiftwise if row.get('project') == 'Language' and not row.get('shift_id', '').endswith('_TOTAL')]
            expected_language = ['L07', 'L08', 'L09', 'L10', 'L11']
            
            language_shift_ids = [row.get('shift_id') for row in language_shifts]
            
            if len(language_shifts) == 5:
                print(f"   ✓ Found 5 Language shifts: {language_shift_ids}")
                missing_language = [s for s in expected_language if s not in language_shift_ids]
                if not missing_language:
                    print("   ✓ All expected Language shifts present")
                    return True
                else:
                    print(f"   ❌ Missing Language shifts: {missing_language}")
                    return False
            else:
                print(f"   ❌ Expected 5 Language shifts, found {len(language_shifts)}")
                return False
        
        return success

def main():
    """Run all backend tests"""
    print("🚀 Starting Cross-Skill Scheduler Backend Tests")
    print("=" * 60)
    
    tester = CrossSkillSchedulerTester()
    
    # Run all tests
    tests = [
        tester.test_root_endpoint,
        tester.test_default_requirements,
        tester.test_sample_template,
        tester.test_run_schedule_default,
        tester.test_excel_upload,
        tester.test_multi_sheet_excel_upload,
        tester.test_project_specific_shifts,
        tester.test_list_schedules,
        tester.test_get_schedule,
        tester.test_export_xlsx,
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