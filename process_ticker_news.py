import ollama
import json
import time
import os
import re
import html

# Configuration
ticker = "micron-tech"  # Variable for ticker
model = 'finance-summarizer-qwen2.5:1.5b'
input_file = f"tickers\\{ticker}\\master_{ticker}_articles.jsonl"
output_file = f"tickers\\{ticker}\\processed_{ticker}_articles.jsonl"

def analyze_financial_content(content):    
    response = ollama.chat(model=model, messages=[
        {'role': 'user', 'content': content}
    ])
    
    return response['message']['content']

def parse_model_response(response_text):
    """Parse the model response which may contain markdown and HTML entities"""
    try:
        # Remove markdown code block formatting
        if '```json' in response_text:
            # Extract content between ```json and ```
            json_match = re.search(r'```json\s*\n(.*?)\n```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)
        
        # Decode HTML entities
        response_text = html.unescape(response_text)
        
        # Parse JSON
        analysis = json.loads(response_text)
        
        # Extract the required fields, handling different possible field names
        market_impact = analysis.get('market_impact', 'ERROR')
        sentiment = analysis.get('sentiment', 'neutral')
        confidence_score = analysis.get('confidence_score', 0.5)
        
        # Normalize values to expected format
        if isinstance(market_impact, str):
            market_impact = market_impact.lower()
        if isinstance(sentiment, str):
            sentiment = sentiment.lower()
        
        return {
            'market_impact': market_impact,
            'sentiment': sentiment,
            'confidence_score': float(confidence_score)
        }
        
    except Exception as e:
        print(f"Error parsing model response: {e}")
        print(f"Raw response: {response_text[:200]}...")
        return {
            'market_impact': 'ERROR',
            'sentiment': 'neutral',
            'confidence_score': 0.0
        }

def process_jsonl_file():
    """Process each row in the JSONL file"""
    processed_count = 0
    
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8') as outfile:
        
        for line in infile:
            try:
                # Parse the JSON line
                row = json.loads(line.strip())
                
                # Get content for analysis
                content_text = row.get('content', '')
                
                if content_text and content_text != 'PAID':
                    print(f"Processing row {processed_count + 1}: {row.get('title', 'No title')[:50]}...")
                    
                    # Get analysis from Ollama
                    analysis_result = analyze_financial_content(content_text)
                    
                    # Parse the model response
                    analysis = parse_model_response(analysis_result)
                    
                    # Add new fields to the row
                    row['market_impact'] = analysis['market_impact']
                    row['sentiment'] = analysis['sentiment']
                    row['confidence_score'] = analysis['confidence_score']
                
                else:
                    # For PAID content or empty content, set default values
                    row['market_impact'] = 'neutral'
                    row['sentiment'] = 'neutral'
                    row['confidence_score'] = 0.0
                
                # Write the updated row to output file
                outfile.write(json.dumps(row) + '\n')
                processed_count += 1
                
                # Small delay to avoid overwhelming the model
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error processing row {processed_count + 1}: {e}")
                continue
    
    print(f"Processing complete! {processed_count} rows processed.")
    print(f"Output saved to: {output_file}")

if __name__ == "__main__":
    start_time = time.time()
    process_jsonl_file()
    end_time = time.time()
    print(f"Total processing time: {end_time - start_time:.2f} seconds")