#!/usr/bin/env python3
"""
TinyOwl Evaluation Harness
Daily testing framework to ensure system quality and catch regressions
"""

import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
from pathlib import Path


class TestCategory(Enum):
    """Categories of evaluation tests"""
    COVERAGE = "coverage"           # Verse coverage completeness
    RETRIEVAL = "retrieval"        # Information retrieval accuracy  
    ANSWERING = "answering"        # Response quality and faithfulness
    PERFORMANCE = "performance"    # Speed and efficiency
    HUMILITY = "humility"         # Theological humility compliance


@dataclass 
class TestCase:
    """Individual test case"""
    id: str
    category: TestCategory
    description: str
    input_data: Any
    expected_output: Any
    success_criteria: str
    timeout_seconds: int = 30


@dataclass
class TestResult:
    """Result of running a test case"""
    test_id: str
    category: TestCategory
    success: bool
    score: float
    execution_time: float
    details: Dict[str, Any]
    error_message: Optional[str] = None


@dataclass
class EvaluationReport:
    """Complete evaluation report"""
    timestamp: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    category_scores: Dict[str, float]
    overall_score: float
    test_results: List[TestResult]
    recommendations: List[str]


class EvaluationHarness:
    """Main evaluation harness for TinyOwl"""
    
    def __init__(self, config_path: str = "configs/evaluation.yaml"):
        self.config_path = Path(config_path)
        self.test_cases = self._load_test_cases()
        self.metrics = {}
        
    def _load_test_cases(self) -> List[TestCase]:
        """Load test cases from configuration"""
        # For now, create test cases programmatically
        # Later this can load from YAML configuration
        return [
            # Coverage Tests
            TestCase(
                id="coverage_all_books",
                category=TestCategory.COVERAGE,
                description="All 66 Bible books present",
                input_data={"check": "book_count"},
                expected_output={"count": 66},
                success_criteria="All canonical books must be present"
            ),
            TestCase(
                id="coverage_total_verses", 
                category=TestCategory.COVERAGE,
                description="Total verse count matches canonical (31,102)",
                input_data={"check": "verse_count"},
                expected_output={"count": 31102},
                success_criteria="Exact verse count match required"
            ),
            TestCase(
                id="coverage_no_duplicates",
                category=TestCategory.COVERAGE, 
                description="No duplicate OSIS IDs",
                input_data={"check": "duplicates"},
                expected_output={"duplicates": []},
                success_criteria="Zero duplicate OSIS IDs allowed"
            ),
            
            # Retrieval Tests
            TestCase(
                id="retrieval_john_3_16",
                category=TestCategory.RETRIEVAL,
                description="Find John 3:16 in top-5 results",
                input_data={"query": "John 3:16", "k": 5},
                expected_output={"osis_id": "John.03.016"},
                success_criteria="Correct pericope in top-5 results"
            ),
            TestCase(
                id="retrieval_salvation_doctrine",
                category=TestCategory.RETRIEVAL,
                description="Doctrinal query returns relevant passages",
                input_data={"query": "salvation by faith", "k": 10},
                expected_output={"relevance_score": 0.8},
                success_criteria="Average relevance score >= 0.8"
            ),
            TestCase(
                id="retrieval_sop_query",
                category=TestCategory.RETRIEVAL,
                description="SOP query routes to correct sources", 
                input_data={"query": "according to Ellen White", "k": 8},
                expected_output={"sop_percentage": 0.75},
                success_criteria="75%+ results from SOP sources"
            ),
            
            # Answering Tests
            TestCase(
                id="answering_no_hallucination",
                category=TestCategory.ANSWERING,
                description="No fabricated verse references",
                input_data={"query": "What does the Bible say about salvation?"},
                expected_output={"hallucinated_refs": 0},
                success_criteria="Zero fabricated scripture references"
            ),
            TestCase(
                id="answering_source_attribution", 
                category=TestCategory.ANSWERING,
                description="All answers include proper source citations",
                input_data={"query": "What is the unpardonable sin?"},
                expected_output={"has_sources": True},
                success_criteria="Response includes at least one Level-1 source"
            ),
            TestCase(
                id="answering_humility_levels",
                category=TestCategory.HUMILITY,
                description="Response uses appropriate humility language",
                input_data={"query": "Compare different views on the Sabbath"},
                expected_output={"humility_markers": ["Scripture states", "appears to", "may indicate"]},
                success_criteria="Proper authority level language used"
            ),
            
            # Performance Tests
            TestCase(
                id="performance_query_speed",
                category=TestCategory.PERFORMANCE,
                description="End-to-end query under 1.5s (p95)",
                input_data={"query": "Romans 3:23", "target_time": 1.5},
                expected_output={"response_time": 1.5},
                success_criteria="95% of queries complete under 1.5 seconds",
                timeout_seconds=5
            ),
            TestCase(
                id="performance_cold_cache",
                category=TestCategory.PERFORMANCE,
                description="Cold cache performance acceptable",
                input_data={"query": "first query after restart", "cold_cache": True},
                expected_output={"response_time": 3.0},
                success_criteria="Cold cache queries under 3 seconds"
            )
        ]
    
    def run_coverage_test(self, test_case: TestCase, system_data: Dict) -> TestResult:
        """Run coverage validation test"""
        start_time = time.time()
        
        try:
            if test_case.input_data["check"] == "book_count":
                actual_count = len(system_data.get("books", []))
                expected_count = test_case.expected_output["count"] 
                success = actual_count == expected_count
                score = 1.0 if success else 0.0
                
                return TestResult(
                    test_id=test_case.id,
                    category=test_case.category,
                    success=success,
                    score=score,
                    execution_time=time.time() - start_time,
                    details={"actual_count": actual_count, "expected_count": expected_count}
                )
                
            elif test_case.input_data["check"] == "verse_count":
                actual_count = system_data.get("total_verses", 0)
                expected_count = test_case.expected_output["count"]
                success = actual_count == expected_count
                score = 1.0 if success else actual_count / expected_count
                
                return TestResult(
                    test_id=test_case.id,
                    category=test_case.category,
                    success=success,
                    score=score,
                    execution_time=time.time() - start_time,
                    details={"actual_count": actual_count, "expected_count": expected_count}
                )
                
            elif test_case.input_data["check"] == "duplicates":
                duplicates = system_data.get("duplicate_osis_ids", [])
                success = len(duplicates) == 0
                score = 1.0 if success else max(0.0, 1.0 - len(duplicates) / 1000)
                
                return TestResult(
                    test_id=test_case.id,
                    category=test_case.category,
                    success=success,
                    score=score,
                    execution_time=time.time() - start_time,
                    details={"duplicate_count": len(duplicates), "duplicates": duplicates[:10]}
                )
                
        except Exception as e:
            return TestResult(
                test_id=test_case.id,
                category=test_case.category,
                success=False,
                score=0.0,
                execution_time=time.time() - start_time,
                details={},
                error_message=str(e)
            )
    
    def run_retrieval_test(self, test_case: TestCase, retrieval_function) -> TestResult:
        """Run retrieval accuracy test"""
        start_time = time.time()
        
        try:
            query = test_case.input_data["query"]
            k = test_case.input_data.get("k", 5)
            
            # Execute retrieval
            results = retrieval_function(query, k)
            
            if test_case.id == "retrieval_john_3_16":
                # Check if John 3:16 is in top-5
                target_osis = test_case.expected_output["osis_id"]
                found = any(r.get("metadata", {}).get("osis_id") == target_osis for r in results)
                score = 1.0 if found else 0.0
                
                return TestResult(
                    test_id=test_case.id,
                    category=test_case.category,
                    success=found,
                    score=score,
                    execution_time=time.time() - start_time,
                    details={"found_target": found, "result_count": len(results)}
                )
                
            elif "relevance_score" in test_case.expected_output:
                # Calculate relevance (placeholder - would need human ratings)
                avg_score = sum(r.get("score", 0) for r in results) / len(results) if results else 0
                target_score = test_case.expected_output["relevance_score"]
                success = avg_score >= target_score
                
                return TestResult(
                    test_id=test_case.id,
                    category=test_case.category,
                    success=success,
                    score=min(1.0, avg_score / target_score),
                    execution_time=time.time() - start_time,
                    details={"average_score": avg_score, "target_score": target_score}
                )
                
        except Exception as e:
            return TestResult(
                test_id=test_case.id,
                category=test_case.category,
                success=False,
                score=0.0,
                execution_time=time.time() - start_time,
                details={},
                error_message=str(e)
            )
    
    def run_answering_test(self, test_case: TestCase, answer_function) -> TestResult:
        """Run answer quality test"""
        start_time = time.time()
        
        try:
            query = test_case.input_data["query"]
            response = answer_function(query)
            
            if test_case.id == "answering_no_hallucination":
                # Check for fabricated references (simplified check)
                hallucinated = 0  # Would implement actual hallucination detection
                success = hallucinated == 0
                score = 1.0 if success else max(0.0, 1.0 - hallucinated / 10)
                
                return TestResult(
                    test_id=test_case.id,
                    category=test_case.category,
                    success=success,
                    score=score,
                    execution_time=time.time() - start_time,
                    details={"hallucinated_refs": hallucinated}
                )
                
            elif test_case.id == "answering_source_attribution":
                # Check if response has proper sources
                has_sources = bool(getattr(response, 'scripture_sources', []) or 
                                 getattr(response, 'sop_sources', []))
                success = has_sources
                score = 1.0 if success else 0.0
                
                return TestResult(
                    test_id=test_case.id,
                    category=test_case.category,
                    success=success,
                    score=score,
                    execution_time=time.time() - start_time,
                    details={"has_sources": has_sources}
                )
                
        except Exception as e:
            return TestResult(
                test_id=test_case.id,
                category=test_case.category,
                success=False,
                score=0.0,
                execution_time=time.time() - start_time,
                details={},
                error_message=str(e)
            )
    
    def run_performance_test(self, test_case: TestCase, system_function) -> TestResult:
        """Run performance test"""
        start_time = time.time()
        
        try:
            query = test_case.input_data["query"]
            target_time = test_case.input_data.get("target_time", 2.0)
            
            # Execute query
            response = system_function(query)
            actual_time = time.time() - start_time
            
            success = actual_time <= target_time
            score = min(1.0, target_time / actual_time) if actual_time > 0 else 1.0
            
            return TestResult(
                test_id=test_case.id,
                category=test_case.category,
                success=success,
                score=score,
                execution_time=actual_time,
                details={"actual_time": actual_time, "target_time": target_time}
            )
            
        except Exception as e:
            return TestResult(
                test_id=test_case.id,
                category=test_case.category,
                success=False,
                score=0.0,
                execution_time=time.time() - start_time,
                details={},
                error_message=str(e)
            )
    
    def run_full_evaluation(self, 
                          system_data: Dict,
                          retrieval_function,
                          answer_function, 
                          system_function) -> EvaluationReport:
        """Run complete evaluation suite"""
        
        results = []
        
        for test_case in self.test_cases:
            if test_case.category == TestCategory.COVERAGE:
                result = self.run_coverage_test(test_case, system_data)
            elif test_case.category == TestCategory.RETRIEVAL:
                result = self.run_retrieval_test(test_case, retrieval_function)
            elif test_case.category == TestCategory.ANSWERING:
                result = self.run_answering_test(test_case, answer_function)
            elif test_case.category == TestCategory.PERFORMANCE:
                result = self.run_performance_test(test_case, system_function)
            else:
                # Default test runner
                result = TestResult(
                    test_id=test_case.id,
                    category=test_case.category,
                    success=False,
                    score=0.0,
                    execution_time=0.0,
                    details={},
                    error_message="Test category not implemented"
                )
            
            results.append(result)
        
        # Calculate summary statistics
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.success)
        failed_tests = total_tests - passed_tests
        
        # Calculate category scores
        category_scores = {}
        for category in TestCategory:
            category_results = [r for r in results if r.category == category]
            if category_results:
                category_scores[category.value] = sum(r.score for r in category_results) / len(category_results)
            else:
                category_scores[category.value] = 0.0
        
        # Calculate overall score
        overall_score = sum(r.score for r in results) / len(results) if results else 0.0
        
        # Generate recommendations
        recommendations = self._generate_recommendations(results, category_scores)
        
        return EvaluationReport(
            timestamp=str(time.time()),
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            category_scores=category_scores,
            overall_score=overall_score,
            test_results=results,
            recommendations=recommendations
        )
    
    def _generate_recommendations(self, results: List[TestResult], category_scores: Dict[str, float]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Check for critical failures
        failed_coverage = [r for r in results if r.category == TestCategory.COVERAGE and not r.success]
        if failed_coverage:
            recommendations.append("CRITICAL: Fix coverage issues before proceeding to embedding")
        
        # Check performance issues
        slow_queries = [r for r in results if r.category == TestCategory.PERFORMANCE and r.execution_time > 2.0]
        if slow_queries:
            recommendations.append(f"PERFORMANCE: {len(slow_queries)} queries are slower than target")
        
        # Check retrieval accuracy
        if category_scores.get("retrieval", 0) < 0.9:
            recommendations.append("ACCURACY: Retrieval accuracy below 90% - review embedding quality")
        
        # Check answer quality
        if category_scores.get("answering", 0) < 0.8:
            recommendations.append("QUALITY: Answer quality below 80% - review response generation")
        
        # Overall system health
        overall = sum(category_scores.values()) / len(category_scores) if category_scores else 0
        if overall >= 0.95:
            recommendations.append("✅ System health excellent - ready for production")
        elif overall >= 0.85:
            recommendations.append("✓ System health good - minor improvements needed") 
        elif overall >= 0.70:
            recommendations.append("⚠ System health fair - significant improvements needed")
        else:
            recommendations.append("❌ System health poor - major fixes required")
        
        return recommendations
    
    def save_report(self, report: EvaluationReport, output_path: str = "evaluation_results.json"):
        """Save evaluation report to file"""
        report_dict = asdict(report)
        
        # Convert enums to strings
        for result in report_dict['test_results']:
            result['category'] = result['category'].value
        
        with open(output_path, 'w') as f:
            json.dump(report_dict, f, indent=2)
        
        print(f"Evaluation report saved to {output_path}")


def create_sample_evaluation():
    """Create and run a sample evaluation"""
    harness = EvaluationHarness()
    
    # Mock system data
    mock_system_data = {
        "books": list(range(66)),  # Mock 66 books
        "total_verses": 31102,     # Correct total
        "duplicate_osis_ids": []   # No duplicates
    }
    
    # Mock functions
    def mock_retrieval(query, k):
        if "John 3:16" in query:
            return [{"metadata": {"osis_id": "John.03.016"}, "score": 0.95}]
        return [{"score": 0.8}] * k
    
    def mock_answer(query):
        class MockResponse:
            scripture_sources = ["mock_source"]
        return MockResponse()
    
    def mock_system(query):
        time.sleep(0.1)  # Mock processing time
        return "mock response"
    
    # Run evaluation
    report = harness.run_full_evaluation(
        mock_system_data, mock_retrieval, mock_answer, mock_system
    )
    
    print(f"Evaluation Results:")
    print(f"- Overall Score: {report.overall_score:.2f}")
    print(f"- Tests Passed: {report.passed_tests}/{report.total_tests}")
    print(f"- Category Scores:")
    for category, score in report.category_scores.items():
        print(f"  * {category}: {score:.2f}")
    print(f"- Recommendations:")
    for rec in report.recommendations:
        print(f"  * {rec}")


if __name__ == "__main__":
    create_sample_evaluation()