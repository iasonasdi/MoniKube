#!/usr/bin/env python3
"""
Neo4J Database Cleanup Utility
Clears all nodes and relationships from the Neo4J database.
"""

import sys
import logging
from typing import Optional

try:
    from neo4j import GraphDatabase
    from neo4j.exceptions import ServiceUnavailable, AuthError
except ImportError:
    print("Neo4J driver not installed. Install with: pip install neo4j")
    sys.exit(1)


def clear_database(uri: str = "bolt://localhost:7687", 
                  username: str = "neo4j", 
                  password: str = "password",
                  database: str = "neo4j",
                  confirm: bool = False) -> bool:
    """
    Clear all nodes and relationships from Neo4J database.
    
    Args:
        uri: Neo4J database URI
        username: Database username
        password: Database password
        database: Database name
        confirm: If False, will prompt for confirmation
        
    Returns:
        bool: Success status
    """
    if not confirm:
        print("⚠️  WARNING: This will DELETE ALL data from Neo4J!")
        print(f"   Database: {database} at {uri}")
        response = input("   Are you sure you want to continue? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("❌ Operation cancelled.")
            return False
    
    try:
        driver = GraphDatabase.driver(uri, auth=(username, password), database=database)
        
        with driver.session() as session:
            # Get count before deletion
            result = session.run("MATCH (n) RETURN count(n) as count")
            count_before = result.single()['count']
            
            print(f"📊 Found {count_before} nodes in database")
            
            if count_before == 0:
                print("✅ Database is already empty.")
                driver.close()
                return True
            
            print("🗑️  Deleting all nodes and relationships...")
            
            # Delete all relationships first, then nodes
            # This is more efficient than MATCH (n) DETACH DELETE n
            session.run("MATCH ()-[r]-() DELETE r")
            session.run("MATCH (n) DELETE n")
            
            # Verify deletion
            result = session.run("MATCH (n) RETURN count(n) as count")
            count_after = result.single()['count']
            
            if count_after == 0:
                print(f"✅ Successfully deleted {count_before} nodes and all relationships!")
                print("✅ Database is now empty and ready for fresh data.")
            else:
                print(f"⚠️  Warning: {count_after} nodes still remain (this shouldn't happen)")
            
        driver.close()
        return True
        
    except ServiceUnavailable as e:
        print(f"❌ Neo4J service unavailable: {e}")
        print("   Make sure Neo4J is running.")
        return False
    except AuthError as e:
        print(f"❌ Neo4J authentication failed: {e}")
        print("   Check your username and password.")
        return False
    except Exception as e:
        print(f"❌ Error clearing database: {e}")
        return False


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Clear all data from Neo4J database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Clear with confirmation prompt
  python3 clear_database.py
  
  # Clear without confirmation (use with caution!)
  python3 clear_database.py --yes
  
  # Clear with custom connection
  python3 clear_database.py --uri bolt://localhost:7687 --username neo4j --password mypass
        """
    )
    
    parser.add_argument('--uri', default='bolt://localhost:7687',
                       help='Neo4J database URI (default: bolt://localhost:7687)')
    parser.add_argument('--username', default='neo4j',
                       help='Database username (default: neo4j)')
    parser.add_argument('--password', default='password',
                       help='Database password (default: password)')
    parser.add_argument('--database', default='neo4j',
                       help='Database name (default: neo4j)')
    parser.add_argument('--yes', '-y', action='store_true',
                       help='Skip confirmation prompt')
    
    args = parser.parse_args()
    
    print("🧹 Neo4J Database Cleanup Utility")
    print("=" * 50)
    print()
    
    success = clear_database(
        uri=args.uri,
        username=args.username,
        password=args.password,
        database=args.database,
        confirm=args.yes
    )
    
    if success:
        print()
        print("💡 Next steps:")
        print("   1. Run your monitoring script to populate fresh data")
        print("   2. The new schema (ComputeNode, namespace, etc.) will be created automatically")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()

