"""Seed 30 fixed MCQs per supported skill (10 easy, 10 medium, 10 hard).
The quiz is a starter bank intended to be reviewed and expanded by subject experts.
"""
from database import get_connection

SKILLS = ['Python','C++','C','Java','JavaScript','HTML','CSS','SQL','MySQL','Data Structures & Algorithms','Machine Learning','Data Analysis','Git & GitHub','Flask']

CORE = {
'EASY': [
('Which data structure stores unique values?', 'List', 'Set', 'Tuple', 'String', 'B'),
('Which structure follows FIFO order?', 'Stack', 'Queue', 'Tree', 'Graph', 'B'),
('What does an SQL SELECT statement do?', 'Deletes rows', 'Retrieves data', 'Creates users', 'Restarts server', 'B'),
('Which HTTP method is conventionally used to retrieve a resource?', 'GET', 'PATCH', 'DELETE', 'CONNECT', 'A'),
('What is a variable used for?', 'Store a value', 'Compile a browser', 'Encrypt a disk automatically', 'Create a network cable', 'A'),
('Which is a boolean value?', '"hello"', '42', 'True', '3.14', 'C'),
('What does an array generally store?', 'A sequence of elements', 'Only one fixed character', 'Only network packets', 'A database server', 'A'),
('What is a function?', 'A reusable block of code', 'A hardware port', 'A file extension', 'A database row only', 'A'),
('Which symbol commonly starts a single-line comment in Python?', '#', '<!--', '/*', '-->', 'A'),
('What does debugging mean?', 'Finding and fixing errors', 'Deleting source code', 'Compressing a video', 'Changing screen brightness', 'A')],
'MEDIUM': [
('What is the average lookup complexity of a hash table?', 'O(n) always', 'O(log n) always', 'O(1) average', 'O(n²)', 'C'),
('Why use a parameterized SQL query?', 'To style a page', 'To reduce SQL injection risk', 'To increase image size', 'To disable indexes', 'B'),
('What is the main purpose of a unit test?', 'Test a small unit of behavior', 'Deploy an app to every user', 'Replace documentation', 'Create a database backup', 'A'),
('What does recursion require to avoid infinite calls?', 'A base case', 'A CSS selector', 'A network socket', 'A foreign key only', 'A'),
('What is a primary key?', 'A unique row identifier', 'A duplicate column', 'A CSS property', 'A temporary variable', 'A'),
('Which complexity is typically better for large n?', 'O(n²)', 'O(2ⁿ)', 'O(n log n)', 'O(n!)', 'C'),
('What is an API?', 'A defined interface for software communication', 'A CPU cache', 'An image format', 'A password manager only', 'A'),
('What does a database transaction help provide?', 'Atomic grouped changes', 'Larger fonts', 'Faster monitor refresh', 'Automatic UI animations', 'A'),
('What is version control primarily for?', 'Track and manage code changes', 'Render 3D models', 'Manage battery temperature', 'Format hard drives', 'A'),
('Why validate user input on the server?', 'Client checks can be bypassed', 'Browsers cannot send text', 'It removes the need for databases', 'It guarantees zero bugs', 'A')],
'HARD': [
('Which technique reduces repeated overlapping recursive work?', 'Memoization', 'Busy waiting', 'Polling only', 'String padding', 'A'),
('What does ACID atomicity mean?', 'A transaction happens entirely or not at all', 'Every query is public', 'Tables have no keys', 'Data is always sorted', 'A'),
('What is a race condition?', 'Outcome depends on timing/interleaving', 'A syntax highlight theme', 'A compressed database', 'A deterministic sort', 'A'),
('What is the key benefit of a database index?', 'Can speed up lookups at storage/write cost', 'Always eliminates all disk use', 'Guarantees no duplicate data', 'Encrypts every column automatically', 'A'),
('What does least privilege mean?', 'Grant only permissions needed for a task', 'Give all users admin access', 'Disable authentication', 'Store passwords in plain text', 'A'),
('Which strategy can help avoid lost updates?', 'Optimistic locking/version checks', 'Removing all transactions', 'Using longer variable names', 'Disabling input validation', 'A'),
('What is idempotency in an API operation?', 'Repeating it has the same intended effect', 'It always creates a new record', 'It only works offline', 'It returns random output', 'A'),
('Why use a cryptographic password hash?', 'To avoid storing plaintext passwords', 'To make passwords reversible', 'To share passwords with clients', 'To remove account permissions', 'A'),
('What is a common mitigation for CSRF?', 'Anti-CSRF token and SameSite cookie protections', 'Disable TLS', 'Expose session secrets', 'Accept every origin', 'A'),
('What is a deadlock?', 'Tasks wait indefinitely on resources held by each other', 'A successful database backup', 'A fast query plan', 'A completed transaction', 'A')]
}
SPECIAL = {
'Python': {
'EASY': [('Which keyword defines a function in Python?','func','def','function','method','B'),('Which Python type is immutable?','list','dict','set','tuple','D'),('What does len([1,2,3]) return?','2','3','4','1','B'),('Which collection stores key-value pairs?','list','tuple','dict','set','C'),('Which literal represents no value?','null','None','void','undefined','B'),('Which keyword handles an exception?','catch','except','error','rescue','B'),('Which operator means exponentiation?','^','**','//','%%','B'),('Which method adds an item to a list?','append()','pushback()','insertEnd()','addLastOnly()','A'),('What does range(3) produce?','0,1,2','1,2,3','0,1,2,3','3 only','A'),('Which prefix marks a Python comment?','#','//','<!--','**','A')],
'MEDIUM': [('What is a list comprehension used for?','Build a list from an expression/iterable','Define a class only','Open a socket','Declare a database','A'),('What does enumerate(iterable) provide?','Index and item pairs','Only the last item','A sorted copy','A file handle','A'),('What is a decorator commonly used for?','Wrap or modify callable behavior','Create a loop','Declare an integer type','Install packages automatically','A'),('What does `with open(...)` help ensure?','Resource cleanup','Code is encrypted','File is always writable','File is compressed','A'),('Which statement creates a generator expression?','(x*x for x in nums)','[x*x] only','{x:x}','lambda x: return x','A'),('What is the purpose of __init__?','Initialize a new instance','Destroy the interpreter','Import modules','Catch every exception','A'),('What does dict.get(key, default) do?','Returns value or default if absent','Always deletes key','Sorts the dictionary','Raises for every missing key','A'),('What does `is` test?','Object identity','Value equality in all cases','Membership','Ordering','A'),('Which module supports regular expressions?','re','regexlib','pattern','textmatch','A'),('What does a virtual environment isolate?','Project Python dependencies','CPU hardware','Git history','Browser tabs','A')],
'HARD': [('Why can a mutable default argument be dangerous?','It is reused across calls','It is copied automatically every call','It disables type checking','It makes recursion impossible','A'),('What does the GIL affect in standard CPython?','Parallel execution of Python bytecode threads','Database schemas','HTML rendering','Network routing only','A'),('What is a descriptor in Python?','Object defining attribute access methods','A package manager','A loop keyword','A JSON file','A'),('What does asyncio primarily support?','Cooperative asynchronous I/O','Automatic GPU compilation','Only multiprocessing','Static HTML validation','A'),('What is method resolution order (MRO)?','Order used to search base classes for attributes','Order of list sorting','Order of import downloads','A database index','A'),('What does `yield from` do?','Delegates iteration to a sub-iterator','Raises every exception','Copies a generator to a list','Creates a thread','A'),('What is a closure?','Function retaining access to enclosing scope','A closed file only','A class without methods','A compiled binary','A'),('Why use `functools.wraps` in a decorator?','Preserve wrapped function metadata','Make the function asynchronous','Cache all results','Prevent exceptions','A'),('What does a context manager implement?','Resource setup and cleanup protocol','Only string formatting','Database normalization','Memory allocation exclusively','A'),('What is the primary risk of untrusted pickle data?','Deserialization can execute arbitrary code','It always loses Unicode','It cannot store numbers','It only supports images','A')]},
'SQL': {
'EASY': [('Which clause filters rows?','WHERE','ORDER BY','GROUP BY','JOIN','A'),('Which function counts rows?','SUM()','COUNT()','TOTALROWS()','SIZE()','B'),('Which command adds a row?','INSERT','ALTER','DROP','GRANT','A'),('Which clause sorts results?','SORT','ORDER BY','ARRANGE','RANK ONLY','B'),('Which keyword removes duplicate result rows?','UNIQUE','DISTINCT','SINGLE','FILTER','B'),('Which aggregate calculates a mean?','AVG()','MID()','MEANROW()','AVERAGE ROW','A'),('Which clause groups rows for aggregates?','GROUP BY','ORDER BY','WHERE','LIMIT','A'),('Which command changes existing rows?','UPDATE','CREATE','SELECT','DESCRIBE','A'),('Which condition matches a range?','BETWEEN','RANGEONLY','INRANGE','WITHIN','A'),('Which wildcard matches any sequence in LIKE?','%','*','?','&','A')],
'MEDIUM': [('What does INNER JOIN return?','Rows with matching join keys in both inputs','All rows from left always','All rows from right always','Only unmatched rows','A'),('What is a foreign key for?','Enforce relationship to referenced rows','Encrypt the table','Sort all columns','Make every value unique automatically','A'),('Which clause filters groups after aggregation?','HAVING','WHERE','FROM','LIMIT','A'),('What does COALESCE return?','First non-NULL argument','Last row','Count of NULLs','A random value','A'),('What does a correlated subquery reference?','A column from the outer query','Only constants','No tables','Only indexes','A'),('Why use a transaction?','Group operations into a controlled unit','Format SQL keywords','Create UI components','Automatically remove all duplicates','A'),('What does LEFT JOIN preserve?','All left-side rows','Only right-side rows','Only exact matches','Only unmatched right rows','A'),('What does COUNT(column) ignore?','NULL values','Zero values','Negative values','Duplicate non-NULL values','A'),('What is normalization intended to reduce?','Redundancy and update anomalies','Query syntax','Column types','Access control','A'),('What does LIMIT do in common SQL dialects?','Restricts returned row count','Restricts column width','Locks a table permanently','Adds a constraint','A')],
'HARD': [('What is a phantom read?','A repeated predicate query sees newly matching rows','A query returns a syntax error','A table loses its primary key','A server changes timezone','A'),('What is the purpose of a composite index?','Index multiple columns in defined order','Encrypt several columns','Join tables automatically','Prevent all table scans in every query','A'),('Why can applying a function to an indexed column hurt performance?','It may prevent use of a simple index lookup','It always improves selectivity','It removes NULL values','It guarantees a covering index','A'),('What does SERIALIZABLE isolation aim to provide?','Behavior equivalent to serial transaction execution','No transaction logging','Unlimited concurrent writes without coordination','Read-only access only','A'),('What is a window function useful for?','Calculations across related rows without collapsing them','Dropping a window/table','Replacing every JOIN','Creating a database user','A'),('What does EXPLAIN commonly show?','Query execution plan','Table data export','User password hash','Database backup content','A'),('What is a deadlock in a database?','Transactions wait on resources held by one another','A query with no WHERE clause','A missing index only','A full disk only','A'),('Why should dynamic SQL values be parameterized?','Prevent injection and separate data from query syntax','Make all queries public','Avoid transactions','Guarantee all queries use indexes','A'),('What is a covering index?','An index containing all columns needed by a query','An index encrypted with TLS','An index on every table by default','A temporary view','A'),('What does a common table expression (CTE) define?','A named query expression for a statement','A permanent table always','A database login','A trigger only','A')]} }

def questions_for(skill, level):
    custom = SPECIAL.get(skill, {}).get(level)
    base = CORE[level]
    if custom:
        return custom
    out = []
    for q, a, b, c, d, correct in base:
        out.append((q.replace('What is', f'In {skill}, what is').replace('Which', f'For {skill}, which', 1), a, b, c, d, correct))
    return out

def seed():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            for skill in SKILLS:
                cur.execute('SELECT id FROM skills WHERE name = %s', (skill,))
                row = cur.fetchone()
                if row:
                    skill_id = row['id']
                else:
                    cur.execute('INSERT INTO skills(name) VALUES(%s)', (skill,))
                    skill_id = cur.lastrowid
                
                cur.execute('SELECT COUNT(*) AS n FROM assessment_questions WHERE skill_id=%s AND active=1', (skill_id,))
                if int(cur.fetchone()['n'] or 0) >= 30:
                    continue
                
                for level in ('EASY', 'MEDIUM', 'HARD'):
                    cur.execute('SELECT COUNT(*) AS n FROM assessment_questions WHERE skill_id=%s AND active=1 AND difficulty=%s', (skill_id, level))
                    count = int(cur.fetchone()['n'] or 0)
                    for question, a, b, c, d, answer in questions_for(skill, level)[count:10]:
                        marks = {'EASY': 3, 'MEDIUM': 5, 'HARD': 7}[level]
                        cur.execute(
                            'INSERT INTO assessment_questions(skill_id, question_text, option_a, option_b, option_c, option_d, correct_option, marks, difficulty, active) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, 1)',
                            (skill_id, question, a, b, c, d, answer, marks, level)
                        )
        conn.commit()
        print('Seeded assessment bank: 30 questions per supported skill (10 each easy/medium/hard).')
    finally:
        conn.close()

if __name__ == '__main__':
    seed()
