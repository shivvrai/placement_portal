"""
Seed Assessment Question Bank script.
Seeds 75+ questions covering Python, SQL, React, Machine Learning, and Data Structures across all difficulty levels.
Checks for duplicates before inserting so it's safe to run multiple times.
"""

import asyncio
import os
import sys

# Ensure default dev SQLite database if DATABASE_URL is not set
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./ccip_dev.db")

# Ensure backend folder is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select, func
from app.core.database import AsyncSessionLocal, engine, Base
from app.models.assessment import AssessmentQuestionBank

QUESTIONS_DATA = [
    # ─── PYTHON ────────────────────────────────────────────────────────
    # Easy / Beginner
    {
        "topic": "Python",
        "difficulty": "easy",
        "question_text": "What is the output of print(type([]))?",
        "options": ["<class 'list'>", "<class 'tuple'>", "<class 'dict'>", "<class 'set'>"],
        "correct_answer": "<class 'list'>",
        "explanation": "[] defines an empty list in Python."
    },
    {
        "topic": "Python",
        "difficulty": "easy",
        "question_text": "Which keyword is used to define a function in Python?",
        "options": ["func", "def", "function", "define"],
        "correct_answer": "def",
        "explanation": "The 'def' keyword is used to create functions."
    },
    {
        "topic": "Python",
        "difficulty": "easy",
        "question_text": "How do you start writing a comment in Python?",
        "options": ["//", "#", "/*", "<!--"],
        "correct_answer": "#",
        "explanation": "Python uses # for single line comments."
    },
    {
        "topic": "Python",
        "difficulty": "easy",
        "question_text": "Which data type is immutable in Python?",
        "options": ["List", "Dictionary", "Set", "Tuple"],
        "correct_answer": "Tuple",
        "explanation": "Tuples cannot be modified after creation."
    },
    {
        "topic": "Python",
        "difficulty": "easy",
        "question_text": "What function is used to get the length of a string or list?",
        "options": ["count()", "size()", "len()", "length()"],
        "correct_answer": "len()",
        "explanation": "len() returns the number of items in an iterable."
    },
    
    # Medium / Intermediate
    {
        "topic": "Python",
        "difficulty": "medium",
        "question_text": "What is the output of list(range(0, 10, 3))?",
        "options": ["[0, 3, 6, 9]", "[0, 3, 6]", "[3, 6, 9]", "[0, 1, 2, 3]"],
        "correct_answer": "[0, 3, 6, 9]",
        "explanation": "range(start, stop, step) generates numbers from 0 up to 9 with step size 3."
    },
    {
        "topic": "Python",
        "difficulty": "medium",
        "question_text": "Which method removes and returns the last element of a list?",
        "options": ["remove()", "pop()", "delete()", "discard()"],
        "correct_answer": "pop()",
        "explanation": "pop() without arguments removes and returns the last item."
    },
    {
        "topic": "Python",
        "difficulty": "medium",
        "question_text": "What is the primary purpose of *args in a function definition?",
        "options": ["Pass keyword arguments", "Pass variable number of positional arguments", "Pass pointer reference", "Define default arguments"],
        "correct_answer": "Pass variable number of positional arguments",
        "explanation": "*args allows passing any number of non-keyword arguments as a tuple."
    },
    {
        "topic": "Python",
        "difficulty": "medium",
        "question_text": "What does the 'zip()' function do?",
        "options": ["Compresses files", "Pairs elements from multiple iterables", "Sorts a list in place", "Reverses a list"],
        "correct_answer": "Pairs elements from multiple iterables",
        "explanation": "zip() combines elements from matching positions of iterables into tuples."
    },
    {
        "topic": "Python",
        "difficulty": "medium",
        "question_text": "Which module in Python standard library provides deep copy capabilities?",
        "options": ["os", "sys", "copy", "clone"],
        "correct_answer": "copy",
        "explanation": "The copy module provides copy.deepcopy() for recursively cloning objects."
    },

    # Hard / Advanced
    {
        "topic": "Python",
        "difficulty": "hard",
        "question_text": "What is the output of [x**2 for x in range(5) if x % 2 != 0]?",
        "options": ["[1, 9]", "[0, 4, 16]", "[1, 4, 9]", "[1, 9, 25]"],
        "correct_answer": "[1, 9]",
        "explanation": "Odd numbers in range(5) are 1 and 3; their squares are 1 and 9."
    },
    {
        "topic": "Python",
        "difficulty": "hard",
        "question_text": "What is a GIL in Python CPython implementation?",
        "options": ["Global Interface Lock", "Global Interpreter Lock", "General Instruction Layer", "Garbage Identification Loop"],
        "correct_answer": "Global Interpreter Lock",
        "explanation": "GIL is a mutex that prevents multiple native threads from executing Python bytecode simultaneously."
    },
    {
        "topic": "Python",
        "difficulty": "hard",
        "question_text": "What does a generator function return when called?",
        "options": ["The final result value", "A generator iterator object", "A list of all yielded items", "None"],
        "correct_answer": "A generator iterator object",
        "explanation": "Calling a generator function returns a generator object without executing code until next() is called."
    },
    {
        "topic": "Python",
        "difficulty": "hard",
        "question_text": "Which method is called during object instantiation right after __new__?",
        "options": ["__construct__", "__init__", "__create__", "__prepare__"],
        "correct_answer": "__init__",
        "explanation": "__new__ creates the instance, and __init__ initializes instance attributes."
    },
    {
        "topic": "Python",
        "difficulty": "hard",
        "question_text": "What is the difference between staticmethod and classmethod in Python?",
        "options": ["classmethod receives the class 'cls' as first arg, staticmethod receives no implicit first arg", "staticmethod takes 'self', classmethod takes 'cls'", "No difference", "classmethod cannot modify class state"],
        "correct_answer": "classmethod receives the class 'cls' as first arg, staticmethod receives no implicit first arg",
        "explanation": "@classmethod receives the class object as the first parameter (cls)."
    },

    # ─── SQL ───────────────────────────────────────────────────────────
    # Easy / Beginner
    {
        "topic": "SQL",
        "difficulty": "easy",
        "question_text": "Which SQL clause is used to filter table rows before grouping?",
        "options": ["WHERE", "HAVING", "GROUP BY", "ORDER BY"],
        "correct_answer": "WHERE",
        "explanation": "WHERE filters rows prior to any aggregations."
    },
    {
        "topic": "SQL",
        "difficulty": "easy",
        "question_text": "Which SQL statement is used to insert new records into a table?",
        "options": ["INSERT INTO", "ADD ROW", "CREATE ROW", "UPDATE TABLE"],
        "correct_answer": "INSERT INTO",
        "explanation": "INSERT INTO table_name (cols) VALUES (...) inserts new records."
    },
    {
        "topic": "SQL",
        "difficulty": "easy",
        "question_text": "Which keyword is used to eliminate duplicate records in SQL SELECT?",
        "options": ["UNIQUE", "DISTINCT", "DIFFERENT", "SINGLE"],
        "correct_answer": "DISTINCT",
        "explanation": "SELECT DISTINCT removes duplicate rows from the query output."
    },
    {
        "topic": "SQL",
        "difficulty": "easy",
        "question_text": "Which function counts the total number of rows returned by a query?",
        "options": ["TOTAL()", "COUNT()", "SUM()", "NUMBER()"],
        "correct_answer": "COUNT()",
        "explanation": "COUNT(*) or COUNT(col) counts matching rows."
    },
    {
        "topic": "SQL",
        "difficulty": "easy",
        "question_text": "Which SQL keyword sorts the query result set?",
        "options": ["GROUP BY", "SORT BY", "ORDER BY", "ARRANGE BY"],
        "correct_answer": "ORDER BY",
        "explanation": "ORDER BY sorts the returned dataset in ASC or DESC order."
    },

    # Medium / Intermediate
    {
        "topic": "SQL",
        "difficulty": "medium",
        "question_text": "What does a LEFT JOIN return?",
        "options": ["All rows from left table + matched rows from right table", "Only matching rows between both tables", "All rows from right table", "Full Cartesian product"],
        "correct_answer": "All rows from left table + matched rows from right table",
        "explanation": "LEFT JOIN includes all rows from the left table regardless of matches in the right table."
    },
    {
        "topic": "SQL",
        "difficulty": "medium",
        "question_text": "Which SQL clause is used to filter groups formed by GROUP BY?",
        "options": ["WHERE", "HAVING", "FILTER", "LIMIT"],
        "correct_answer": "HAVING",
        "explanation": "HAVING filters aggregate values generated by GROUP BY."
    },
    {
        "topic": "SQL",
        "difficulty": "medium",
        "question_text": "Which aggregate function calculates the average value of a numeric column?",
        "options": ["AVG()", "MEAN()", "CALC_AVG()", "MEDIAN()"],
        "correct_answer": "AVG()",
        "explanation": "AVG() returns the mean average value of a numeric column."
    },
    {
        "topic": "SQL",
        "difficulty": "medium",
        "question_text": "What type of key uniquely identifies each record in a database table?",
        "options": ["Foreign Key", "Primary Key", "Composite Key", "Candidate Key"],
        "correct_answer": "Primary Key",
        "explanation": "A Primary Key enforces unique and non-null values for every table record."
    },
    {
        "topic": "SQL",
        "difficulty": "medium",
        "question_text": "Which operator is used to search for a specified pattern in a column?",
        "options": ["IN", "LIKE", "BETWEEN", "EXISTS"],
        "correct_answer": "LIKE",
        "explanation": "LIKE with wildcard symbols % or _ performs pattern matching."
    },

    # Hard / Advanced
    {
        "topic": "SQL",
        "difficulty": "hard",
        "question_text": "Which window function assigns ranks with gaps for tie scores?",
        "options": ["RANK()", "DENSE_RANK()", "ROW_NUMBER()", "NTILE()"],
        "correct_answer": "RANK()",
        "explanation": "RANK() skips rank numbers when ties occur, producing gaps."
    },
    {
        "topic": "SQL",
        "difficulty": "hard",
        "question_text": "What does CTE stand for in SQL?",
        "options": ["Common Table Expression", "Controlled Transaction Engine", "Central Table Extension", "Calculated Temporary Entity"],
        "correct_answer": "Common Table Expression",
        "explanation": "A CTE is defined using the WITH clause to create temporary result sets."
    },
    {
        "topic": "SQL",
        "difficulty": "hard",
        "question_text": "What is the key difference between UNION and UNION ALL?",
        "options": ["UNION removes duplicates while UNION ALL keeps duplicates", "UNION ALL is slower", "UNION joins columns horizontally", "UNION ALL is only for MySQL"],
        "correct_answer": "UNION removes duplicates while UNION ALL keeps duplicates",
        "explanation": "UNION performs duplicate removal overhead; UNION ALL returns all rows."
    },
    {
        "topic": "SQL",
        "difficulty": "hard",
        "question_text": "What isolation level prevents phantom reads in SQL database transactions?",
        "options": ["Read Uncommitted", "Read Committed", "Repeatable Read", "Serializable"],
        "correct_answer": "Serializable",
        "explanation": "Serializable isolation provides highest level of lock isolation preventing phantom reads."
    },
    {
        "topic": "SQL",
        "difficulty": "hard",
        "question_text": "Which window function fetches the value of a previous row in a partition?",
        "options": ["LAG()", "LEAD()", "FIRST_VALUE()", "NTH_VALUE()"],
        "correct_answer": "LAG()",
        "explanation": "LAG() allows accessing data from a previous row in the query result set."
    },

    # ─── REACT ─────────────────────────────────────────────────────────
    # Easy / Beginner
    {
        "topic": "React",
        "difficulty": "easy",
        "question_text": "Which React hook is used to handle component state?",
        "options": ["useState", "useEffect", "useContext", "useRef"],
        "correct_answer": "useState",
        "explanation": "useState allows functional components to manage local state."
    },
    {
        "topic": "React",
        "difficulty": "easy",
        "question_text": "What is JSX in React?",
        "options": ["A syntax extension for JavaScript", "A CSS framework", "A database engine", "A server template engine"],
        "correct_answer": "A syntax extension for JavaScript",
        "explanation": "JSX allows writing HTML-like code directly inside JavaScript files."
    },
    {
        "topic": "React",
        "difficulty": "easy",
        "question_text": "How do you pass data from a parent to a child component in React?",
        "options": ["State", "Props", "Context", "Redux"],
        "correct_answer": "Props",
        "explanation": "Props are passed downwards from parent to child components."
    },
    {
        "topic": "React",
        "difficulty": "easy",
        "question_text": "Which command is commonly used to create a new React Vite project?",
        "options": ["npm create vite@latest", "npm start react", "vite new app", "create-react-vite"],
        "correct_answer": "npm create vite@latest",
        "explanation": "npm create vite@latest is the standard tool to bootstrap modern React projects."
    },
    {
        "topic": "React",
        "difficulty": "easy",
        "question_text": "What attribute is used instead of 'class' for CSS styling in React JSX?",
        "options": ["className", "class", "styleClass", "cssClass"],
        "correct_answer": "className",
        "explanation": "className is used in JSX to avoid conflicting with the JavaScript reserved word 'class'."
    },

    # Medium / Intermediate
    {
        "topic": "React",
        "difficulty": "medium",
        "question_text": "When does useEffect with an empty dependency array [] run?",
        "options": ["Only once after initial mount", "On every render", "On component unmount only", "Never"],
        "correct_answer": "Only once after initial mount",
        "explanation": "An empty dependency array causes the effect to run only once after the first render."
    },
    {
        "topic": "React",
        "difficulty": "medium",
        "question_text": "Which hook is used to persist mutable values without causing re-renders?",
        "options": ["useRef", "useState", "useMemo", "useCallback"],
        "correct_answer": "useRef",
        "explanation": "useRef returns a mutable ref object whose .current property persists across renders without triggering a render."
    },
    {
        "topic": "React",
        "difficulty": "medium",
        "question_text": "Why should you assign a unique 'key' prop when rendering lists in React?",
        "options": ["Helps React identify which items have changed or been reordered", "Required by CSS grid", "Applies default styles to items", "Saves state in localStorage"],
        "correct_answer": "Helps React identify which items have changed or been reordered",
        "explanation": "Keys provide identity to elements in dynamic lists for efficient DOM diffing."
    },
    {
        "topic": "React",
        "difficulty": "medium",
        "question_text": "What is the purpose of useMemo hook?",
        "options": ["Memoize expensive computed values", "Cache HTTP requests", "Prevent component mounting", "Manage form state"],
        "correct_answer": "Memoize expensive computed values",
        "explanation": "useMemo caches the calculated value of a function between re-renders based on dependencies."
    },
    {
        "topic": "React",
        "difficulty": "medium",
        "question_text": "What hook should be used to memoize callback functions passed to child components?",
        "options": ["useCallback", "useMemo", "useRef", "useReducer"],
        "correct_answer": "useCallback",
        "explanation": "useCallback returns a memoized version of the callback that only changes when dependencies change."
    },

    # Hard / Advanced
    {
        "topic": "React",
        "difficulty": "hard",
        "question_text": "What is React Fiber?",
        "options": ["The core reconciliation engine architecture introduced in React 16", "A styling library for React", "A state management alternative to Redux", "A server rendering protocol"],
        "correct_answer": "The core reconciliation engine architecture introduced in React 16",
        "explanation": "Fiber enables incremental rendering and prioritization of updates."
    },
    {
        "topic": "React",
        "difficulty": "hard",
        "question_text": "What lifecycle method or hook technique handles rendering errors in child component trees?",
        "options": ["Error Boundaries (componentDidCatch / getDerivedStateFromError)", "useError hook", "try/catch block inside useEffect", "window.onerror"],
        "correct_answer": "Error Boundaries (componentDidCatch / getDerivedStateFromError)",
        "explanation": "Error boundaries are class components that catch JavaScript errors in child tree components."
    },
    {
        "topic": "React",
        "difficulty": "hard",
        "question_text": "What is the main benefit of React Server Components (RSC)?",
        "options": ["Executing component logic exclusively on the server to reduce bundle size", "Replacing client-side state management completely", "Enabling client-side SQL queries", "Bypassing virtual DOM rendering"],
        "correct_answer": "Executing component logic exclusively on the server to reduce bundle size",
        "explanation": "RSCs run on the server, zero client bundle weight for server-only dependencies."
    },
    {
        "topic": "React",
        "difficulty": "hard",
        "question_text": "How does React batch state updates in modern versions (React 18+)?",
        "options": ["Automatic batching groups all updates even inside promises and timeouts", "Manual batching via batch() function", "State updates are never batched", "Only event handlers are batched"],
        "correct_answer": "Automatic batching groups all updates even inside promises and timeouts",
        "explanation": "React 18 automatically batches state updates across async events, timeouts, and promises."
    },
    {
        "topic": "React",
        "difficulty": "hard",
        "question_text": "What hook handles complex state logic requiring multi-action dispatching?",
        "options": ["useReducer", "useState", "useContext", "useDeferredValue"],
        "correct_answer": "useReducer",
        "explanation": "useReducer is preferred for complex state logic involving multiple sub-values and actions."
    },

    # ─── MACHINE LEARNING ──────────────────────────────────────────────
    # Easy / Beginner
    {
        "topic": "Machine Learning",
        "difficulty": "easy",
        "question_text": "Which algorithm is commonly used for linear regression tasks?",
        "options": ["Ordinary Least Squares (OLS)", "K-Means", "Apriori", "DBSCAN"],
        "correct_answer": "Ordinary Least Squares (OLS)",
        "explanation": "OLS minimizes the sum of squared errors between predicted and actual values."
    },
    {
        "topic": "Machine Learning",
        "difficulty": "easy",
        "question_text": "What type of ML algorithm learns from labeled training data?",
        "options": ["Supervised Learning", "Unsupervised Learning", "Reinforcement Learning", "Self-Supervised Learning"],
        "correct_answer": "Supervised Learning",
        "explanation": "Supervised learning algorithms map inputs to known target labels."
    },
    {
        "topic": "Machine Learning",
        "difficulty": "easy",
        "question_text": "Which metric measures the fraction of correct predictions over total predictions?",
        "options": ["Accuracy", "Precision", "Recall", "F1-Score"],
        "correct_answer": "Accuracy",
        "explanation": "Accuracy = (True Positives + True Negatives) / Total Samples."
    },
    {
        "topic": "Machine Learning",
        "difficulty": "easy",
        "question_text": "What is overfitting in machine learning models?",
        "options": ["Model performs well on training data but poorly on unseen test data", "Model performs poorly on both training and test data", "Model takes too long to train", "Model requires too much memory"],
        "correct_answer": "Model performs well on training data but poorly on unseen test data",
        "explanation": "Overfitting occurs when a model learns noise in training data instead of general patterns."
    },
    {
        "topic": "Machine Learning",
        "difficulty": "easy",
        "question_text": "Which Python library is the standard choice for classical Machine Learning algorithms?",
        "options": ["scikit-learn", "Flask", "Django", "NumPy"],
        "correct_answer": "scikit-learn",
        "explanation": "scikit-learn offers classification, regression, clustering, and preprocessing tools."
    },

    # Medium / Intermediate
    {
        "topic": "Machine Learning",
        "difficulty": "medium",
        "question_text": "Why is Accuracy an unsuitable evaluation metric for highly imbalanced datasets?",
        "options": ["A trivial model predicting the majority class gets high accuracy despite missing minority class", "Accuracy calculation is computationally expensive", "Accuracy cannot be computed for multi-class tasks", "Accuracy can yield negative numbers"],
        "correct_answer": "A trivial model predicting the majority class gets high accuracy despite missing minority class",
        "explanation": "High accuracy on imbalanced data hides complete failure on the minority target class."
    },
    {
        "topic": "Machine Learning",
        "difficulty": "medium",
        "question_text": "What does F1-score represent in binary classification?",
        "options": ["Harmonic mean of Precision and Recall", "Arithmetic mean of Sensitivity and Specificity", "Geometric mean of Accuracy and Loss", "Difference between True Positives and False Positives"],
        "correct_answer": "Harmonic mean of Precision and Recall",
        "explanation": "F1-score = 2 * (Precision * Recall) / (Precision + Recall)."
    },
    {
        "topic": "Machine Learning",
        "difficulty": "medium",
        "question_text": "Which unsupervised technique is primarily used for dimensionality reduction?",
        "options": ["Principal Component Analysis (PCA)", "Random Forest", "Logistic Regression", "K-Nearest Neighbors"],
        "correct_answer": "Principal Component Analysis (PCA)",
        "explanation": "PCA projects data onto orthogonal principal components to reduce feature count while preserving variance."
    },
    {
        "topic": "Machine Learning",
        "difficulty": "medium",
        "question_text": "What technique splits data into K subsets to evaluate model generalization?",
        "options": ["K-Fold Cross-Validation", "K-Means Clustering", "Bootstrapping", "Grid Search"],
        "correct_answer": "K-Fold Cross-Validation",
        "explanation": "K-Fold cross-validation trains and tests model K times on rotated splits."
    },
    {
        "topic": "Machine Learning",
        "difficulty": "medium",
        "question_text": "What penalty does L1 regularization (Lasso) apply to model coefficients?",
        "options": ["Sum of absolute values of coefficients", "Sum of squared values of coefficients", "Log-likelihood of parameters", "Inverse of variance"],
        "correct_answer": "Sum of absolute values of coefficients",
        "explanation": "Lasso adds L1 penalty (sum of absolute weights) which forces uninformative weights to zero."
    },

    # Hard / Advanced
    {
        "topic": "Machine Learning",
        "difficulty": "hard",
        "question_text": "What causes the Vanishing Gradient problem in deep neural networks?",
        "options": ["Gradients shrink exponentially during backpropagation through many layers", "Learning rate is set too large", "Weights exceed floating point representation limits", "Loss function reaches negative values"],
        "correct_answer": "Gradients shrink exponentially during backpropagation through many layers",
        "explanation": "Multiplying small derivatives across many layers causes gradients to approach zero, preventing early layer learning."
    },
    {
        "topic": "Machine Learning",
        "difficulty": "hard",
        "question_text": "What key mechanism powers Transformer architectures (e.g. BERT, GPT)?",
        "options": ["Self-Attention mechanism", "Recurrent LSTM cells", "Convolutional pooling layers", "Markov Chain Monte Carlo"],
        "correct_answer": "Self-Attention mechanism",
        "explanation": "Self-attention computes dynamic weights between token representations across sequences in parallel."
    },
    {
        "topic": "Machine Learning",
        "difficulty": "hard",
        "question_text": "What is the Bias-Variance tradeoff?",
        "options": ["Balancing underfitting due to high bias with overfitting due to high variance", "Choosing between execution speed and GPU memory", "Selecting batch size vs learning rate", "Tradeoff between precision and recall"],
        "correct_answer": "Balancing underfitting due to high bias with overfitting due to high variance",
        "explanation": "Bias measures simplification error; variance measures sensitivity to training noise."
    },
    {
        "topic": "Machine Learning",
        "difficulty": "hard",
        "question_text": "Which ensemble algorithm builds sequential decision trees to correct previous tree errors?",
        "options": ["Gradient Boosting (e.g. XGBoost)", "Random Forest", "Bagging Classifier", "Extra Trees"],
        "correct_answer": "Gradient Boosting (e.g. XGBoost)",
        "explanation": "Boosting fits each subsequent tree to pseudo-residuals/errors of preceding trees."
    },
    {
        "topic": "Machine Learning",
        "difficulty": "hard",
        "question_text": "What loss function is standard for multi-class classification neural network output with Softmax?",
        "options": ["Categorical Cross-Entropy", "Mean Squared Error", "Binary Cross-Entropy", "Huber Loss"],
        "correct_answer": "Categorical Cross-Entropy",
        "explanation": "Categorical Cross-Entropy measures distance between predicted probability distributions and one-hot ground truth labels."
    },

    # ─── DATA STRUCTURES ──────────────────────────────────────────────
    # Easy / Beginner
    {
        "topic": "Data Structures",
        "difficulty": "easy",
        "question_text": "Which data structure operates on a Last In, First Out (LIFO) principle?",
        "options": ["Stack", "Queue", "Array", "Linked List"],
        "correct_answer": "Stack",
        "explanation": "Stack elements are pushed and popped from top in LIFO order."
    },
    {
        "topic": "Data Structures",
        "difficulty": "easy",
        "question_text": "Which data structure operates on a First In, First Out (FIFO) principle?",
        "options": ["Queue", "Stack", "Binary Tree", "Heap"],
        "correct_answer": "Queue",
        "explanation": "Queue processes elements in arrival order (FIFO)."
    },
    {
        "topic": "Data Structures",
        "difficulty": "easy",
        "question_text": "What is the time complexity of accessing an array element by index?",
        "options": ["O(1)", "O(n)", "O(log n)", "O(n^2)"],
        "correct_answer": "O(1)",
        "explanation": "Direct indexing calculates memory offset in O(1) constant time."
    },
    {
        "topic": "Data Structures",
        "difficulty": "easy",
        "question_text": "What does each node in a basic singly linked list contain?",
        "options": ["Data and a reference/pointer to next node", "Data only", "Data and two child pointers", "Memory address of array"],
        "correct_answer": "Data and a reference/pointer to next node",
        "explanation": "A singly linked list node holds payload value and pointer to next node."
    },
    {
        "topic": "Data Structures",
        "difficulty": "easy",
        "question_text": "Which searching algorithm requires the input array to be sorted?",
        "options": ["Binary Search", "Linear Search", "Depth-First Search", "Breadth-First Search"],
        "correct_answer": "Binary Search",
        "explanation": "Binary search halves search space based on element comparison, requiring sorted elements."
    },

    # Medium / Intermediate
    {
        "topic": "Data Structures",
        "difficulty": "medium",
        "question_text": "What is the average time complexity of searching key in a Hash Table?",
        "options": ["O(1)", "O(n)", "O(log n)", "O(n log n)"],
        "correct_answer": "O(1)",
        "explanation": "Hash functions map keys to bucket indices in O(1) average time."
    },
    {
        "topic": "Data Structures",
        "difficulty": "medium",
        "question_text": "What graph traversal algorithm uses a Queue data structure?",
        "options": ["Breadth-First Search (BFS)", "Depth-First Search (DFS)", "Dijkstra's Algorithm", "Kruskal's Algorithm"],
        "correct_answer": "Breadth-First Search (BFS)",
        "explanation": "BFS uses FIFO queue to explore graph level by level."
    },
    {
        "topic": "Data Structures",
        "difficulty": "medium",
        "question_text": "What property defines a Min-Heap binary tree?",
        "options": ["Parent node key is less than or equal to child node keys", "Left child key is always greater than right child key", "All leaf nodes are at different levels", "Tree must be balanced AVL tree"],
        "correct_answer": "Parent node key is less than or equal to child node keys",
        "explanation": "In a Min-Heap, root holds the minimum key in every subtree."
    },
    {
        "topic": "Data Structures",
        "difficulty": "medium",
        "question_text": "What is the worst-case time complexity of Quick Sort?",
        "options": ["O(n^2)", "O(n log n)", "O(n)", "O(log n)"],
        "correct_answer": "O(n^2)",
        "explanation": "Quick Sort degrades to O(n^2) when poor pivot selection occurs (e.g. sorted input)."
    },
    {
        "topic": "Data Structures",
        "difficulty": "medium",
        "question_text": "In a Binary Search Tree (BST), where are keys smaller than the root located?",
        "options": ["In the left subtree", "In the right subtree", "At leaf nodes only", "In root node"],
        "correct_answer": "In the left subtree",
        "explanation": "BST property dictates all keys in left subtree are smaller than root."
    },

    # Hard / Advanced
    {
        "topic": "Data Structures",
        "difficulty": "hard",
        "question_text": "What condition defines an AVL self-balancing tree for every node?",
        "options": ["Height difference between left and right subtrees is at most 1", "Total nodes must be prime number", "Root key is median of all keys", "Nodes must have exactly 2 children"],
        "correct_answer": "Height difference between left and right subtrees is at most 1",
        "explanation": "AVL balance factor = height(left) - height(right), constrained to {-1, 0, 1}."
    },
    {
        "topic": "Data Structures",
        "difficulty": "hard",
        "question_text": "What data structure is used in Dijkstra's algorithm to efficiently pick the next shortest vertex?",
        "options": ["Priority Queue (Min-Heap)", "Simple Array", "Stack", "Circular Queue"],
        "correct_answer": "Priority Queue (Min-Heap)",
        "explanation": "Min-Heap extracts minimum tentative distance vertex in O(log V) time."
    },
    {
        "topic": "Data Structures",
        "difficulty": "hard",
        "question_text": "What data structure implements Disjoint-Set Union (DSU) efficiently with path compression?",
        "options": ["Union-Find", "Trie", "Segment Tree", "Red-Black Tree"],
        "correct_answer": "Union-Find",
        "explanation": "Union-Find with path compression and rank heuristic achieves near O(1) amortized operations."
    },
    {
        "topic": "Data Structures",
        "difficulty": "hard",
        "question_text": "What is the time complexity of building a heap (Heapify) from an unordered array of n elements?",
        "options": ["O(n)", "O(n log n)", "O(n^2)", "O(log n)"],
        "correct_answer": "O(n)",
        "explanation": "Bottom-up build-heap algorithm processes array in O(n) linear time."
    },
    {
        "topic": "Data Structures",
        "difficulty": "hard",
        "question_text": "Which tree structure is optimized for prefix matching and autocomplete search?",
        "options": ["Trie (Prefix Tree)", "B-Tree", "Binary Heap", "Red-Black Tree"],
        "correct_answer": "Trie (Prefix Tree)",
        "explanation": "Trie stores characters along tree branches for O(k) key prefix lookups."
    }
]

# Duplicate questions for difficulty aliases ('beginner' -> 'easy', 'intermediate' -> 'medium', 'advanced' -> 'hard')
# to ensure 100% compatibility whether frontend asks for easy or beginner!
DIFFICULTY_ALIASES = {
    "easy": "beginner",
    "medium": "intermediate",
    "hard": "advanced",
}

async def seed():
    print("Connecting to database...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        seeded_count = 0
        skipped_count = 0

        # Build combined dataset with both difficulty naming schemes
        all_questions = []
        for q in QUESTIONS_DATA:
            all_questions.append(q)
            
            # Create alias record with beginner/intermediate/advanced
            alias_diff = DIFFICULTY_ALIASES.get(q["difficulty"])
            if alias_diff:
                q_alias = q.copy()
                q_alias["difficulty"] = alias_diff
                all_questions.append(q_alias)

        for q in all_questions:
            # Check if question already exists in DB to prevent duplicates
            query = select(AssessmentQuestionBank).where(
                func.lower(AssessmentQuestionBank.topic) == q["topic"].lower(),
                AssessmentQuestionBank.difficulty == q["difficulty"],
                AssessmentQuestionBank.question_text == q["question_text"],
            )
            res = await db.execute(query)
            existing = res.scalar_one_or_none()

            if existing:
                skipped_count += 1
                continue

            question = AssessmentQuestionBank(
                topic=q["topic"],
                difficulty=q["difficulty"],
                question_text=q["question_text"],
                options=q["options"],
                correct_answer=q["correct_answer"],
                explanation=q.get("explanation", ""),
                is_active=True,
                quality_status="reviewed",
            )
            db.add(question)
            seeded_count += 1

        await db.commit()
        print(f"✅ Seeding complete!")
        print(f"   Inserted: {seeded_count} new questions")
        print(f"   Skipped (already existing): {skipped_count}")

if __name__ == "__main__":
    asyncio.run(seed())
