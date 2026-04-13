import requests
import sys
import json
import os
from datetime import datetime, timedelta
import time

class SMK3AuditAPITester:
    def __init__(self, base_url="https://smk3-audit.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.admin_token = None
        self.auditor_token = None
        self.auditee_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Test data
        self.test_users = {
            'admin': {'email': f'admin_{int(time.time())}@test.com', 'password': 'TestPass123!', 'name': 'Test Admin', 'role': 'admin'},
            'auditor': {'email': f'auditor_{int(time.time())}@test.com', 'password': 'TestPass123!', 'name': 'Test Auditor', 'role': 'auditor'},
            'auditee': {'email': f'auditee_{int(time.time())}@test.com', 'password': 'TestPass123!', 'name': 'Test Auditee', 'role': 'auditee'}
        }
        
        self.test_criteria_id = None
        self.test_clause_id = None
        self.test_document_id = None
        self.test_recommendation_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, files=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if headers:
            test_headers.update(headers)
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if files:
                # Remove Content-Type for file uploads
                test_headers.pop('Content-Type', None)
                
            if method == 'GET':
                response = requests.get(url, headers=test_headers)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, headers=test_headers)
                else:
                    response = requests.post(url, json=data, headers=test_headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json() if response.content else {}
                except:
                    response_data = {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json().get('detail', 'No detail')
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Response: {response.text[:200]}")
                response_data = {}

            self.test_results.append({
                'name': name,
                'method': method,
                'endpoint': endpoint,
                'expected_status': expected_status,
                'actual_status': response.status_code,
                'success': success
            })

            return success, response_data

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.test_results.append({
                'name': name,
                'method': method,
                'endpoint': endpoint,
                'expected_status': expected_status,
                'actual_status': 'ERROR',
                'success': False,
                'error': str(e)
            })
            return False, {}

    def test_health_check(self):
        """Test API health check"""
        success, _ = self.run_test("Health Check", "GET", "", 200)
        return success

    def test_user_registration(self):
        """Test user registration for all roles"""
        results = {}
        for role, user_data in self.test_users.items():
            success, response = self.run_test(
                f"Register {role}",
                "POST",
                "auth/register",
                200,
                data=user_data
            )
            results[role] = success
            if success:
                print(f"   ✅ {role} registered successfully")
            else:
                print(f"   ❌ {role} registration failed")
        
        return all(results.values())

    def test_user_login(self):
        """Test user login for all roles"""
        results = {}
        for role, user_data in self.test_users.items():
            success, response = self.run_test(
                f"Login {role}",
                "POST",
                "auth/login",
                200,
                data={'email': user_data['email'], 'password': user_data['password']}
            )
            results[role] = success
            if success and 'access_token' in response:
                if role == 'admin':
                    self.admin_token = response['access_token']
                elif role == 'auditor':
                    self.auditor_token = response['access_token']
                elif role == 'auditee':
                    self.auditee_token = response['access_token']
                print(f"   ✅ {role} logged in successfully")
            else:
                print(f"   ❌ {role} login failed")
        
        return all(results.values())

    def test_seed_data(self):
        """Test seeding initial criteria data"""
        self.token = self.admin_token
        success, response = self.run_test(
            "Seed Initial Data",
            "POST",
            "seed-data",
            200
        )
        if success:
            print(f"   ✅ Seeded {response.get('criteria_count', 0)} criteria")
        return success

    def test_criteria_operations(self):
        """Test criteria CRUD operations"""
        self.token = self.admin_token
        
        # Get criteria
        success, criteria = self.run_test("Get Criteria", "GET", "criteria", 200)
        if not success:
            return False
        
        print(f"   📊 Found {len(criteria)} criteria")
        
        # Create new criteria
        new_criteria = {
            "name": "Test Criteria",
            "description": "Test criteria for automated testing",
            "order": 99
        }
        
        success, response = self.run_test(
            "Create Criteria",
            "POST",
            "criteria",
            200,
            data=new_criteria
        )
        
        if success:
            self.test_criteria_id = response.get('id')
            print(f"   ✅ Created criteria with ID: {self.test_criteria_id}")
        
        return success

    def test_clauses_operations(self):
        """Test clauses CRUD operations"""
        if not self.test_criteria_id:
            print("   ❌ No criteria ID available for clause testing")
            return False
            
        self.token = self.admin_token
        
        # Create clause
        new_clause = {
            "criteria_id": self.test_criteria_id,
            "clause_number": "99.1",
            "title": "Test Clause",
            "description": "Test clause for automated testing"
        }
        
        success, response = self.run_test(
            "Create Clause",
            "POST",
            "clauses",
            200,
            data=new_clause
        )
        
        if success:
            self.test_clause_id = response.get('id')
            print(f"   ✅ Created clause with ID: {self.test_clause_id}")
            
            # Update knowledge base
            kb_data = {
                "knowledge_base": "Test knowledge base for automated testing. This clause requires proper documentation and evidence."
            }
            
            success, _ = self.run_test(
                "Update Knowledge Base",
                "PUT",
                f"clauses/{self.test_clause_id}/knowledge-base",
                200,
                data=kb_data
            )
            
            if success:
                print("   ✅ Knowledge base updated successfully")
        
        return success

    def test_document_upload(self):
        """Test document upload functionality"""
        if not self.test_clause_id:
            print("   ❌ No clause ID available for document testing")
            return False
            
        self.token = self.admin_token
        
        # Create a test file
        test_content = "This is a test document for SMK3 audit testing.\nIt contains sample evidence for the test clause."
        
        files = {
            'file': ('test_document.txt', test_content, 'text/plain')
        }
        
        success, response = self.run_test(
            "Upload Document",
            "POST",
            f"clauses/{self.test_clause_id}/upload",
            200,
            files=files
        )
        
        if success:
            self.test_document_id = response.get('id')
            print(f"   ✅ Uploaded document with ID: {self.test_document_id}")
            
            # Get documents for clause
            success, documents = self.run_test(
                "Get Documents",
                "GET",
                f"clauses/{self.test_clause_id}/documents",
                200
            )
            
            if success:
                print(f"   📄 Found {len(documents)} documents for clause")
        
        return success

    def test_ai_audit_analysis(self):
        """Test AI audit analysis"""
        if not self.test_clause_id:
            print("   ❌ No clause ID available for AI audit testing")
            return False
            
        self.token = self.admin_token
        
        print("   🤖 Starting AI analysis (this may take 10-15 seconds)...")
        
        success, response = self.run_test(
            "AI Audit Analysis",
            "POST",
            f"audit/analyze/{self.test_clause_id}",
            200
        )
        
        if success:
            print(f"   ✅ AI Analysis completed")
            print(f"   📊 Score: {response.get('score', 0)}")
            print(f"   📋 Status: {response.get('status', 'Unknown')}")
            
            # Get audit result
            success, result = self.run_test(
                "Get Audit Result",
                "GET",
                f"audit/results/{self.test_clause_id}",
                200
            )
            
            if success:
                print("   ✅ Audit result retrieved successfully")
        
        return success

    def test_dashboard_stats(self):
        """Test dashboard statistics"""
        self.token = self.admin_token
        
        success, stats = self.run_test(
            "Get Dashboard Stats",
            "GET",
            "audit/dashboard",
            200
        )
        
        if success:
            print(f"   📊 Total clauses: {stats.get('total_clauses', 0)}")
            print(f"   📊 Audited clauses: {stats.get('audited_clauses', 0)}")
            print(f"   📊 Average score: {stats.get('average_score', 0)}")
            print(f"   📊 Criteria scores: {len(stats.get('criteria_scores', []))}")
        
        return success

    def test_recommendations(self):
        """Test recommendations functionality"""
        if not self.test_clause_id:
            print("   ❌ No clause ID available for recommendations testing")
            return False
            
        self.token = self.auditor_token
        
        # Create recommendation
        deadline = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        rec_data = {
            "clause_id": self.test_clause_id,
            "recommendation_text": "Test recommendation for automated testing",
            "deadline": deadline
        }
        
        success, response = self.run_test(
            "Create Recommendation",
            "POST",
            "recommendations",
            200,
            data=rec_data
        )
        
        if success:
            self.test_recommendation_id = response.get('id')
            print(f"   ✅ Created recommendation with ID: {self.test_recommendation_id}")
            
            # Update recommendation status
            self.token = self.auditee_token
            update_data = {
                "status": "in_progress"
            }
            
            success, _ = self.run_test(
                "Update Recommendation Status",
                "PUT",
                f"recommendations/{self.test_recommendation_id}",
                200,
                data=update_data
            )
            
            if success:
                print("   ✅ Recommendation status updated")
        
        return success

    def test_notifications(self):
        """Test notifications functionality"""
        self.token = self.admin_token
        
        success, response = self.run_test(
            "Get Notifications",
            "GET",
            "recommendations/notifications",
            200
        )
        
        if success:
            notifications = response.get('notifications', [])
            print(f"   🔔 Found {len(notifications)} notifications")
        
        return success

    def test_report_generation(self):
        """Test PDF report generation"""
        self.token = self.admin_token
        
        print("   📄 Generating PDF report (this may take a few seconds)...")
        
        success, response = self.run_test(
            "Generate PDF Report",
            "POST",
            "reports/generate",
            200
        )
        
        if success:
            filename = response.get('filename', 'Unknown')
            content_length = len(response.get('content', ''))
            print(f"   ✅ Report generated: {filename}")
            print(f"   📄 Content size: {content_length} characters (base64)")
        
        return success

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting SMK3 Audit API Tests")
        print("=" * 50)
        
        test_sequence = [
            ("Health Check", self.test_health_check),
            ("User Registration", self.test_user_registration),
            ("User Login", self.test_user_login),
            ("Seed Data", self.test_seed_data),
            ("Criteria Operations", self.test_criteria_operations),
            ("Clauses Operations", self.test_clauses_operations),
            ("Document Upload", self.test_document_upload),
            ("AI Audit Analysis", self.test_ai_audit_analysis),
            ("Dashboard Stats", self.test_dashboard_stats),
            ("Recommendations", self.test_recommendations),
            ("Notifications", self.test_notifications),
            ("Report Generation", self.test_report_generation)
        ]
        
        failed_tests = []
        
        for test_name, test_func in test_sequence:
            print(f"\n{'='*20} {test_name} {'='*20}")
            try:
                success = test_func()
                if not success:
                    failed_tests.append(test_name)
                    print(f"❌ {test_name} FAILED")
                else:
                    print(f"✅ {test_name} PASSED")
            except Exception as e:
                failed_tests.append(test_name)
                print(f"❌ {test_name} ERROR: {str(e)}")
        
        # Print final results
        print("\n" + "="*50)
        print("📊 FINAL RESULTS")
        print("="*50)
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if failed_tests:
            print(f"\n❌ Failed test categories: {', '.join(failed_tests)}")
            return 1
        else:
            print("\n✅ All test categories passed!")
            return 0

def main():
    tester = SMK3AuditAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())