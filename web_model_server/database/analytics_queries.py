# Copyright (C) 2024 RidgeRun, LLC (http://www.ridgerun.com)
# All Rights Reserved.

# The contents of this software are proprietary and confidential to RidgeRun,
# LLC.  No part of this program may be photocopied, reproduced or translated
# into another programming language without prior written consent of
# RidgeRun, LLC.  The user is free to modify the source code after obtaining
# a software license from RidgeRun.  All source code changes must be provided
# back to RidgeRun without any encumbrance.

import sqlite3

conn = sqlite3.connect('analytics.db')
c = conn.cursor()

def total_requests():
    c.execute('SELECT COUNT(*) FROM requests')
    result = c.fetchone()
    return result[0]

def requests_by_function():
    c.execute('SELECT function, COUNT(*) FROM requests GROUP BY function')
    results = c.fetchall()
    return results

def requests_by_email():
    c.execute('SELECT email, COUNT(*) FROM requests GROUP BY email')
    results = c.fetchall()
    return results

print("Total requests:", total_requests(), "\n")

print("Total requests X Function:")
for function, count in requests_by_function():
    print(f"{function}: {count}")

print("\nTotal requests X Email:")
for email, count in requests_by_email():
    print(f"{email}: {count}")

conn.close()
