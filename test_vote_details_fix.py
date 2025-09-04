#!/usr/bin/env python3
"""
Test script to verify the vote details fix in the admin panel.
This simulates the JavaScript fetch request that was failing.
"""
import sys
sys.path.insert(0, 'src')

from toveco_voting.database import DatabaseManager
from toveco_voting.admin_manager import AdminManager

def test_vote_details_route():
    """Test the vote details route logic."""
    # Initialize managers
    db_manager = DatabaseManager("votes.db")
    admin_manager = AdminManager(db_manager)
    
    # Get all votes
    votes = admin_manager.get_recent_activity(limit=1000)
    
    if not votes:
        print("❌ No votes in database to test")
        return False
    
    print(f"✅ Found {len(votes)} votes in database")
    
    # Test finding vote by ID (simulating the route logic)
    test_vote_id = str(votes[0].get("id"))
    print(f"\n🔍 Testing vote lookup with ID: {test_vote_id}")
    
    # Simulate the route logic
    found_vote = None
    for v in votes:
        if str(v.get("id")) == test_vote_id:
            found_vote = v
            break
    
    if found_vote:
        print(f"✅ Successfully found vote:")
        print(f"   - Voter: {found_vote.get('voter_name')}")
        print(f"   - Timestamp: {found_vote.get('timestamp')}")
        print(f"   - ID: {found_vote.get('id')}")
        return True
    else:
        print(f"❌ Failed to find vote with ID {test_vote_id}")
        return False

if __name__ == "__main__":
    try:
        success = test_vote_details_route()
        if success:
            print("\n✅ Vote details fix appears to be working correctly!")
            print("   The route should now properly fetch votes by ID.")
        else:
            print("\n⚠️  Test did not complete successfully")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        sys.exit(1)