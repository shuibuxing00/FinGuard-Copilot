"""
Synthetic Data Generator module.
Creates realistic test data with anomaly patterns.
Synthetic data only - no real user information.
"""

import random
import pandas as pd
from datetime import datetime, timedelta
from typing import Tuple
from security.anonymizer import Anonymizer


def generate_synthetic_data(
    n_users: int = 10,
    n_transactions: int = 500,
    seed: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Generate synthetic datasets for compliance testing.
    
    Args:
        n_users: Number of synthetic users to create
        n_transactions: Number of synthetic transactions
        seed: Random seed for reproducibility
        
    Returns:
        Tuple of (users_df, transactions_df, devices_df)
    """
    random.seed(seed)
    anonymizer = Anonymizer()
    
    # Generate users
    users_df = _generate_users(n_users, anonymizer)
    
    # Generate transactions with anomalies
    transactions_df = _generate_transactions(n_users, n_transactions, users_df, anonymizer)
    
    # Generate devices
    devices_df = _generate_devices(n_users, users_df, anonymizer)
    
    return users_df, transactions_df, devices_df


def _generate_users(n_users: int, anonymizer: Anonymizer) -> pd.DataFrame:
    """
    Generate user profiles.
    
    Args:
        n_users: Number of users
        anonymizer: Anonymizer instance
        
    Returns:
        Users DataFrame
    """
    users = []
    
    for i in range(n_users):
        raw_id = f"USER_{i:05d}"
        pseudonym = anonymizer.pseudonymize(raw_id)
        
        account_type = random.choice(['checking', 'savings', 'business'])
        risk_profile = random.choice(['low', 'medium', 'high'])
        
        user = {
            'user_id': pseudonym,
            'account_type': account_type,
            'risk_profile': risk_profile,
            'account_age_days': random.randint(30, 3650),
            'total_transactions': random.randint(10, 500),
            'verification_status': random.choice(['verified', 'unverified']),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        users.append(user)
    
    return pd.DataFrame(users)


def _generate_transactions(
    n_users: int,
    n_transactions: int,
    users_df: pd.DataFrame,
    anonymizer: Anonymizer
) -> pd.DataFrame:
    """
    Generate transactions with realistic anomaly patterns.
    
    Args:
        n_users: Number of users
        n_transactions: Number of transactions
        users_df: Users DataFrame
        anonymizer: Anonymizer instance
        
    Returns:
        Transactions DataFrame
    """
    transactions = []
    
    user_ids = users_df['user_id'].tolist()
    base_time = datetime.utcnow()
    
    for i in range(n_transactions):
        user_id = random.choice(user_ids)
        recipient_id = random.choice(user_ids)
        
        # Generate transaction with patterns
        anomaly_type = None
        risk_score = 20  # Base risk
        
        # Large amount anomaly (10% chance)
        if random.random() < 0.10:
            amount = random.uniform(10000, 50000)
            anomaly_type = 'large_amount'
            risk_score += 40
        # Normal amount
        else:
            amount = random.uniform(50, 5000)
        
        # Time anomaly - overnight transactions (5% chance)
        if random.random() < 0.05:
            hour = random.randint(0, 5)
            anomaly_type = 'time_anomaly'
            risk_score += 30
        else:
            hour = random.randint(8, 22)
        
        # Rapid transfers pattern
        if random.random() < 0.08:
            if anomaly_type:
                anomaly_type = 'rapid_transfers'
            amount = random.uniform(5000, 15000)
            risk_score += 35
        
        timestamp = base_time - timedelta(days=random.randint(0, 30), hours=hour)
        
        transaction = {
            'transaction_id': f"TXN_{i:06d}",
            'user_id': user_id,
            'recipient_id': recipient_id,
            'amount': amount,
            'timestamp': timestamp.isoformat(),
            'transaction_type': random.choice(['transfer', 'withdrawal', 'deposit']),
            'status': random.choice(['completed', 'pending']),
            'anomaly_type': anomaly_type or '',
            'risk_score': min(risk_score, 100),
            'violation_flags': _generate_violation_flags(anomaly_type)
        }
        
        transactions.append(transaction)
    
    return pd.DataFrame(transactions)


def _generate_violation_flags(anomaly_type: str) -> str:
    """
    Generate compliance violation flags based on anomaly type.
    
    Args:
        anomaly_type: Type of anomaly
        
    Returns:
        Comma-separated violation flags
    """
    flags = []
    
    if anomaly_type == 'large_amount':
        flags.append('LARGE_TRANSACTION_THRESHOLD')
    elif anomaly_type == 'time_anomaly':
        flags.append('UNUSUAL_TIMING')
    elif anomaly_type == 'rapid_transfers':
        flags.extend(['RAPID_MOVEMENT', 'POTENTIAL_SPLITTING'])
    
    # Random additional flags
    if random.random() < 0.15:
        flags.append('NEW_RECIPIENT')
    
    return ', '.join(flags) if flags else ''


def _generate_devices(
    n_users: int,
    users_df: pd.DataFrame,
    anonymizer: Anonymizer
) -> pd.DataFrame:
    """
    Generate device access history.
    
    Args:
        n_users: Number of users
        users_df: Users DataFrame
        anonymizer: Anonymizer instance
        
    Returns:
        Devices DataFrame
    """
    devices = []
    
    device_types = ['iPhone', 'Android', 'Windows', 'macOS']
    locations = ['New York, NY', 'Los Angeles, CA', 'London, UK', 'Singapore', 'Unknown']
    
    for user_id in users_df['user_id'].tolist():
        # Each user has 1-3 devices
        n_devices = random.randint(1, 3)
        
        for d in range(n_devices):
            # Anomalous device (high-risk)
            is_anomalous = random.random() < 0.15
            
            device = {
                'user_id': user_id,
                'device_id': f"DEV_{user_id[:8]}_{d}",
                'device_type': random.choice(device_types),
                'location': random.choice(locations) if not is_anomalous else 'Unknown',
                'last_login': (
                    datetime.utcnow() - timedelta(hours=random.randint(1, 720))
                ).isoformat(),
                'is_new': is_anomalous,
                'ip_address': '.'.join([str(random.randint(0, 255)) for _ in range(4)])
            }
            
            devices.append(device)
    
    return pd.DataFrame(devices)


def generate_and_save(
    output_dir: str = 'data',
    n_users: int = 10,
    n_transactions: int = 500
) -> None:
    """
    Generate and save synthetic datasets to CSV files.
    
    Args:
        output_dir: Output directory for CSV files
        n_users: Number of users
        n_transactions: Number of transactions
    """
    import os
    
    try:
        # Create directory if needed
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"Generating {n_users} users and {n_transactions} transactions...")
        
        users_df, transactions_df, devices_df = generate_synthetic_data(
            n_users=n_users,
            n_transactions=n_transactions
        )
        
        # Save to CSV
        users_path = os.path.join(output_dir, 'users.csv')
        transactions_path = os.path.join(output_dir, 'transactions.csv')
        devices_path = os.path.join(output_dir, 'devices.csv')
        
        users_df.to_csv(users_path, index=False)
        transactions_df.to_csv(transactions_path, index=False)
        devices_df.to_csv(devices_path, index=False)
        
        print(f"✓ Saved {len(users_df)} users to {users_path}")
        print(f"✓ Saved {len(transactions_df)} transactions to {transactions_path}")
        print(f"✓ Saved {len(devices_df)} devices to {devices_path}")
        print("\nSynthetic data only - no real user information")
    
    except Exception as e:
        print(f"Error generating data: {e}")


if __name__ == '__main__':
    generate_and_save()
