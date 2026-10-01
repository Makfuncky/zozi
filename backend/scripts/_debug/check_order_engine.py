# Fix order_engine.py - the outer try block at line 764 needs except/finally
# The issue is that the try block starting at line 764 (0-indexed: 763) 
# has no matching except/finally before line 873 `db.flush()` at same indent level
# Looking at the structure, the try block should end and except blocks should follow

with open('domains/orders/services/core/order_engine.py', 'r') as f:
    content = f.read()
    lines = content.split('\n')

# Find the try at line 764 (0-indexed: 763)
# The structure is:
# 764: try:
# 765-872: code inside try
# 873: db.flush()  <- this is at the same indent as try, meaning try block ended without except

# We need to find where the except blocks are and move them
# Looking at lines 931-943, there's a try/except for email that seems to be a separate block
# The except HTTPException and except Exception at lines 937-942 are orphaned

# The fix: the outer try at line 764 needs except blocks
# Looking at the code, the except clauses at 937-942 should be for the outer try
# But they're after a different try/except block (the email one at 931)

# Let's look at the actual structure more carefully
for i in range(763, 770):
    print(f'{i+1}: {repr(lines[i])}')
print('...')
for i in range(870, 880):
    print(f'{i+1}: {repr(lines[i])}')
