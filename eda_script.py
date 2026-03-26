import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from collections import Counter
from tqdm import tqdm

# --- Configuration ---
# IMPORTANT: Replace this with the actual path to your structured log CSV from Phase 1.
STRUCTURED_DATA_PATH = 'BGL_structured.csv' 

def perform_statistical_eda(df: pd.DataFrame):
    """
    Performs statistical analysis: message length, temporal patterns, node stats.
    Uses Matplotlib for all visualizations.
    """
    print("\n--- 1. Statistical Analysis ---")
    
    # 1.1 Log Message Length Distribution
    df['message_length'] = df['Message'].astype(str).apply(len)
    
    print("1.1 Message Length Statistics:")
    print(df['message_length'].describe())
    
    plt.figure(figsize=(10, 5))
    # Cap the x-axis to the 99th percentile to better visualize the bulk of the data
    x_max = df['message_length'].quantile(0.99)
    
    # Use standard Matplotlib histogram
    plt.hist(df['message_length'], bins=50, edgecolor='black', alpha=0.7)
    
    plt.title('Distribution of Log Message Lengths (Characters)')
    plt.xlabel('Message Length')
    plt.ylabel('Frequency')
    plt.xlim(0, x_max) 
    plt.tight_layout()
    plt.show()
    # 

    # 1.2 Temporal Patterns (Logs by Hour)
    df['Hour'] = df['Timestamp'].dt.hour
    hourly_counts = df.groupby('Hour')['Message'].count()
    
    print("\n1.2 Hourly Log Volume:")
    print(hourly_counts)

    plt.figure(figsize=(12, 6))
    # Use standard Pandas/Matplotlib plot
    hourly_counts.plot(kind='bar', color='skyblue')
    plt.title('Log Volume by Hour of Day')
    plt.xlabel('Hour of Day (0-23)')
    plt.ylabel('Number of Logs')
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.show()
    # 

    # 1.3 Node-Level Statistics
    node_counts = df['NodeID'].value_counts()
    
    print("\n1.3 Top 10 Most Active Nodes (by Log Count):")
    top_10_nodes = node_counts.head(10)
    print(top_10_nodes)
    
    plt.figure(figsize=(12, 6))
    # Use standard Pandas/Matplotlib plot
    top_10_nodes.plot(kind='bar', color='lightcoral')
    plt.title('Top 10 Most Active Nodes')
    plt.xlabel('Node ID')
    plt.ylabel('Number of Logs')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()

def perform_text_analysis(file_path: str):
    """
    Performs streaming token counting to find frequent keywords, 
    efficiently handling large datasets without loading all text into a single string.
    """
    print("\n--- 2. Text Analysis (Streaming Keyword Frequency) ---")
    
    def simple_tokenizer(text):
        return str(text).lower().split()

    word_counter = Counter()
    CHUNK_SIZE = 100000 
    
    try:
        # We only need the 'Message' column for this analysis
        reader = pd.read_csv(file_path, usecols=['Message'], chunksize=CHUNK_SIZE)
        
        for i, chunk in enumerate(tqdm(reader, desc="Processing Log Chunks")):
            for message in chunk['Message']:
                tokens = simple_tokenizer(message)
                word_counter.update(tokens)
                
    except FileNotFoundError:
        print(f"❌ Error: Structured data file not found at {file_path}. Cannot perform text analysis.")
        return

    # Define stop words specific to system logs (can be expanded)
    common_stopwords = set(['the', 'to', 'a', 'in', 'and', 'at', 'with', 'for', 'of', 
                            'is', 'it', 'on', 'from', 'node', 'ce', 'sym', 'at', '0x', 
                            'info', 'kernel', 'ras', 'block', 'r', 'm', 'n', 'c', 'j', 'u', ''])

    # Filter out stopwords and single-character tokens
    filtered_counts = {
        word: count 
        for word, count in word_counter.items() 
        if word not in common_stopwords and len(word) > 1
    }

    # Find the 20 most frequent keywords
    top_keywords = Counter(filtered_counts).most_common(20)
    
    print("\nTop 20 Most Frequent Keywords (Excluding Common Stopwords):")
    for keyword, count in top_keywords:
        print(f"- {keyword}: {count}")

    # Visualization: Bar chart of top 20 keywords (using plt.barh)
    keywords, frequencies = zip(*top_keywords)
    
    plt.figure(figsize=(12, 8))
    # Plot horizontal bar chart
    plt.barh(keywords, frequencies, color='teal')
    plt.gca().invert_yaxis() # Display the most frequent keyword at the top
    
    plt.title('Top 20 Most Frequent Keywords in Log Messages')
    plt.xlabel('Frequency')
    plt.ylabel('Keyword')
    plt.tight_layout()
    plt.show()
    # 


def main():
    if not os.path.exists(STRUCTURED_DATA_PATH):
        print(f"FATAL ERROR: Structured log data not found at '{STRUCTURED_DATA_PATH}'.")
        print("Please ensure Phase 1 (Parsing) has run successfully and created this file.")
        return

    # Load the data once for statistical analysis
    try:
        print(f"Loading structured data for Statistical EDA from {STRUCTURED_DATA_PATH}...")
        # Use low_memory=False for large files to avoid mixed type guessing warnings
        df = pd.read_csv(STRUCTURED_DATA_PATH, parse_dates=['Timestamp'], low_memory=False)
        # Convert Unix timestamp 
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='s', errors='coerce') 
        
        perform_statistical_eda(df)
        
    except Exception as e:
        print(f"An error occurred during Statistical EDA (check column names): {e}")

    # Text analysis is done separately using streaming to conserve memory
    perform_text_analysis(STRUCTURED_DATA_PATH)

if __name__ == '__main__':
    main()