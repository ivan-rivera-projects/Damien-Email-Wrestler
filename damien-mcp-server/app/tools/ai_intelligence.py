"""
AI Intelligence MCP Tools

This module implements 6 new MCP tools that expose the complete Phase 3 AI intelligence
capabilities through the Model Context Protocol for seamless AI assistant integration.

Tools implemented:
1. damien_ai_analyze_emails - Comprehensive email analysis
2. damien_ai_suggest_rules - Intelligent rule generation  
3. damien_ai_quick_test - Integration validation
4. damien_ai_create_rule - Natural language rule creation
5. damien_ai_get_insights - Email intelligence dashboard
6. damien_ai_optimize_inbox - Intelligent inbox management
"""

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional, Literal
from datetime import datetime, timedelta
import json

from ..services.cli_bridge import CLIBridge
from ..services.async_processor import AsyncTaskProcessor
from ..core.progress_tracker import ProgressTracker

logger = logging.getLogger(__name__)


class AIIntelligenceTools:
    """MCP tools for AI intelligence capabilities."""
    
    def __init__(self):
        self.cli_bridge = CLIBridge()
        self.async_processor = AsyncTaskProcessor()
        self.progress_tracker = ProgressTracker()
        logger.info("AI Intelligence MCP tools initialized")
    
    async def damien_ai_analyze_emails(
        self,
        days: int = 30,
        max_emails: int = 500,
        min_confidence: float = 0.7,
        output_format: Literal["summary", "detailed", "json"] = "summary",
        query: Optional[str] = None,
        patterns_only: bool = False
    ) -> Dict[str, Any]:
        """
        Perform comprehensive AI analysis of Gmail emails.
        
        Advanced features:
        - Real Gmail API integration with pattern detection
        - Intelligent embedding generation with caching
        - Business impact analysis with ROI calculations
        - Multi-algorithm pattern detection (8+ types)
        - Executive-ready reporting and visualizations
        """
        start_time = time.time()
        
        try:
            logger.info(f"Starting email analysis: {days} days, {max_emails} max emails")
            
            # Create progress tracking
            operation = self.progress_tracker.create_operation(
                name="Email Analysis",
                total_items=max_emails,
                steps=[
                    ("fetch", "Fetching Emails", "Retrieving emails from Gmail"),
                    ("analyze", "AI Analysis", "Performing intelligent analysis"),
                    ("patterns", "Pattern Detection", "Detecting email patterns"),
                    ("insights", "Generate Insights", "Creating insights and recommendations")
                ]
            )
            operation.start()
            
            # Step 1: Fetch emails
            operation.update_progress(message="Fetching emails from Gmail...")
            emails = await self.cli_bridge.fetch_recent_emails(
                days=days,
                max_count=max_emails,
                query=query
            )
            operation.advance_step(f"Fetched {len(emails)} emails")
            
            # Step 2: AI Analysis
            operation.update_progress(message="Performing AI analysis...")
            analysis_result = await self.cli_bridge.analyze_emails_with_ai(
                emails=emails,
                min_confidence=min_confidence,
                include_patterns=not patterns_only
            )
            operation.advance_step("AI analysis completed")
            
            # Step 3: Pattern Detection
            operation.update_progress(message="Detecting patterns...")
            patterns = await self.cli_bridge.detect_email_patterns(
                emails=emails,
                analysis_result=analysis_result
            )
            operation.advance_step(f"Detected {len(patterns)} patterns")
            
            # Step 4: Generate insights
            operation.update_progress(message="Generating insights...")
            insights = await self.cli_bridge.generate_insights(
                emails=emails,
                patterns=patterns,
                analysis_result=analysis_result
            )
            operation.complete("Analysis completed successfully")
            
            processing_time = time.time() - start_time
            
            # Format response based on output_format
            if output_format == "summary":
                return {
                    "status": "success",
                    "summary": {
                        "emails_analyzed": len(emails),
                        "patterns_detected": len(patterns),
                        "processing_time_seconds": round(processing_time, 2),
                        "confidence_threshold": min_confidence,
                        "key_insights": insights.get("summary", [])[:5]
                    },
                    "recommendations": insights.get("recommendations", [])[:3],
                    "business_impact": {
                        "automation_potential": f"{insights.get('automation_rate', 0):.1f}%",
                        "time_savings_estimate": f"{insights.get('time_savings_hours', 0):.1f} hours/week"
                    }
                }
            
            elif output_format == "detailed":
                return {
                    "status": "success",
                    "analysis": {
                        "emails_analyzed": len(emails),
                        "patterns_detected": len(patterns),
                        "processing_time_seconds": round(processing_time, 2),
                        "confidence_threshold": min_confidence
                    },
                    "patterns": patterns,
                    "insights": insights,
                    "performance_metrics": {
                        "throughput_emails_per_second": len(emails) / processing_time if processing_time > 0 else 0,
                        "average_confidence": analysis_result.get("average_confidence", 0),
                        "pattern_accuracy": analysis_result.get("pattern_accuracy", 0)
                    }
                }
            
            else:  # json format
                return {
                    "status": "success",
                    "data": {
                        "emails": [email.to_dict() for email in emails] if hasattr(emails[0], 'to_dict') else emails,
                        "patterns": patterns,
                        "analysis": analysis_result,
                        "insights": insights,
                        "metadata": {
                            "processing_time": processing_time,
                            "email_count": len(emails),
                            "pattern_count": len(patterns)
                        }
                    }
                }
                
        except Exception as e:
            logger.error(f"Email analysis failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "processing_time_seconds": time.time() - start_time
            }
    
    async def damien_ai_suggest_rules(
        self,
        limit: int = 5,
        min_confidence: float = 0.8,
        categories: Optional[List[str]] = None,
        include_business_impact: bool = True,
        auto_validate: bool = True
    ) -> Dict[str, Any]:
        """
        Generate intelligent email management rules.
        
        Advanced features:
        - ML-powered pattern analysis for rule generation
        - Business impact assessment with time savings
        - Confidence scoring with statistical validation
        - Rule complexity analysis and optimization
        - Integration with existing Damien rule system
        """
        start_time = time.time()
        
        try:
            logger.info(f"Generating rule suggestions: limit={limit}, confidence={min_confidence}")
            
            # Create progress tracking
            operation = self.progress_tracker.create_operation(
                name="Rule Suggestion Generation",
                steps=[
                    ("analyze", "Pattern Analysis", "Analyzing email patterns"),
                    ("generate", "Rule Generation", "Generating intelligent rules"),
                    ("validate", "Rule Validation", "Validating rule effectiveness"),
                    ("impact", "Business Impact", "Calculating business impact")
                ]
            )
            operation.start()
            
            # Step 1: Analyze patterns
            operation.update_progress(message="Analyzing email patterns...")
            pattern_analysis = await self.cli_bridge.analyze_patterns_for_rules(
                categories=categories,
                min_confidence=min_confidence
            )
            operation.advance_step("Pattern analysis completed")
            
            # Step 2: Generate rules
            operation.update_progress(message="Generating intelligent rules...")
            rule_suggestions = await self.cli_bridge.generate_rule_suggestions(
                patterns=pattern_analysis,
                limit=limit,
                min_confidence=min_confidence
            )
            operation.advance_step(f"Generated {len(rule_suggestions)} rule suggestions")
            
            # Step 3: Validate rules (if enabled)
            if auto_validate:
                operation.update_progress(message="Validating rule effectiveness...")
                validation_results = await self.cli_bridge.validate_rule_suggestions(
                    rule_suggestions=rule_suggestions
                )
                operation.advance_step("Rule validation completed")
            else:
                validation_results = {"skipped": True}
            
            # Step 4: Calculate business impact (if enabled)
            if include_business_impact:
                operation.update_progress(message="Calculating business impact...")
                business_impact = await self.cli_bridge.calculate_rule_business_impact(
                    rule_suggestions=rule_suggestions
                )
                operation.advance_step("Business impact calculated")
            else:
                business_impact = {"skipped": True}
            
            operation.complete("Rule suggestions generated successfully")
            
            processing_time = time.time() - start_time
            
            return {
                "status": "success",
                "suggestions": rule_suggestions,
                "validation": validation_results,
                "business_impact": business_impact,
                "metadata": {
                    "suggestions_count": len(rule_suggestions),
                    "processing_time_seconds": round(processing_time, 2),
                    "confidence_threshold": min_confidence,
                    "categories_analyzed": categories or "all"
                },
                "summary": {
                    "total_suggestions": len(rule_suggestions),
                    "high_confidence_count": len([r for r in rule_suggestions if r.get("confidence", 0) >= 0.9]),
                    "estimated_time_savings": business_impact.get("total_time_savings_hours", 0) if include_business_impact else "not_calculated"
                }
            }
            
        except Exception as e:
            logger.error(f"Rule suggestion failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "processing_time_seconds": time.time() - start_time
            }
    
    async def damien_ai_quick_test(
        self,
        sample_size: int = 50,
        days: int = 7,
        include_performance: bool = True,
        validate_components: bool = True
    ) -> Dict[str, Any]:
        """
        Quick validation of AI integration and performance.
        
        Advanced features:
        - Component health checking and validation
        - Performance benchmarking and optimization
        - Sample data analysis with confidence metrics
        - System readiness assessment for production
        """
        start_time = time.time()
        
        try:
            logger.info(f"Running AI integration quick test: {sample_size} samples, {days} days")
            
            # Test results collector
            test_results = {
                "component_tests": {},
                "performance_tests": {},
                "integration_tests": {}
            }
            
            # Component validation tests
            if validate_components:
                component_results = await self.cli_bridge.validate_ai_components()
                test_results["component_tests"] = component_results
            
            # Performance tests
            if include_performance:
                performance_results = await self.cli_bridge.run_performance_tests(
                    sample_size=sample_size
                )
                test_results["performance_tests"] = performance_results
            
            # Integration test with sample data
            sample_emails = await self.cli_bridge.fetch_recent_emails(
                days=days,
                max_count=sample_size
            )
            
            if sample_emails:
                # Quick analysis test
                quick_analysis = await self.cli_bridge.quick_analyze_emails(sample_emails)
                test_results["integration_tests"]["sample_analysis"] = quick_analysis
                
                # Quick search test
                search_test = await self.cli_bridge.test_search_functionality(sample_emails)
                test_results["integration_tests"]["search_test"] = search_test
            
            processing_time = time.time() - start_time
            
            # Calculate overall health score
            health_score = self._calculate_health_score(test_results)
            
            return {
                "status": "success",
                "health_score": health_score,
                "test_results": test_results,
                "summary": {
                    "total_tests_run": len([t for category in test_results.values() for t in category.keys()]),
                    "processing_time_seconds": round(processing_time, 2),
                    "sample_size": len(sample_emails) if sample_emails else 0,
                    "components_validated": validate_components,
                    "performance_tested": include_performance,
                    "system_ready": health_score >= 0.8
                },
                "recommendations": self._generate_test_recommendations(test_results, health_score)
            }
            
        except Exception as e:
            logger.error(f"Quick test failed: {e}")
            return {
                "status": "error", 
                "error": str(e),
                "processing_time_seconds": time.time() - start_time
            }
    
    async def damien_ai_create_rule(
        self,
        rule_description: str,
        validate_before_create: bool = True,
        dry_run: bool = False,
        confidence_threshold: float = 0.8
    ) -> Dict[str, Any]:
        """
        Create email rules using natural language descriptions.
        
        Advanced features:
        - GPT-4 powered natural language processing
        - Intent recognition and rule translation
        - Validation against existing rules for conflicts
        - Preview and confirmation before implementation
        """
        start_time = time.time()
        
        try:
            logger.info(f"Creating rule from description: '{rule_description[:50]}...'")
            
            # Parse natural language description
            parsed_rule = await self.cli_bridge.parse_natural_language_rule(
                description=rule_description
            )
            
            # Validate rule if requested
            validation_result = None
            if validate_before_create:
                validation_result = await self.cli_bridge.validate_rule_before_creation(
                    parsed_rule=parsed_rule,
                    confidence_threshold=confidence_threshold
                )
            
            # Create rule (or dry run)
            if dry_run:
                creation_result = {
                    "dry_run": True,
                    "would_create": parsed_rule,
                    "estimated_impact": await self.cli_bridge.estimate_rule_impact(parsed_rule)
                }
            else:
                creation_result = await self.cli_bridge.create_email_rule(
                    parsed_rule=parsed_rule
                )
            
            processing_time = time.time() - start_time
            
            return {
                "status": "success",
                "rule_created": not dry_run,
                "dry_run": dry_run,
                "parsed_rule": parsed_rule,
                "validation": validation_result,
                "creation_result": creation_result,
                "metadata": {
                    "original_description": rule_description,
                    "processing_time_seconds": round(processing_time, 2),
                    "confidence_threshold": confidence_threshold,
                    "validation_performed": validate_before_create
                }
            }
            
        except Exception as e:
            logger.error(f"Rule creation failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "original_description": rule_description,
                "processing_time_seconds": time.time() - start_time
            }
    
    async def damien_ai_get_insights(
        self,
        insight_type: Literal["trends", "patterns", "efficiency", "summary"] = "summary",
        time_range: int = 30,
        include_predictions: bool = False,
        format: Literal["text", "json", "chart_data"] = "text"
    ) -> Dict[str, Any]:
        """
        Get comprehensive email intelligence and insights.
        
        Advanced features:
        - Trend analysis with predictive modeling
        - Efficiency metrics and automation opportunities
        - Pattern evolution tracking over time
        - Business intelligence reporting
        """
        start_time = time.time()
        
        try:
            logger.info(f"Generating insights: type={insight_type}, range={time_range} days")
            
            # Generate insights based on type
            if insight_type == "trends":
                insights_data = await self.cli_bridge.analyze_email_trends(
                    days=time_range,
                    include_predictions=include_predictions
                )
            elif insight_type == "patterns":
                insights_data = await self.cli_bridge.analyze_email_patterns(
                    days=time_range
                )
            elif insight_type == "efficiency":
                insights_data = await self.cli_bridge.analyze_email_efficiency(
                    days=time_range
                )
            else:  # summary
                insights_data = await self.cli_bridge.generate_summary_insights(
                    days=time_range,
                    include_predictions=include_predictions
                )
            
            processing_time = time.time() - start_time
            
            # Format response based on format preference
            if format == "text":
                formatted_insights = await self.cli_bridge.format_insights_as_text(insights_data)
            elif format == "chart_data":
                formatted_insights = await self.cli_bridge.format_insights_as_chart_data(insights_data)
            else:  # json
                formatted_insights = insights_data
            
            return {
                "status": "success",
                "insight_type": insight_type,
                "insights": formatted_insights,
                "metadata": {
                    "time_range_days": time_range,
                    "format": format,
                    "include_predictions": include_predictions,
                    "processing_time_seconds": round(processing_time, 2),
                    "data_points_analyzed": insights_data.get("data_points", 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Insights generation failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "insight_type": insight_type,
                "processing_time_seconds": time.time() - start_time
            }
    
    async def damien_ai_optimize_inbox(
        self,
        optimization_type: Literal["declutter", "organize", "automate", "all"] = "all", 
        aggressiveness: Literal["conservative", "moderate", "aggressive"] = "moderate",
        dry_run: bool = True,
        max_actions: int = 100
    ) -> Dict[str, Any]:
        """
        AI-powered inbox optimization and management.
        
        Advanced features:
        - Multi-strategy optimization algorithms
        - Risk assessment and safety mechanisms
        - Batch processing with progress tracking
        - Rollback capabilities for all operations
        """
        start_time = time.time()
        
        try:
            logger.info(f"Optimizing inbox: type={optimization_type}, aggressiveness={aggressiveness}")
            
            # Create progress tracking
            operation = self.progress_tracker.create_operation(
                name="Inbox Optimization",
                steps=[
                    ("analyze", "Inbox Analysis", "Analyzing current inbox state"),
                    ("plan", "Optimization Planning", "Creating optimization plan"),
                    ("execute", "Execute Changes", "Applying optimizations"),
                    ("verify", "Verification", "Verifying optimization results")
                ]
            )
            operation.start()
            
            # Step 1: Analyze current inbox state
            operation.update_progress(message="Analyzing inbox...")
            inbox_analysis = await self.cli_bridge.analyze_inbox_state()
            operation.advance_step("Inbox analysis completed")
            
            # Step 2: Create optimization plan
            operation.update_progress(message="Creating optimization plan...")
            optimization_plan = await self.cli_bridge.create_optimization_plan(
                analysis=inbox_analysis,
                optimization_type=optimization_type,
                aggressiveness=aggressiveness,
                max_actions=max_actions
            )
            operation.advance_step(f"Plan created with {len(optimization_plan.get('actions', []))} actions")
            
            # Step 3: Execute optimizations (or dry run)
            if dry_run:
                operation.update_progress(message="Simulating optimizations...")
                execution_result = await self.cli_bridge.simulate_optimizations(
                    plan=optimization_plan
                )
                operation.advance_step("Simulation completed")
            else:
                operation.update_progress(message="Executing optimizations...")
                execution_result = await self.cli_bridge.execute_optimizations(
                    plan=optimization_plan
                )
                operation.advance_step("Optimizations executed")
            
            # Step 4: Verify results
            operation.update_progress(message="Verifying results...")
            verification_result = await self.cli_bridge.verify_optimization_results(
                execution_result=execution_result,
                dry_run=dry_run
            )
            operation.complete("Inbox optimization completed")
            
            processing_time = time.time() - start_time
            
            return {
                "status": "success",
                "dry_run": dry_run,
                "optimization_type": optimization_type,
                "aggressiveness": aggressiveness,
                "plan": optimization_plan,
                "execution_result": execution_result,
                "verification": verification_result,
                "summary": {
                    "actions_planned": len(optimization_plan.get("actions", [])),
                    "actions_executed": execution_result.get("actions_completed", 0) if not dry_run else "simulated",
                    "processing_time_seconds": round(processing_time, 2),
                    "inbox_improvement": verification_result.get("improvement_score", 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Inbox optimization failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "optimization_type": optimization_type,
                "processing_time_seconds": time.time() - start_time
            }
    
    def _calculate_health_score(self, test_results: Dict[str, Any]) -> float:
        """Calculate overall system health score from test results."""
        scores = []
        
        # Component health
        if test_results.get("component_tests"):
            component_score = sum(1 for result in test_results["component_tests"].values() 
                                if result.get("status") == "healthy") / len(test_results["component_tests"])
            scores.append(component_score)
        
        # Performance health
        if test_results.get("performance_tests"):
            perf_tests = test_results["performance_tests"]
            perf_score = 1.0 if perf_tests.get("meets_targets", False) else 0.5
            scores.append(perf_score)
        
        # Integration health
        if test_results.get("integration_tests"):
            integration_score = 0.5  # Base score
            if test_results["integration_tests"].get("sample_analysis", {}).get("success"):
                integration_score += 0.3
            if test_results["integration_tests"].get("search_test", {}).get("success"):
                integration_score += 0.2
            scores.append(integration_score)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _generate_test_recommendations(self, test_results: Dict[str, Any], health_score: float) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        if health_score < 0.7:
            recommendations.append("System health below optimal - review component status")
        
        if test_results.get("performance_tests", {}).get("average_response_time", 0) > 1000:
            recommendations.append("Response times above target - consider performance optimization")
        
        if not test_results.get("integration_tests", {}).get("search_test", {}).get("success"):
            recommendations.append("Search functionality issues detected - validate RAG engine")
        
        if health_score >= 0.9:
            recommendations.append("System performing excellently - ready for production use")
        
        return recommendations or ["System health acceptable - no immediate actions required"]


# Export the tools class for MCP server integration
ai_intelligence_tools = AIIntelligenceTools()
