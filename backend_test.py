#!/usr/bin/env python3
"""
DriveShare & Dock Backend API Test Suite
Tests all backend endpoints including auth, listings, payments, and more.
"""

import asyncio
import aiohttp
import json
import sys
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Backend URL from environment
BACKEND_URL = "https://forest-dock.preview.emergentagent.com/api"

class BackendTester:
    def __init__(self):
        self.session = None
        self.auth_token = None
        # Use unique email for each test run to avoid conflicts
        unique_id = str(uuid.uuid4())[:8]
        self.test_user_data = {
            "name": "Test User",
            "email": f"test_{unique_id}@example.com", 
            "phone": "555-1234",
            "password": "password123"
        }
        self.test_results = []
        
    async def setup_session(self):
        """Setup HTTP session"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
            
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "response_data": response_data
        })
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        if not success and response_data:
            print(f"    Response: {response_data}")
        print()
        
    async def make_request(self, method: str, endpoint: str, data: Dict = None, headers: Dict = None) -> tuple:
        """Make HTTP request and return (success, response_data, status_code)"""
        url = f"{BACKEND_URL}{endpoint}"
        
        # Add auth header if token exists
        if self.auth_token and headers is None:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
        elif self.auth_token and headers:
            headers["Authorization"] = f"Bearer {self.auth_token}"
            
        try:
            async with self.session.request(method, url, json=data, headers=headers) as response:
                try:
                    response_data = await response.json()
                except:
                    response_data = await response.text()
                    
                return response.status < 400, response_data, response.status
        except Exception as e:
            return False, str(e), 0
            
    async def test_root_endpoint(self):
        """Test API health by checking if backend is accessible"""
        # Since root endpoint (/) is not accessible through /api path in this setup,
        # we'll test backend health by checking a known working endpoint
        success, data, status = await self.make_request("GET", "/listings", headers={})
        
        if success and isinstance(data, list):
            self.log_test("Backend Health Check", True, 
                         f"Backend is accessible and responding correctly (listings endpoint)")
        else:
            self.log_test("Backend Health Check", False, f"Backend not accessible, Status: {status}", data)
            
    async def test_auth_register(self):
        """Test POST /auth/register"""
        success, data, status = await self.make_request("POST", "/auth/register", self.test_user_data, headers={})
        
        if success and isinstance(data, dict) and "token" in data and "user" in data:
            self.auth_token = data["token"]
            user = data["user"]
            expected_fields = ["id", "email", "name", "phone", "is_verified", "created_at"]
            
            if all(field in user for field in expected_fields):
                self.log_test("Auth Register", True, 
                             f"User created: {user['email']}, Verified: {user['is_verified']}")
                
                # Save credentials for future use
                await self.save_test_credentials(data)
            else:
                self.log_test("Auth Register", False, "Missing user fields", data)
        else:
            self.log_test("Auth Register", False, f"Status: {status}", data)
            
    async def test_auth_login(self):
        """Test POST /auth/login"""
        login_data = {
            "email": self.test_user_data["email"],
            "password": self.test_user_data["password"]
        }
        
        success, data, status = await self.make_request("POST", "/auth/login", login_data, headers={})
        
        if success and isinstance(data, dict) and "token" in data and "user" in data:
            self.auth_token = data["token"]  # Update token
            user = data["user"]
            
            if user["email"] == self.test_user_data["email"]:
                self.log_test("Auth Login", True, f"Login successful for: {user['email']}")
            else:
                self.log_test("Auth Login", False, "Email mismatch", data)
        else:
            self.log_test("Auth Login", False, f"Status: {status}", data)
            
    async def test_auth_me(self):
        """Test GET /auth/me"""
        if not self.auth_token:
            self.log_test("Auth Me", False, "No auth token available")
            return
            
        success, data, status = await self.make_request("GET", "/auth/me")
        
        if success and isinstance(data, dict):
            expected_fields = ["id", "email", "name", "phone", "is_verified", "created_at"]
            
            if all(field in data for field in expected_fields):
                self.log_test("Auth Me", True, 
                             f"User info retrieved: {data['email']}, Verified: {data['is_verified']}")
            else:
                self.log_test("Auth Me", False, "Missing user fields", data)
        else:
            self.log_test("Auth Me", False, f"Status: {status}", data)
            
    async def test_listings_get_without_auth(self):
        """Test GET /listings without authentication"""
        success, data, status = await self.make_request("GET", "/listings", headers={})
        
        if success and isinstance(data, list):
            self.log_test("Listings GET (No Auth)", True, 
                         f"Retrieved {len(data)} listings without authentication")
        else:
            self.log_test("Listings GET (No Auth)", False, f"Status: {status}", data)
            
    async def test_listings_post_without_verification(self):
        """Test POST /listings without verification (should fail with 403)"""
        if not self.auth_token:
            self.log_test("Listings POST (No Verification)", False, "No auth token available")
            return
            
        listing_data = {
            "category": "rv_rental",
            "title": "Test RV Rental",
            "description": "A beautiful RV for rent",
            "price": 150.0,
            "location": "San Francisco, CA",
            "images": ["data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k="],
            "amenities": {"wifi": True, "kitchen": True}
        }
        
        success, data, status = await self.make_request("POST", "/listings", listing_data)
        
        # Should fail with 403 because user is not verified
        if not success and status == 403:
            self.log_test("Listings POST (No Verification)", True, 
                         "Correctly rejected unverified user with 403")
        elif success:
            self.log_test("Listings POST (No Verification)", False, 
                         "Should have failed for unverified user", data)
        else:
            self.log_test("Listings POST (No Verification)", False, f"Status: {status}", data)
            
    async def test_stripe_verification_create_checkout(self):
        """Test POST /payments/verification/create-checkout"""
        if not self.auth_token:
            self.log_test("Stripe Verification Checkout", False, "No auth token available")
            return
            
        # Use the frontend URL as origin
        origin_url = "https://forest-dock.preview.emergentagent.com"
        
        success, data, status = await self.make_request(
            "POST", 
            f"/payments/verification/create-checkout?origin_url={origin_url}"
        )
        
        if success and isinstance(data, dict):
            if "url" in data and "session_id" in data:
                # Verify URL contains Stripe checkout
                if "checkout.stripe.com" in data["url"] or "stripe" in data["url"].lower():
                    self.log_test("Stripe Verification Checkout", True, 
                                 f"Checkout session created: {data['session_id']}")
                else:
                    self.log_test("Stripe Verification Checkout", False, 
                                 "URL doesn't appear to be Stripe checkout", data)
            else:
                self.log_test("Stripe Verification Checkout", False, 
                             "Missing url or session_id", data)
        else:
            self.log_test("Stripe Verification Checkout", False, f"Status: {status}", data)
            
    async def test_additional_endpoints(self):
        """Test additional endpoints for completeness"""
        
        # Test listings with category filter
        success, data, status = await self.make_request("GET", "/listings?category=rv_rental", headers={})
        if success:
            self.log_test("Listings GET (Category Filter)", True, f"Retrieved listings for rv_rental")
        else:
            self.log_test("Listings GET (Category Filter)", False, f"Status: {status}", data)
            
        # Test user's own listings (requires auth)
        if self.auth_token:
            success, data, status = await self.make_request("GET", "/listings/user/me")
            if success and isinstance(data, list):
                self.log_test("User Listings GET", True, f"Retrieved {len(data)} user listings")
            else:
                self.log_test("User Listings GET", False, f"Status: {status}", data)
                
    async def test_error_scenarios(self):
        """Test error handling scenarios"""
        
        # Test invalid login credentials
        invalid_login = {
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        success, data, status = await self.make_request("POST", "/auth/login", invalid_login, headers={})
        if not success and status == 401:
            self.log_test("Invalid Login Credentials", True, "Correctly rejected invalid credentials with 401")
        else:
            self.log_test("Invalid Login Credentials", False, f"Should have failed with 401, got {status}", data)
            
        # Test accessing protected endpoint without auth
        success, data, status = await self.make_request("GET", "/auth/me", headers={})
        if not success and status == 401:
            self.log_test("Protected Endpoint (No Auth)", True, "Correctly rejected unauthenticated request with 401")
        else:
            self.log_test("Protected Endpoint (No Auth)", False, f"Should have failed with 401, got {status}", data)
            
        # Test invalid auth token
        invalid_headers = {"Authorization": "Bearer invalid_token_here"}
        # Temporarily clear the valid token to ensure we're testing with invalid token
        original_token = self.auth_token
        self.auth_token = None
        success, data, status = await self.make_request("GET", "/auth/me", headers=invalid_headers)
        self.auth_token = original_token  # Restore valid token
        
        if not success and status == 401:
            self.log_test("Invalid Auth Token", True, "Correctly rejected invalid token with 401")
        else:
            self.log_test("Invalid Auth Token", False, f"Should have failed with 401, got {status}", data)
                
    async def save_test_credentials(self, auth_data: Dict):
        """Save test credentials to memory file"""
        try:
            credentials = {
                "test_user": {
                    "email": self.test_user_data["email"],
                    "password": self.test_user_data["password"],
                    "name": self.test_user_data["name"],
                    "phone": self.test_user_data["phone"],
                    "token": auth_data["token"],
                    "user_id": auth_data["user"]["id"],
                    "is_verified": auth_data["user"]["is_verified"],
                    "created_at": datetime.now().isoformat()
                }
            }
            
            with open("/app/memory/test_credentials.md", "w") as f:
                f.write("# Test Credentials\n")
                f.write("# Agent writes here when creating/modifying auth credentials (admin accounts, test users).\n")
                f.write("# Testing agent reads this before auth tests. Fork/continuation agents read on startup.\n\n")
                f.write("## Test User Credentials\n")
                f.write(f"- **Email**: {credentials['test_user']['email']}\n")
                f.write(f"- **Password**: {credentials['test_user']['password']}\n")
                f.write(f"- **Name**: {credentials['test_user']['name']}\n")
                f.write(f"- **Phone**: {credentials['test_user']['phone']}\n")
                f.write(f"- **User ID**: {credentials['test_user']['user_id']}\n")
                f.write(f"- **Verified**: {credentials['test_user']['is_verified']}\n")
                f.write(f"- **Token**: {credentials['test_user']['token'][:50]}...\n")
                f.write(f"- **Created**: {credentials['test_user']['created_at']}\n")
                
        except Exception as e:
            print(f"Failed to save credentials: {e}")
            
    async def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting DriveShare & Dock Backend API Tests")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 60)
        
        await self.setup_session()
        
        try:
            # Core API tests as specified in review request
            await self.test_root_endpoint()
            await self.test_auth_register()
            await self.test_auth_login()
            await self.test_auth_me()
            await self.test_listings_get_without_auth()
            await self.test_listings_post_without_verification()
            await self.test_stripe_verification_create_checkout()
            
            # Additional endpoint tests
            await self.test_additional_endpoints()
            
            # Error handling tests
            await self.test_error_scenarios()
            
        finally:
            await self.cleanup_session()
            
        # Print summary
        print("=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
                    
        return failed_tests == 0

async def main():
    """Main test runner"""
    tester = BackendTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())