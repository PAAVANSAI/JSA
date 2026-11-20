import argparse
import sys
import logging
from pipeline.inbox import UnifiedInboxManager
from models.job import JobPost

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

def run():
    parser = argparse.ArgumentParser(description="Job Search Automation (JSA) Runner")
    parser.add_argument("--keywords", nargs="+", default=["AWS", "Cloud", "DevOps"], help="Search target keywords")
    parser.add_argument("--locations", nargs="+", default=["Hyderabad", "Bengaluru", "Remote"], help="Target cities")
    parser.add_argument("--sweep-all", action="store_true", help="Run 5-query sweep across AWS, DevOps, Fresher, and Cloud Support")
    parser.add_argument("--test-mock", action="store_true", help="Inject sample jobs across multiple layers to verify deduplication and pipeline")

    args = parser.parse_args()

    print("\n" + "="*60)
    print("🚀 JOB SEARCH AUTOMATION (JSA) - 6-LAYER UNIFIED PIPELINE")
    print("="*60)

    inbox = UnifiedInboxManager()

    if args.test_mock:
        print("\n🧪 Running mock test verification for deduplication and best-link resolution...")
        mock_posts = [
            # Same job on Layer 2 (Indeed) and Layer 1 (Greenhouse Direct)
            JobPost(
                title="Cloud Support Engineer (AWS)",
                company="Razorpay",
                location="Bengaluru, India",
                apply_url="https://job-boards.greenhouse.io/razorpaysoftwareprivatelimited/jobs/4745511005",
                source_layer=1,
                source_name="Career Page: Greenhouse (Razorpay)",
                description="Looking for an AWS fresher / Cloud Support Trainee with knowledge of EC2, S3, Linux, Docker."
            ),
            JobPost(
                title="Cloud Support Engineer - AWS Fresher",
                company="Razorpay",
                location="Bengaluru",
                apply_url="https://www.indeed.co.in/viewjob?jk=indeed_copy_456",
                source_layer=2,
                source_name="JobSpy: Indeed",
                description="Razorpay is urgently hiring Cloud Support Engineer. Knowledge of AWS, Linux."
            ),
            # Scam posting example
            JobPost(
                title="DevOps Fresher Urgent - Pay Rs 500 Registration Fee",
                company="Shady Placement Consultancy",
                location="Hyderabad",
                apply_url="https://wa.me/919999999999",
                source_layer=6,
                source_name="Telegram Job Channel",
                description="Immediate joining. Contact on WhatsApp. Mandatory registration fee Rs 500."
            )
        ]
        
        print(f"📥 Ingested {len(mock_posts)} sample posts across Layers 1, 2, and 6.")
        
        # Test deduplicator
        unique = inbox.deduplicator.deduplicate_batch(mock_posts)
        print(f"✨ Deduplication result: {len(mock_posts)} raw posts reduced to {len(unique)} unique postings.")
        
        from pipeline.company_intelligence import CompanyIntelligence
        from pipeline.cold_pitch_generator import ColdPitchGenerator
        qualified_batch = []
        for job in unique:
            inbox.scam_detector.evaluate(job)
            score = inbox.scorer.score_job(job)
            print(f"\n- [{job.company}] {job.title}")
            print(f"  Source: {job.source_name} (Best link: {job.apply_url})")
            print(f"  Match Score: {score}/100")
            print(f"  Scam Score: {job.scam_score} (Reasons: {job.scam_reasons})")
            
            if score >= 60 and job.scam_score < 0.5:
                intel = CompanyIntelligence.enrich_job(job)
                pitch = ColdPitchGenerator.generate_pitch(job)
                pdf_path = inbox.pdf_builder.generate_pdf(job)
                inbox.tracker.log_application(job, intel['salary'], pitch['linkedin_search_url'])
                inbox.deduplicator.mark_notified(job)
                print(f"  📄 Tailored PDF resume built: {pdf_path}")
                print(f"  💰 Salary: {intel['salary']} | {intel['rating']}")
                print(f"  💬 1-Tap Cold DM: {pitch['linkedin_dm'][:60]}...")
                qualified_batch.append({
                    "job": job,
                    "intel": intel,
                    "pitch": pitch,
                    "pdf_path": pdf_path
                })

        if qualified_batch:
            inbox.notifier.send_digest_alert(qualified_batch)
            top_job = qualified_batch[0]
            caption = f"📄 <b>Tailored Resume: {top_job['job'].company}</b>\nRole: {top_job['job'].title} ({top_job['job'].match_score:.0f}% match)"
            inbox.notifier.send_pdf_document(top_job["pdf_path"], caption)

        print("\n✅ Mock pipeline verification completed successfully.")
        return

    # Execution cycle
    if args.sweep_all:
        print("🔍 Executing multi-query sweep across 5 AWS/DevOps entry-level search sets...")
        summary = inbox.run_sweep()
    else:
        summary = inbox.run_cycle(keywords=args.keywords, locations=args.locations)
    print("\n" + "="*60)
    print("📊 PIPELINE CYCLE SUMMARY:")
    print(f"  Total raw jobs harvested: {summary['total_harvested']}")
    print(f"  Unique new jobs discovered: {summary['unique_new_jobs']}")
    print(f"  Qualified jobs notified: {summary['notified_jobs']}")
    print("="*60)

if __name__ == "__main__":
    run()
