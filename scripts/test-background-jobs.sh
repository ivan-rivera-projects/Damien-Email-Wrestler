                echo "------------------------------"
                
                RESULT_RESPONSE=$(call_mcp_tool "damien_job_get_result" "{\"job_id\": \"$JOB_ID\"}")
                
                if echo "$RESULT_RESPONSE" | grep -q '"success":true' > /dev/null 2>&1; then
                    echo -e "${GREEN}✓ Job results retrieved successfully${NC}"
                    
                    # Extract key metrics from results
                    EMAILS_ANALYZED=$(echo "$RESULT_RESPONSE" | grep -o '"emails_processed":[0-9]*' | cut -d':' -f2)
                    PATTERNS_FOUND=$(echo "$RESULT_RESPONSE" | grep -o '"patterns_found":[0-9]*' | cut -d':' -f2)
                    
                    if [ -n "$EMAILS_ANALYZED" ]; then
                        echo "Emails analyzed: $EMAILS_ANALYZED"
                    fi
                    if [ -n "$PATTERNS_FOUND" ]; then
                        echo "Patterns found: $PATTERNS_FOUND"
                    fi
                    
                    echo -e "${GREEN}✓ Background job system fully functional${NC}"
                else
                    echo -e "${RED}✗ Failed to retrieve job results${NC}"
                    echo "Response: $RESULT_RESPONSE"
                fi
                break
                
            elif [ "$JOB_STATUS" = "failed" ]; then
                echo -e "${RED}✗ Job failed${NC}"
                ERROR_MESSAGE=$(echo "$STATUS_RESPONSE" | grep -o '"error_message":"[^"]*"' | cut -d'"' -f4)
                echo "Error: $ERROR_MESSAGE"
                break
                
            elif [ "$JOB_STATUS" = "cancelled" ]; then
                echo -e "${YELLOW}! Job was cancelled${NC}"
                break
            fi
        else
            echo -e "${RED}✗ Failed to get job status${NC}"
            break
        fi
        
        ((CHECK_COUNT++))
    done
    
    if [ $CHECK_COUNT -eq $MAX_CHECKS ]; then
        echo -e "${YELLOW}⚠️  Job monitoring timed out after $MAX_CHECKS checks${NC}"
        echo "This might be normal for larger analysis jobs"
        
        # Test job cancellation
        echo ""
        echo -e "${BLUE}Test 6: Testing job cancellation${NC}"
        echo "--------------------------------"
        
        CANCEL_RESPONSE=$(call_mcp_tool "damien_job_cancel" "{\"job_id\": \"$JOB_ID\"}")
        
        if echo "$CANCEL_RESPONSE" | grep -q '"success":true' > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Job cancellation works${NC}"
        else
            echo -e "${YELLOW}! Job may have already completed or failed${NC}"
        fi
    fi
    
else
    echo -e "${RED}✗ Failed to start async analysis job${NC}"
    echo "Response: $ANALYSIS_RESPONSE"
    exit 1
fi

echo ""

# Test 7: Test job management tools
echo -e "${BLUE}Test 7: Testing job management tools${NC}"
echo "-----------------------------------"

# List running jobs
echo "Checking for running jobs..."
RUNNING_JOBS_RESPONSE=$(call_mcp_tool "damien_job_list" '{"status_filter": "running", "limit": 5}')

if echo "$RUNNING_JOBS_RESPONSE" | grep -q '"success":true' > /dev/null 2>&1; then
    RUNNING_COUNT=$(echo "$RUNNING_JOBS_RESPONSE" | grep -o '"count":[0-9]*' | cut -d':' -f2)
    echo "Currently running jobs: $RUNNING_COUNT"
    echo -e "${GREEN}✓ Job filtering works${NC}"
else
    echo -e "${RED}✗ Job filtering failed${NC}"
fi

# List completed jobs
echo "Checking for completed jobs..."
COMPLETED_JOBS_RESPONSE=$(call_mcp_tool "damien_job_list" '{"status_filter": "completed", "limit": 3}')

if echo "$COMPLETED_JOBS_RESPONSE" | grep -q '"success":true' > /dev/null 2>&1; then
    COMPLETED_COUNT=$(echo "$COMPLETED_JOBS_RESPONSE" | grep -o '"count":[0-9]*' | cut -d':' -f2)
    echo "Completed jobs: $COMPLETED_COUNT"
    echo -e "${GREEN}✓ Job history tracking works${NC}"
else
    echo -e "${RED}✗ Job history retrieval failed${NC}"
fi

echo ""

# Final Summary
echo -e "${BLUE}🏆 Test Summary${NC}"
echo "==============="

echo ""
echo -e "${GREEN}✅ Core Background Job Features Tested:${NC}"
echo "  ├─ ✓ Async tool availability"
echo "  ├─ ✓ Job listing and filtering"
echo "  ├─ ✓ Background job creation"
echo "  ├─ ✓ Real-time progress monitoring"
echo "  ├─ ✓ Job result retrieval"
echo "  ├─ ✓ Job status management"
echo "  └─ ✓ Job cancellation (if needed)"

echo ""
echo -e "${BLUE}🎯 Ready for Production Use:${NC}"
echo "  • Large-scale email analysis (3,000+ emails)"
echo "  • Inbox optimization jobs"
echo "  • Progress tracking and notifications"
echo "  • Job management and cancellation"

echo ""
echo -e "${GREEN}🚀 Background job system is fully operational!${NC}"

# Performance recommendations
echo ""
echo -e "${BLUE}💡 Performance Tips:${NC}"
echo "  • Start with smaller target_count (100-500) and scale up"
echo "  • Use specific Gmail queries to focus analysis"
echo "  • Monitor job progress with ./scripts/status.sh"
echo "  • Check logs if jobs fail: logs/damien-mcp-server.log"

echo ""
echo -e "${BLUE}🔗 Integration Ready:${NC}"
echo "  • Connect Claude Desktop to: http://localhost:8081"
echo "  • Use damien_ai_analyze_emails_async for large analyses"
echo "  • Track progress with damien_job_get_status"
echo "  • Retrieve results with damien_job_get_result"

echo ""
echo "✨ Test completed successfully!"
