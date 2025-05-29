#!/usr/bin/env python3
"""Generate comprehensive integration status report"""

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "damien_cli"))

def generate_integration_report():
    """Generate comprehensive status report"""
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "phase_2_status": "validation_in_progress",
        "components": {},
        "tests": {},
        "recommendations": []
    }
    
    # Test each component
    components_to_test = [
        ("Models", test_models_status),
        ("Embeddings", test_embeddings_status),
        ("Patterns", test_patterns_status),
        ("Gmail Analyzer", test_gmail_analyzer_status),
        ("Batch Processor", test_batch_processor_status),
        ("AI Commands", test_ai_commands_status),
    ]
    
    for component_name, test_func in components_to_test:
        try:
            status = test_func()
            report["components"][component_name] = status
        except Exception as e:
            report["components"][component_name] = {
                "status": "error",
                "error": str(e)
            }
    
    # Calculate overall status
    working_components = sum(1 for comp in report["components"].values() 
                           if comp.get("status") == "working")
    total_components = len(report["components"])
    completion_rate = working_components / total_components * 100
    
    report["overall_completion"] = f"{completion_rate:.1f}%"
    report["working_components"] = f"{working_components}/{total_components}"
    
    # Generate recommendations
    if completion_rate >= 90:
        report["recommendations"].append("✅ Phase 2 is ready - proceed to Phase 4")
    elif completion_rate >= 70:
        report["recommendations"].append("⚠️ Most components working - fix remaining issues")
    else:
        report["recommendations"].append("❌ Significant work needed before Phase 4")
    
    # Save report
    with open("phase_2_integration_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("📊 Phase 2 Integration Status Report")
    print("=" * 40)
    print(f"Overall Completion: {report['overall_completion']}")
    print(f"Working Components: {report['working_components']}")
    print("\nComponent Status:")
    
    for comp_name, comp_status in report["components"].items():
        status_icon = "✅" if comp_status.get("status") == "working" else "❌"
        print(f"  {status_icon} {comp_name}: {comp_status.get('status', 'unknown')}")
    
    print("\nRecommendations:")
    for rec in report["recommendations"]:
        print(f"  {rec}")
    
    return report

def test_models_status():
    """Test models component status"""
    try:
        from damien_cli.features.ai_intelligence.models import BatchProcessingResult
        # Quick validation
        BatchProcessingResult(
            total_items=1, processed_successfully=1, failed_items=0,
            skipped_items=0, processing_time_seconds=1.0, throughput_per_second=1.0,
            peak_memory_usage_mb=1.0, average_cpu_usage_percent=1.0,
            patterns_discovered=0, suggestions_created=0, retry_attempts=0,
            embeddings_generated=0, batch_size=1, parallel_workers=1
        )
        return {"status": "working", "details": "All model imports and validation successful"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def test_embeddings_status():
    """Test embeddings component status"""
    try:
        from damien_cli.features.ai_intelligence.categorization.embeddings import EmailEmbeddingGenerator
        generator = EmailEmbeddingGenerator()
        test_email = {'id': 'test', 'subject': 'test', 'snippet': 'test', 'from_sender': 'test@test.com'}
        embedding = generator.generate_embedding(test_email)
        return {"status": "working", "details": f"Embedding generated, dimension: {len(embedding)}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def test_patterns_status():
    """Test patterns component status"""
    try:
        from damien_cli.features.ai_intelligence.categorization.patterns import EmailPatternDetector
        detector = EmailPatternDetector()
        return {"status": "working", "details": "Pattern detector initialized successfully"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def test_gmail_analyzer_status():
    """Test Gmail analyzer status"""
    try:
        from damien_cli.features.ai_intelligence.categorization.gmail_analyzer import GmailEmailAnalyzer
        analyzer = GmailEmailAnalyzer(gmail_service=None)
        return {"status": "working", "details": "Gmail analyzer initialized successfully"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def test_batch_processor_status():
    """Test batch processor status"""
    try:
        from damien_cli.features.ai_intelligence.utils.batch_processor import BatchEmailProcessor
        processor = BatchEmailProcessor()
        return {"status": "working", "details": "Batch processor initialized successfully"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def test_ai_commands_status():
    """Test AI commands status"""
    try:
        from damien_cli.features.ai_intelligence.commands import ai_group
        commands = [cmd.name for cmd in ai_group.commands.values()]
        return {"status": "working", "details": f"AI commands available: {', '.join(commands)}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    report = generate_integration_report()
    
    # Exit with error code if completion rate is too low
    completion = float(report["overall_completion"].replace("%", ""))
    sys.exit(0 if completion >= 70 else 1)