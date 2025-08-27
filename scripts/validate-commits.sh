#!/bin/bash
# Validate commit messages for Conventional Commits compliance
#
# Usage: ./scripts/validate-commits.sh [number_of_commits]
#
# This script validates recent commit messages against:
# - Conventional Commits format
# - English language requirement
# - Project-specific standards

set -e

# Color output settings
RED='\033[0;31m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Number of commits to check (default: 10)
NUM_COMMITS=${1:-10}

# Result counters
TOTAL_COMMITS=0
VALID_COMMITS=0
INVALID_COMMITS=0
WARNINGS=0

echo "======================================================"
echo "📋 Commit Message Validation for QuantForge"
echo "======================================================"
echo ""
echo "Checking last $NUM_COMMITS commits for compliance..."
echo ""

# Temporary file for processing
TEMP_FILE=$(mktemp)
trap "rm -f $TEMP_FILE" EXIT

# Valid commit types
VALID_TYPES="feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert"

# Function to validate a single commit
validate_commit() {
    local commit_hash=$1
    local commit_subject=$2
    local commit_body=$3
    local is_valid=true
    local warnings=""
    
    echo -e "${BLUE}Commit:${NC} $commit_hash"
    echo "Subject: $commit_subject"
    
    # Check Conventional Commits format
    if echo "$commit_subject" | grep -qE "^($VALID_TYPES)(\(.+\))?: .+"; then
        echo -e "  ${GREEN}✓${NC} Format: Conventional Commits compliant"
    else
        echo -e "  ${RED}✗${NC} Format: Does not match Conventional Commits format"
        echo "    Expected: <type>(<scope>): <subject>"
        echo "    Valid types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert"
        is_valid=false
    fi
    
    # Extract type and scope if format is valid
    if echo "$commit_subject" | grep -qE "^($VALID_TYPES)"; then
        local commit_type=$(echo "$commit_subject" | sed -E "s/^([a-z]+).*/\1/")
        local has_scope=$(echo "$commit_subject" | grep -q "^[a-z]\+(" && echo "yes" || echo "no")
        
        if [ "$has_scope" = "yes" ]; then
            local scope=$(echo "$commit_subject" | sed -E "s/^[a-z]+\(([^)]+)\).*/\1/")
            echo "  Type: $commit_type, Scope: $scope"
        else
            echo "  Type: $commit_type, Scope: none"
        fi
    fi
    
    # Check subject line length (50 chars recommended)
    local subject_length=${#commit_subject}
    if [ $subject_length -le 50 ]; then
        echo -e "  ${GREEN}✓${NC} Length: $subject_length chars (≤50)"
    elif [ $subject_length -le 72 ]; then
        echo -e "  ${YELLOW}⚠${NC}  Length: $subject_length chars (>50, ≤72)"
        warnings="$warnings\n    - Subject line longer than recommended 50 chars"
        WARNINGS=$((WARNINGS + 1))
    else
        echo -e "  ${RED}✗${NC} Length: $subject_length chars (>72)"
        is_valid=false
    fi
    
    # Check for English (basic check - no non-ASCII in subject)
    if echo "$commit_subject" | grep -qP "[^\x00-\x7F]"; then
        echo -e "  ${RED}✗${NC} Language: Non-ASCII characters detected (use English)"
        is_valid=false
    else
        echo -e "  ${GREEN}✓${NC} Language: English"
    fi
    
    # Check imperative mood (basic check - doesn't start with -ed, -ing)
    if echo "$commit_subject" | grep -qE ": [a-z]+(ed|ing) "; then
        echo -e "  ${YELLOW}⚠${NC}  Style: May not be imperative mood"
        warnings="$warnings\n    - Use imperative mood (e.g., 'add' not 'added' or 'adding')"
        WARNINGS=$((WARNINGS + 1))
    fi
    
    # Check for period at end of subject
    if echo "$commit_subject" | grep -q "\.$"; then
        echo -e "  ${RED}✗${NC} Style: Subject should not end with period"
        is_valid=false
    fi
    
    # Check body line length (if body exists)
    if [ -n "$commit_body" ]; then
        local long_lines=$(echo "$commit_body" | awk 'length > 72 { print NR }' | wc -l)
        if [ $long_lines -gt 0 ]; then
            echo -e "  ${YELLOW}⚠${NC}  Body: $long_lines lines exceed 72 characters"
            warnings="$warnings\n    - Wrap body text at 72 characters"
            WARNINGS=$((WARNINGS + 1))
        fi
    fi
    
    # Check for references to plans that should be in docs
    if echo "$commit_body" | grep -q "plans/.*\.md"; then
        echo -e "  ${YELLOW}⚠${NC}  Reference: Contains reference to plans/ (should reference docs/)"
        warnings="$warnings\n    - Reference docs/ instead of plans/ for specifications"
        WARNINGS=$((WARNINGS + 1))
    fi
    
    # Print warnings if any
    if [ -n "$warnings" ]; then
        echo -e "  ${YELLOW}Warnings:${NC}$warnings"
    fi
    
    # Update counters
    TOTAL_COMMITS=$((TOTAL_COMMITS + 1))
    if [ "$is_valid" = true ]; then
        VALID_COMMITS=$((VALID_COMMITS + 1))
        echo -e "  ${GREEN}✅ Valid commit${NC}"
    else
        INVALID_COMMITS=$((INVALID_COMMITS + 1))
        echo -e "  ${RED}❌ Invalid commit${NC}"
    fi
    
    echo ""
}

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}Error: Not in a git repository${NC}"
    exit 1
fi

# Get recent commits
git log --pretty=format:"%H|%s" -n "$NUM_COMMITS" | while IFS='|' read -r hash subject; do
    # Get full commit message body
    body=$(git log --format=%B -n 1 "$hash" | tail -n +2)
    validate_commit "$hash" "$subject" "$body"
done > $TEMP_FILE

# Display results
cat $TEMP_FILE

# Count results (re-parse since we're in a subshell above)
TOTAL_COMMITS=$(grep -c "^Commit:" $TEMP_FILE || true)
VALID_COMMITS=$(grep -c "✅ Valid commit" $TEMP_FILE || true)
INVALID_COMMITS=$(grep -c "❌ Invalid commit" $TEMP_FILE || true)
WARNINGS=$(grep -c "⚠" $TEMP_FILE || true)

echo "======================================================"
echo "📊 Validation Summary"
echo "======================================================"
echo ""
echo "Total commits checked: $TOTAL_COMMITS"
echo -e "${GREEN}Valid commits: $VALID_COMMITS${NC}"
echo -e "${RED}Invalid commits: $INVALID_COMMITS${NC}"
echo -e "${YELLOW}Warnings: $WARNINGS${NC}"
echo ""

if [ $INVALID_COMMITS -eq 0 ]; then
    echo -e "${GREEN}✨ All commits are valid!${NC}"
    echo ""
    echo "Your commit messages follow the Conventional Commits standard."
    exit 0
else
    echo -e "${RED}⚠️  Some commits do not meet the standards${NC}"
    echo ""
    echo "Please ensure all commits follow:"
    echo "1. Conventional Commits format: <type>(<scope>): <subject>"
    echo "2. English language only"
    echo "3. Subject line ≤50 characters (72 max)"
    echo "4. Imperative mood in subject"
    echo "5. No period at end of subject"
    echo "6. Body lines wrapped at 72 characters"
    echo ""
    echo "Example of a good commit:"
    echo "  feat(models): add Black76 futures pricing model"
    echo ""
    echo "See .claude/commands/commit-ai.md for detailed guidelines."
    exit 1
fi