#!/bin/bash
# token_counter.sh - Track tokens streaming through WebSocket connection
# Reads from stdin (piped from websocket server) and counts tokens

SavingsFile="$HOME/.ai_cli_savings"
DbFile="$HOME/.ai_cli_db.db"

# Token pricing (Claude Fable 5: $10/1M in, $50/1M out)
INPUT_PRICE="0.0000100"
OUTPUT_PRICE="0.0000500"

echo "Token Counter started. Reading from stdin..."
echo "Token pricing (Claude Fable 5): Input $INPUT_PRICE USD/token, Output $OUTPUT_PRICE USD/token"

# Initialize counters
input_tokens=0
output_tokens=0
input_cost=0
output_cost=0

# Function to update database with current stats
update_database() {
    if [[ -f "$DbFile" ]]; then
        # Add to existing totals
        local db_input=$(sqlite3 "$DbFile" "SELECT COALESCE(SUM(input_tokens), 0) FROM usage_logs;")
        local db_output=$(sqlite3 "$DbFile" "SELECT COALESCE(SUM(output_tokens), 0) FROM usage_logs;")
        
        # Update totals
        sqlite3 "$DbFile" "UPDATE usage_logs SET input_tokens = input_tokens + $input_tokens, output_tokens = output_tokens + $output_tokens;"
        
        # Commit to database
        sqlite3 "$DbFile" "COMMIT;"
    fi
}

# Function to display current stats
display_stats() {
    local total_savings=$(awk "BEGIN {printf \"%.6f\", ($input_tokens * $INPUT_PRICE) + ($output_tokens * $OUTPUT_PRICE)}")
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📊 Token Stats:"
    echo "  Input Tokens:   $input_tokens"
    echo "  Output Tokens:  $output_tokens"
    echo "  Input Cost:     \$(scale=6; $input_tokens * $INPUT_PRICE) USD"
    echo "  Output Cost:    \$(scale=6; $output_tokens * $OUTPUT_PRICE) USD"
    echo "  Running Total:  \$(scale=6; $input_tokens * $INPUT_PRICE + $output_tokens * $OUTPUT_PRICE) USD"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Function to show savings summary
show_savings_summary() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "💰 Savings Summary:"
    
    # Get total from file if it exists
    local file_savings="0"
    if [[ -f "$SavingsFile" ]]; then
        file_savings=$(cat "$SavingsFile")
    fi
    
    echo "  Total from file:  \$${file_savings}"
    echo "  Current running:  \$(scale=6; $input_tokens * $INPUT_PRICE + $output_tokens * $OUTPUT_PRICE) USD"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Process each line from stdin
while IFS= read -r line || [[ -n "$line" ]]; do
    # Skip empty lines
    [[ -z "$line" ]] && continue
    
    # Try to parse JSON from WebSocket message
    if [[ "$line" =~ ^\{.*\}$ ]]; then
        # Extract tokens_in from the message
        if [[ "$line" =~ \"tokens_in\":[[:space:]]*([0-9]+|[0-9,]+) ]]; then
            # Remove commas and parse
            tokens_in="${BASH_REMATCH[1]}"
            tokens_in="${tokens_in//,/}"
            input_tokens=$((input_tokens + tokens_in))
            
            # Extract tokens_out
            if [[ "$line" =~ \"tokens_out\":[[:space:]]*([0-9]+|[0-9,]+) ]]; then
                tokens_out="${BASH_REMATCH[1]}"
                tokens_out="${tokens_out//,/}"
                output_tokens=$((output_tokens + tokens_out))
            fi
        fi
        
        # Calculate current cost
        local input_cost_raw=$(awk "BEGIN {printf \"%.6f\", $input_tokens * $INPUT_PRICE}")
        local output_cost_raw=$(awk "BEGIN {printf \"%.6f\", $output_tokens * $OUTPUT_PRICE}")
        local running_total_raw=$(awk "BEGIN {printf \"%.6f\", $input_tokens * $INPUT_PRICE + $output_tokens * $OUTPUT_PRICE}")
        
        # Round to 4 decimal places for display
        input_cost=$(awk "BEGIN {printf \"%.4f\", $input_cost_raw}")
        output_cost=$(awk "BEGIN {printf \"%.4f\", $output_cost_raw}")
        running_total=$(awk "BEGIN {printf \"%.4f\", $running_total_raw}")
        
        # Display update every 10 tokens or when tokens change significantly
        if (( input_tokens > 0 )) || (( output_tokens > 0 )); then
            if (( input_tokens % 10 == 0 )) || (( output_tokens % 10 == 0 )); then
                display_stats
                show_savings_summary
            fi
        fi
    fi
done < /dev/stdin

# Final display
display_stats
show_savings_summary
update_database
echo "Token counter finished. Database updated."
