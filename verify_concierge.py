#!/usr/bin/env python3
"""
PocketProSBA Concierge Verification Script

This script performs a comprehensive test of the PocketProSBA application,
focusing on the concierge greeting functionality and user experience.
"""

import requests
import json
import time
import os
import sys
from colorama import init, Fore, Style

# Initialize colorama for cross-platform colored terminal output
init()

# Base URLs to test
URLS = [
    "http://localhost:8080",  # Nginx
    "http://localhost:5000",  # Backend direct
]

def print_header(text):
    """Print a formatted header"""
    print(f"\n{Fore.CYAN}{'=' * 80}")
    print(f" {text}")
    print(f"{'=' * 80}{Style.RESET_ALL}\n")

def print_success(text):
    """Print a success message"""
    print(f"{Fore.GREEN}✓ {text}{Style.RESET_ALL}")

def print_error(text):
    """Print an error message"""
    print(f"{Fore.RED}✗ {text}{Style.RESET_ALL}")

def print_warning(text):
    """Print a warning message"""
    print(f"{Fore.YELLOW}! {text}{Style.RESET_ALL}")

def print_info(text):
    """Print an info message"""
    print(f"{Fore.BLUE}ℹ {text}{Style.RESET_ALL}")

def print_json(data):
    """Print formatted JSON data"""
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            print(data)
            return
    
    print(f"{Fore.MAGENTA}{json.dumps(data, indent=2)}{Style.RESET_ALL}")

def test_backend_connection(base_url):
    """Test basic connection to the backend"""
    print_header(f"Testing Backend Connection: {base_url}")
    
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        if response.ok:
            print_success(f"Connected to backend: {base_url}")
            try:
                data = response.json()
                print_info("Health check response:")
                print_json(data)
                return True
            except json.JSONDecodeError:
                print_warning(f"Received non-JSON response: {response.text[:100]}...")
                return True
        else:
            print_error(f"Failed to connect to backend: HTTP {response.status_code}")
            print_info(f"Response: {response.text[:100]}...")
            return False
    except requests.RequestException as e:
        print_error(f"Connection error: {str(e)}")
        return False

def test_concierge_workflow(base_url):
    """Test the complete concierge greeting workflow"""
    print_header(f"Testing Concierge Greeting Workflow: {base_url}")
    
    # Step 1: Start a session with a system message
    print_info("Step 1: Starting a user session with SYSTEM message")
    try:
        response = requests.post(
            f"{base_url}/api/chat",
            json={"message": "SYSTEM: User session started", "userName": "TestUser"},
            timeout=5
        )
        
        if response.ok:
            try:
                data = response.json()
                print_success("Session started successfully")
                print_json(data)
                
                # Check if the response contains a personalized greeting
                if "TestUser" in str(data):
                    print_success("Response is personalized with the user's name")
                else:
                    print_warning("Response does not appear to be personalized with the user's name")
            except json.JSONDecodeError:
                print_error("Failed to parse JSON response")
                print_info(f"Raw response: {response.text[:200]}...")
        else:
            print_error(f"Failed to start session: HTTP {response.status_code}")
            print_info(f"Response: {response.text[:100]}...")
            return False
    except requests.RequestException as e:
        print_error(f"Connection error during session start: {str(e)}")
        return False
    
    # Step 2: Send a regular chat message as the same user
    print_info("\nStep 2: Sending a regular chat message")
    try:
        response = requests.post(
            f"{base_url}/api/chat",
            json={"message": "Tell me about SBA loans", "userName": "TestUser"},
            timeout=5
        )
        
        if response.ok:
            try:
                data = response.json()
                print_success("Message sent successfully")
                print_json(data)
                
                # Check if the response contains the user's name
                if "TestUser" in str(data) or "TestUser" in str(response.text):
                    print_success("Response is personalized with the user's name")
                else:
                    print_warning("Response does not appear to be personalized with the user's name")
                
                # Check if the response contains information about SBA loans
                if "loan" in str(data).lower() or "sba" in str(data).lower():
                    print_success("Response contains relevant information about SBA loans")
                else:
                    print_warning("Response does not appear to contain information about SBA loans")
            except json.JSONDecodeError:
                print_error("Failed to parse JSON response")
                print_info(f"Raw response: {response.text[:200]}...")
        else:
            print_error(f"Failed to send message: HTTP {response.status_code}")
            print_info(f"Response: {response.text[:100]}...")
            return False
    except requests.RequestException as e:
        print_error(f"Connection error during message send: {str(e)}")
        return False
    
    return True

def main():
    print_header("PocketProSBA Concierge Verification")
    
    successful_urls = []
    
    for base_url in URLS:
        if test_backend_connection(base_url):
            successful_urls.append(base_url)
    
    if not successful_urls:
        print_error("No backends are available. Make sure the backend server is running.")
        sys.exit(1)
    
    # Test concierge workflow on each available backend
    for base_url in successful_urls:
        test_concierge_workflow(base_url)
    
    print_header("Verification Complete")
    
    # Final summary
    print_info("Summary:")
    for base_url in URLS:
        if base_url in successful_urls:
            print_success(f"{base_url}: Available and functional")
        else:
            print_error(f"{base_url}: Not available")

if __name__ == "__main__":
    main()
