import sqlite3
from pathlib import Path

DB_PATH = Path(r"d:\zpeak\meeting-term-explainer\database\terms.db")

new_defs = {
    "Kafka": "Distributed event streaming platform used for real-time data pipelines and message processing.",
    "RabbitMQ": "Message broker that enables reliable communication between distributed applications.",
    "Django": "Python web framework for building secure and scalable web applications.",
    "S3": "AWS object storage service for storing and retrieving files at scale.",
    "EC2": "AWS virtual server service for running applications in the cloud.",
    "VPC": "Private virtual network for securely hosting AWS resources.",
    "IAM": "AWS service for managing user identities, permissions, and access control.",
    "Encryption": "Process of converting data into a secure format readable only with a key.",
    "MFA": "Security method requiring multiple forms of identity verification.",
    "A/B Testing": "Experiment comparing two versions to determine which performs better.",
    "CAC": "Customer Acquisition Cost, the average cost to gain a new customer.",
    "PaaS": "Cloud platform providing application development and deployment infrastructure.",
    "IaaS": "Cloud model providing virtualized computing resources over the internet."
}

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    report = []
    
    for term, new_def in new_defs.items():
        # Get before
        cursor.execute("SELECT definition FROM terms WHERE term=? COLLATE NOCASE", (term,))
        row = cursor.fetchone()
        old_def = row[0] if row else "NOT FOUND"
        
        # Update
        if row:
            cursor.execute("UPDATE terms SET definition=? WHERE term=? COLLATE NOCASE", (new_def, term))
        else:
            print(f"Warning: Term '{term}' not found in database.")
            
        report.append({
            "term": term,
            "before": old_def,
            "after": new_def
        })
        
    conn.commit()
    conn.close()
    
    with open("before_after_report.txt", "w", encoding="utf-8") as f:
        for r in report:
            f.write(f"Term: {r['term']}\n")
            f.write(f"Before: {r['before']}\n")
            f.write(f"After : {r['after']}\n")
            f.write("-" * 40 + "\n")
            
    print("Updates complete. Report saved to before_after_report.txt")

if __name__ == "__main__":
    main()
