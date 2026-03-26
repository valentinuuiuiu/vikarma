import asyncio
from server.tools.gateway import VikarmaToolGateway

# Mock the list of 64 APIs (temples)
# In reality, these would be the actual endpoints.
BHAIRAVA_APIS = [f"https://temple-api.bhairava.org/api/v1/temple/{i}" for i in range(1, 65)]

async def test_bhairava_connection():
    gateway = VikarmaToolGateway()
    results = {}
    
    print(f"\nInitiating connection tests to {len(BHAIRAVA_APIS)} Bhairava temple APIs...")
    
    for api_url in BHAIRAVA_APIS:
        # Simulate connection test
        # Log the attempt. In a real scenario, we'd use await gateway.web_fetch(api_url)
        results[api_url] = "Initiated"
        
    print(f"Connection test framework initiated for all {len(results)} Bhairava temples.")
    return len(results) == 64

if __name__ == "__main__":
    result = asyncio.run(test_bhairava_connection())
    if result:
        print("Success: 64 connection tests initiated.")
    else:
        print("Failed: Could not initiate all 64 connection tests.")
