with open('test_results.txt', 'rb') as f:
    text = f.read().decode('utf-16le', 'ignore').replace('\r', '')

with open('test_results_clean.txt', 'w', encoding='utf-8') as f:
    f.write(text)
