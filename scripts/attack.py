import sys
import os
import argparse
import sqlite3
from datetime import datetime

# Allow importing core package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.database import get_db_connection

DB_B_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/site_b.db'))

def execute_attack(args):
    if not os.path.exists(DB_B_PATH):
        print(f"[x] ERROR: Site B database not found at {DB_B_PATH}. Please run generator first.")
        sys.exit(1)

    conn = get_db_connection(DB_B_PATH)
    cursor = conn.cursor()
    
    attack_type = args.type.lower()
    tx_id = args.transaction_id
    
    try:
        if attack_type == 'update':
            if not tx_id or args.amount is None:
                print("[x] ERROR: --transaction-id and --amount are required for 'update' attack.")
                sys.exit(1)
                
            # Check if exists
            cursor.execute("SELECT Amount FROM Banking_Transactions WHERE TransactionID = ?", (tx_id,))
            row = cursor.fetchone()
            if not row:
                print(f"[x] ERROR: Transaction {tx_id} not found in Site B database.")
                sys.exit(1)
                
            orig_amount = row['Amount']
            cursor.execute("UPDATE Banking_Transactions SET Amount = ? WHERE TransactionID = ?", (args.amount, tx_id))
            conn.commit()
            print(f"[+] ATTACK SUCCESS (Site B modified directly via SQL):")
            print(f"  Transaction ID: {tx_id}")
            print(f"  Original Amount: ${orig_amount:.2f}")
            print(f"  Tampered Amount: ${args.amount:.2f}")
            
        elif attack_type == 'delete':
            if not tx_id:
                print("[x] ERROR: --transaction-id is required for 'delete' attack.")
                sys.exit(1)
                
            # Check if exists
            cursor.execute("SELECT * FROM Banking_Transactions WHERE TransactionID = ?", (tx_id,))
            row = cursor.fetchone()
            if not row:
                print(f"[x] ERROR: Transaction {tx_id} not found in Site B database.")
                sys.exit(1)
                
            cursor.execute("DELETE FROM Banking_Transactions WHERE TransactionID = ?", (tx_id,))
            conn.commit()
            print(f"[+] ATTACK SUCCESS (Site B modified directly via SQL):")
            print(f"  Transaction ID {tx_id} has been deleted.")
            
        elif attack_type == 'insert':
            new_tx_id = tx_id or "TX-FAKE"
            from_acc = "ACC999"
            to_acc = "ACC888"
            amount = args.amount if args.amount is not None else 5000.00
            block_id = args.block if args.block is not None else 1
            timestamp = datetime.now().isoformat()
            
            cursor.execute('''
                INSERT INTO Banking_Transactions (TransactionID, From_Account, To_Account, Amount, Timestamp, BlockID)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (new_tx_id, from_acc, to_acc, amount, timestamp, block_id))
            conn.commit()
            print(f"[+] ATTACK SUCCESS (Site B modified directly via SQL):")
            print(f"  Injected Fake Transaction {new_tx_id} in Block {block_id}:")
            print(f"    From: {from_acc} | To: {to_acc} | Amount: ${amount:.2f}")
            
        else:
            print(f"[x] ERROR: Unknown attack type: {attack_type}. Choose 'update', 'delete', or 'insert'.")
            sys.exit(1)
            
    except Exception as e:
        print(f"[x] Database error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Simulate Rogue DBA Attack on Site B Database")
    parser.add_argument("--type", required=True, choices=["update", "delete", "insert"], help="Attack type")
    parser.add_argument("--transaction-id", help="Target transaction ID")
    parser.add_argument("--amount", type=float, help="Amount value")
    parser.add_argument("--block", type=int, default=1, help="Block ID (for inserts)")
    
    args = parser.parse_args()
    execute_attack(args)
