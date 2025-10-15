#!/usr/bin/env python3
"""
Exam Question Evaluator for CompTIA Security+ RAG System
Handles parsing and evaluation of scenario-based exam questions
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from rag_retriever import RAGRetriever
from llm_engine import LLMEngine


@dataclass
class ExamQuestion:
    """Structured representation of an exam question"""
    id: str
    scenario: str
    question: str
    options: List[str]  # List of option texts (unlabeled)
    correct_answer: str
    explanation: Optional[str] = None
    chapter: Optional[str] = None


class ExamQuestionParser:
    """Parse exam questions from text format"""

    @staticmethod
    def parse_question(text: str, question_id: str = None) -> ExamQuestion:
        """
        Parse a single exam question from text

        Supports both labeled and unlabeled formats:

        Labeled format:
        [Scenario...]
        [Question?]
        A. Option A
        B. Option B
        Correct answer: A

        Unlabeled format:
        [Scenario...]
        [Question?]
        answer
        Option 1 text
        Option 2 text
        """
        # Split into lines
        lines = text.strip().split('\n')

        # Find sections
        scenario_lines = []
        question_lines = []
        options_list = []
        correct_answer = None
        explanation_lines = []

        current_section = "scenario"
        option_mode = None  # Will be "labeled" or "unlabeled"

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # Check if it's a labeled option (A., B., C., D. or 1., 2., 3., 4.)
            labeled_option_match = re.match(r'^([A-D]|[1-4])\.\s*(.+)$', line)
            if labeled_option_match and current_section in ["question", "options"]:
                current_section = "options"
                option_mode = "labeled"
                _, text = labeled_option_match.groups()
                options_list.append(text)
                continue

            # Check if it's the correct answer line
            answer_match = re.match(r'^(?:Correct answer|Answer):\s*(.+)$', line, re.IGNORECASE)
            if answer_match:
                current_section = "explanation"
                correct_answer = answer_match.group(1).strip()
                continue

            # Check if this line says "answer" alone (marker for unlabeled options)
            if line.lower() == "answer" and current_section == "question":
                current_section = "options"
                option_mode = "unlabeled"
                continue

            # Add to appropriate section
            if current_section == "scenario":
                # Check if this line looks like a question (ends with ?)
                if line.endswith('?'):
                    current_section = "question"
                    question_lines.append(line)
                else:
                    scenario_lines.append(line)
            elif current_section == "question":
                question_lines.append(line)
            elif current_section == "options":
                # In unlabeled mode, treat each non-empty line as an option
                if option_mode == "unlabeled" and not answer_match:
                    options_list.append(line)
            elif current_section == "explanation":
                explanation_lines.append(line)

        # Assemble sections
        scenario = ' '.join(scenario_lines).strip()
        question = ' '.join(question_lines).strip()
        explanation = ' '.join(explanation_lines).strip() if explanation_lines else None

        return ExamQuestion(
            id=question_id or "unknown",
            scenario=scenario,
            question=question,
            options=options_list,
            correct_answer=correct_answer,
            explanation=explanation
        )


class ExamEvaluator:
    """Evaluate RAG system performance on exam questions"""

    def __init__(
        self,
        collection_name: str = "comptia_security_plus",
        embedding_dim: int = 1536,
        embedding_model: str = "text-embedding-3-small",
        llm_model: str = "gemini-2.5-pro"
    ):
        """Initialize evaluator with retriever and LLM engine"""
        print("=" * 60)
        print("INITIALIZING EXAM EVALUATOR")
        print("=" * 60)

        self.retriever = RAGRetriever(
            collection_name=collection_name,
            embedding_dim=embedding_dim,
            model=embedding_model
        )

        self.llm_engine = LLMEngine(model=llm_model)

        # Track results
        self.results = []

        print("=" * 60)
        print("✅ Exam Evaluator ready")
        print("=" * 60)

    def evaluate_question(
        self,
        question: ExamQuestion,
        k: int = 10,  # Increased from 7 for better context with 2321 chunks
        chapter_filter: Optional[str] = None,
        verbose: bool = True
    ) -> Dict:
        """
        Evaluate a single exam question

        Returns:
            Dict with evaluation results including:
            - correct: bool
            - predicted_answer: str
            - actual_answer: str
            - reasoning: str
            - confidence: str
        """
        if verbose:
            print(f"\n{'='*80}")
            print(f"EVALUATING: {question.id}")
            print(f"{'='*80}")
            print(f"Scenario: {question.scenario[:100]}...")
            print(f"Question: {question.question[:100]}...")

        # Retrieve context
        results, context = self.retriever.retrieve_for_exam_question(
            scenario=question.scenario,
            question=question.question,
            options=question.options,
            k=k,
            chapter_filter=chapter_filter or question.chapter
        )

        if verbose:
            print(f"\n📚 Retrieved {len(results)} unique documents")

        # Generate answer
        response = self.llm_engine.answer_exam_question(
            scenario=question.scenario,
            question=question.question,
            options=question.options,
            context=context
        )

        predicted = response["answer"]
        correct = predicted == question.correct_answer

        if verbose:
            print(f"\n🤖 Predicted: {predicted}")
            print(f"✓  Actual: {question.correct_answer}")
            print(f"{'✅ CORRECT' if correct else '❌ INCORRECT'}")

        result = {
            "question_id": question.id,
            "correct": correct,
            "predicted_answer": predicted,
            "actual_answer": question.correct_answer,
            "reasoning": response["reasoning"],
            "confidence": response["confidence"],
            "num_sources": len(results)
        }

        self.results.append(result)
        return result

    def evaluate_questions(
        self,
        questions: List[ExamQuestion],
        k: int = 10,  # Increased from 7 for better context with 2321 chunks
        chapter_filter: Optional[str] = None,
        verbose: bool = True
    ) -> Dict:
        """
        Evaluate multiple exam questions

        Returns:
            Summary statistics
        """
        print(f"\n{'='*80}")
        print(f"EVALUATING {len(questions)} EXAM QUESTIONS")
        print(f"{'='*80}")

        self.results = []

        for i, question in enumerate(questions, 1):
            print(f"\n[{i}/{len(questions)}]")
            self.evaluate_question(question, k=k, chapter_filter=chapter_filter, verbose=verbose)

            if i < len(questions) and verbose:
                print("\n" + "-" * 80)

        # Calculate statistics
        total = len(self.results)
        correct = sum(1 for r in self.results if r["correct"])
        accuracy = (correct / total * 100) if total > 0 else 0

        # Usage stats
        usage = self.llm_engine.get_usage_stats()

        summary = {
            "total_questions": total,
            "correct": correct,
            "incorrect": total - correct,
            "accuracy": accuracy,
            "usage": usage,
            "cost_per_question": usage["total_cost"] / total if total > 0 else 0
        }

        print(f"\n{'='*80}")
        print("EVALUATION SUMMARY")
        print(f"{'='*80}")
        print(f"Total Questions: {total}")
        print(f"Correct: {correct}")
        print(f"Incorrect: {total - correct}")
        print(f"Accuracy: {accuracy:.1f}%")
        print(f"\n💰 Cost Statistics:")
        print(f"   Total cost: ${usage['total_cost']:.4f}")
        print(f"   Cost per question: ${summary['cost_per_question']:.4f}")
        print(f"   Input tokens: {usage['total_input_tokens']:,}")
        print(f"   Output tokens: {usage['total_output_tokens']:,}")
        print(f"{'='*80}")

        return summary

    def get_results(self) -> List[Dict]:
        """Get all evaluation results"""
        return self.results

    def print_detailed_results(self):
        """Print detailed results for each question"""
        for i, result in enumerate(self.results, 1):
            print(f"\n{'='*80}")
            print(f"Question {i}: {result['question_id']}")
            print(f"{'='*80}")
            print(f"Status: {'✅ CORRECT' if result['correct'] else '❌ INCORRECT'}")
            print(f"Predicted: {result['predicted_answer']}")
            print(f"Actual: {result['actual_answer']}")
            print(f"Confidence: {result['confidence']}")
            print(f"Sources: {result['num_sources']}")
            print(f"\nReasoning:")
            print("-" * 80)
            print(result['reasoning'])


def main():
    """Test the exam evaluator with sample questions"""

    # Sample exam questions (from your examples)
    questions = [
        ExamQuestion(
            id="Q1",
            scenario="A large multinational corporation has recently experienced a significant data breach. The breach was detected by an external cybersecurity firm, and the corporation's IT department was unable to prevent or detect the breach in its early stages. The CEO wants to ensure that such a breach does not happen again and is considering several options to enhance the company's security posture.",
            question="Which of the following options would be the MOST effective in preventing and detecting future data breaches?",
            options={
                "A": "Implementing a dedicated Computer Incident Response Team (CIRT)",
                "B": "Hiring an external cybersecurity firm to conduct regular penetration testing",
                "C": "Conducting regular cybersecurity training for all employees",
                "D": "Increasing the budget for the IT department to purchase more advanced security software"
            },
            correct_answer="A",
            chapter="1"
        ),
        ExamQuestion(
            id="Q2",
            scenario="You are the Chief Information Security Officer (CISO) at a tech company. Your company is facing issues with silos between the development and operations teams, leading to inefficiencies and security vulnerabilities.",
            question="Which approach should you adopt to encourage collaboration and integrate security considerations at every stage of software development and deployment?",
            options={
                "A": "Outsourcing security to a third-party vendor",
                "B": "Adopting a Development and Operations (DevOps) approach",
                "C": "Implementing a new security policy",
                "D": "Establishing a Security Operations Center (SOC)"
            },
            correct_answer="B",
            chapter="1"
        )
    ]

    # Initialize evaluator
    evaluator = ExamEvaluator()

    # Evaluate questions
    summary = evaluator.evaluate_questions(questions, k=7, verbose=True)

    # Print detailed results
    print("\n" + "=" * 80)
    print("DETAILED RESULTS")
    print("=" * 80)
    evaluator.print_detailed_results()


if __name__ == "__main__":
    main()
