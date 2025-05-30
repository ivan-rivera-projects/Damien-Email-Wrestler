total_tasks_executed / self.total_workflows_executed
            if self.total_workflows_executed > 0 else 0
        )
        
        return {
            "workflow_metrics": {
                "total_workflows_executed": self.total_workflows_executed,
                "total_tasks_executed": self.total_tasks_executed,
                "average_workflow_time_seconds": avg_workflow_time,
                "average_tasks_per_workflow": avg_tasks_per_workflow
            },
            "active_workflows": len(self.active_workflows),
            "registered_workflows": len(self.workflow_registry),
            "component_availability": {
                "rag_engine": self.rag_engine is not None,
                "batch_processor": self.batch_processor is not None,
                "chunker": self.chunker is not None,
                "privacy_guardian": self.privacy_guardian is not None
            }
        }


# Factory function for easy initialization
def create_hierarchical_processor(
    rag_engine: Optional[RAGEngine] = None,
    batch_processor: Optional[BatchProcessor] = None,
    chunker: Optional[IntelligentChunker] = None,
    privacy_guardian: Optional[PrivacyGuardian] = None
) -> HierarchicalProcessor:
    """Factory function to create a hierarchical processor with component dependencies."""
    return HierarchicalProcessor(
        rag_engine=rag_engine,
        batch_processor=batch_processor,
        chunker=chunker,
        privacy_guardian=privacy_guardian
    )


# Predefined workflow templates
class WorkflowTemplates:
    """Predefined workflow templates for common email processing scenarios."""
    
    @staticmethod
    def comprehensive_analysis_workflow(
        emails: List[EmailItem],
        search_queries: List[str] = None
    ) -> ProcessingWorkflow:
        """Create a comprehensive email analysis workflow template."""
        return ProcessingWorkflow(
            workflow_id=f"comprehensive_{uuid.uuid4().hex[:8]}",
            name="Comprehensive Email Analysis",
            description="Complete analysis including privacy, chunking, batch processing, RAG indexing, and search",
            allow_parallel_execution=True,
            failure_strategy="continue",
            metadata={
                "template": "comprehensive_analysis",
                "emails_count": len(emails),
                "search_queries": search_queries or []
            }
        )
    
    @staticmethod
    def privacy_focused_workflow(emails: List[EmailItem]) -> ProcessingWorkflow:
        """Create a privacy-focused workflow template."""
        return ProcessingWorkflow(
            workflow_id=f"privacy_{uuid.uuid4().hex[:8]}",
            name="Privacy-Focused Analysis",
            description="Privacy protection with basic analysis and chunking",
            allow_parallel_execution=False,  # Sequential for privacy
            failure_strategy="stop",  # Stop on privacy failures
            metadata={
                "template": "privacy_focused",
                "emails_count": len(emails)
            }
        )
    
    @staticmethod
    def performance_optimized_workflow(emails: List[EmailItem]) -> ProcessingWorkflow:
        """Create a performance-optimized workflow template."""
        return ProcessingWorkflow(
            workflow_id=f"performance_{uuid.uuid4().hex[:8]}",
            name="Performance-Optimized Analysis",
            description="Fast parallel processing with minimal dependencies",
            allow_parallel_execution=True,
            failure_strategy="continue",
            global_timeout_seconds=300,  # 5 minute limit
            metadata={
                "template": "performance_optimized",
                "emails_count": len(emails)
            }
        )
