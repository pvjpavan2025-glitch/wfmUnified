#!/usr/bin/env python3
"""
Script to generate a proper bcrypt hash for testing
"""
from passlib.hash import bcrypt

password = "test123"
hash_value = bcrypt.hash(password)
print(f"Password: {password}")
print(f"Hash: {hash_value}")
print(f"Verify: {bcrypt.verify(password, hash_value)}")
