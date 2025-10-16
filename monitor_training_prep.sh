#!/bin/bash
# Monitor Q&A generation and prepare for training launch

echo "🦉 TinyOwl Training Preparation Monitor"
echo "========================================"
echo ""

TRAINING_DIR="/home/nigel/tinyowl/training_data"
QA_FILE="$TRAINING_DIR/instruction_tuning.jsonl"

while true; do
    clear
    echo "🦉 TinyOwl Training Preparation Monitor"
    echo "========================================"
    echo ""
    echo "📊 Current Status:"
    echo ""

    # Check if generation is still running
    if ps aux | grep -v grep | grep "generate_qa_pairs" > /dev/null; then
        echo "✅ Q&A Generation: RUNNING"

        # Count current Q&A pairs
        if [ -f "$QA_FILE" ]; then
            QA_COUNT=$(wc -l < "$QA_FILE")
            QA_SIZE=$(du -h "$QA_FILE" | cut -f1)
            echo "   └─ Generated: $QA_COUNT Q&A pairs ($QA_SIZE)"

            # Show latest question
            LATEST=$(tail -1 "$QA_FILE" | jq -r '.instruction' 2>/dev/null)
            if [ -n "$LATEST" ]; then
                echo "   └─ Latest: ${LATEST:0:80}..."
            fi
        fi

        echo ""
        echo "⏱️  Estimated completion: 1-2 hours"
        echo "   (Processing 5,000 chunks → ~10,000-15,000 Q&A pairs)"

    else
        echo "✅ Q&A Generation: COMPLETE"

        if [ -f "$QA_FILE" ]; then
            QA_COUNT=$(wc -l < "$QA_FILE")
            QA_SIZE=$(du -h "$QA_FILE" | cut -f1)
            echo "   └─ Final count: $QA_COUNT Q&A pairs ($QA_SIZE)"
        fi

        echo ""
        echo "🎉 READY TO TRAIN!"
        echo ""
        echo "Next steps:"
        echo "1. Go to https://colab.research.google.com/"
        echo "2. Upload TinyOwl_Training.ipynb"
        echo "3. Upload training files (see below)"
        echo "4. Start training!"

        break
    fi

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "📁 Files Ready for Upload:"
    echo ""

    # Check all required files
    if [ -f "/home/nigel/tinyowl/TinyOwl_Training.ipynb" ]; then
        echo "   ✅ TinyOwl_Training.ipynb"
    else
        echo "   ❌ TinyOwl_Training.ipynb (MISSING!)"
    fi

    if [ -f "$TRAINING_DIR/domain_adaptation.jsonl" ]; then
        DA_SIZE=$(du -h "$TRAINING_DIR/domain_adaptation.jsonl" | cut -f1)
        DA_COUNT=$(wc -l < "$TRAINING_DIR/domain_adaptation.jsonl")
        echo "   ✅ domain_adaptation.jsonl ($DA_SIZE - $DA_COUNT chunks)"
    else
        echo "   ❌ domain_adaptation.jsonl (MISSING!)"
    fi

    if [ -f "$QA_FILE" ]; then
        echo "   ✅ instruction_tuning.jsonl ($QA_SIZE - $QA_COUNT pairs)"
    else
        echo "   ❌ instruction_tuning.jsonl (MISSING!)"
    fi

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Press Ctrl+C to stop monitoring"
    echo "Refreshing every 30 seconds..."
    echo ""

    sleep 30
done

echo ""
echo "🚀 All systems GO for training!"
echo ""
echo "Read: /home/nigel/tinyowl/START_TRAINING_NOW.md"
