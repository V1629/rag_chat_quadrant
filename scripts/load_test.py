#!/usr/bin/env python3
"""
Simple load test script for the PDF RAG API.
This is a bonus feature for testing system performance.
"""

import asyncio
import aiohttp
import time
import json
import uuid
from typing import List, Dict
import argparse

class LoadTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session_id = str(uuid.uuid4())
        self.chat_session_id = None
        
    async def create_user_and_session(self, session: aiohttp.ClientSession) -> bool:
        """Create user and chat session"""
        try:
            # Create user
            async with session.post(f"{self.base_url}/api/users", 
                                   params={"session_id": self.session_id}) as resp:
                if resp.status != 200:
                    return False
            
            # Create chat session
            async with session.post(f"{self.base_url}/api/sessions",
                                   params={"session_id": self.session_id},
                                   json={"session_name": f"Load Test {self.session_id[:8]}"}) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.chat_session_id = data["id"]
                    return True
                return False
        except Exception as e:
            print(f"Error creating user/session: {e}")
            return False
    
    async def send_chat_message(self, session: aiohttp.ClientSession, message: str) -> Dict:
        """Send a chat message and measure response time"""
        start_time = time.time()
        
        try:
            payload = {
                "message": message,
                "session_id": self.chat_session_id,
                "top_k": 5,
                "only_answer_if_sources": False
            }
            
            async with session.post(f"{self.base_url}/api/chat", 
                                   json=payload) as resp:
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # Convert to ms
                
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "success": True,
                        "response_time_ms": response_time,
                        "sources_count": len(data.get("sources", [])),
                        "message_length": len(data.get("message", ""))
                    }
                else:
                    return {
                        "success": False,
                        "response_time_ms": response_time,
                        "error": f"HTTP {resp.status}"
                    }
        except Exception as e:
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            return {
                "success": False,
                "response_time_ms": response_time,
                "error": str(e)
            }
    
    async def health_check(self, session: aiohttp.ClientSession) -> bool:
        """Check if the API is healthy"""
        try:
            async with session.get(f"{self.base_url}/health") as resp:
                return resp.status == 200
        except:
            return False

async def run_concurrent_requests(base_url: str, num_requests: int, concurrency: int) -> List[Dict]:
    """Run concurrent chat requests"""
    
    # Test queries
    test_queries = [
        "What is the main topic of the documents?",
        "Can you summarize the key points?",
        "What are the most important findings?",
        "How does this relate to artificial intelligence?",
        "What conclusions can be drawn from the data?",
        "What are the recommendations mentioned?",
        "Can you explain the methodology used?",
        "What are the limitations discussed?",
        "How does this compare to other studies?",
        "What future work is suggested?"
    ]
    
    async with aiohttp.ClientSession() as session:
        # Create a load tester instance
        tester = LoadTester(base_url)
        
        # Check health first
        if not await tester.health_check(session):
            print("❌ API health check failed!")
            return []
        
        print("✅ API is healthy")
        
        # Setup user and session
        if not await tester.create_user_and_session(session):
            print("❌ Failed to create user and session!")
            return []
        
        print(f"✅ Created test session: {tester.chat_session_id}")
        
        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(concurrency)
        
        async def bounded_request(query_idx: int):
            async with semaphore:
                query = test_queries[query_idx % len(test_queries)]
                return await tester.send_chat_message(session, query)
        
        # Run concurrent requests
        print(f"🚀 Running {num_requests} requests with concurrency {concurrency}...")
        start_time = time.time()
        
        tasks = [bounded_request(i) for i in range(num_requests)]
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"⏱️  Total time: {total_time:.2f}s")
        print(f"📊 Requests per second: {num_requests / total_time:.2f}")
        
        return results

def analyze_results(results: List[Dict]):
    """Analyze and display load test results"""
    if not results:
        print("❌ No results to analyze")
        return
    
    successful_requests = [r for r in results if r["success"]]
    failed_requests = [r for r in results if not r["success"]]
    
    print(f"\n📈 LOAD TEST RESULTS")
    print(f"{'='*50}")
    print(f"Total requests: {len(results)}")
    print(f"Successful: {len(successful_requests)} ({len(successful_requests)/len(results)*100:.1f}%)")
    print(f"Failed: {len(failed_requests)} ({len(failed_requests)/len(results)*100:.1f}%)")
    
    if successful_requests:
        response_times = [r["response_time_ms"] for r in successful_requests]
        response_times.sort()
        
        print(f"\n⏱️  RESPONSE TIMES (ms)")
        print(f"Min: {min(response_times):.1f}")
        print(f"Max: {max(response_times):.1f}")
        print(f"Mean: {sum(response_times)/len(response_times):.1f}")
        print(f"Median: {response_times[len(response_times)//2]:.1f}")
        print(f"95th percentile: {response_times[int(len(response_times)*0.95)]:.1f}")
        print(f"99th percentile: {response_times[int(len(response_times)*0.99)]:.1f}")
        
        # Sources analysis
        sources_counts = [r.get("sources_count", 0) for r in successful_requests]
        print(f"\n📚 SOURCES RETRIEVED")
        print(f"Average sources per response: {sum(sources_counts)/len(sources_counts):.1f}")
        print(f"Max sources: {max(sources_counts) if sources_counts else 0}")
        
        # Message length analysis
        message_lengths = [r.get("message_length", 0) for r in successful_requests]
        print(f"\n📝 RESPONSE LENGTHS")
        print(f"Average response length: {sum(message_lengths)/len(message_lengths):.0f} chars")
        print(f"Max response length: {max(message_lengths) if message_lengths else 0} chars")
    
    if failed_requests:
        print(f"\n❌ FAILURES")
        error_counts = {}
        for req in failed_requests:
            error = req.get("error", "Unknown")
            error_counts[error] = error_counts.get(error, 0) + 1
        
        for error, count in error_counts.items():
            print(f"{error}: {count} occurrences")

async def main():
    parser = argparse.ArgumentParser(description="Load test the PDF RAG API")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--requests", type=int, default=20, help="Number of requests to send")
    parser.add_argument("--concurrency", type=int, default=5, help="Concurrent requests")
    
    args = parser.parse_args()
    
    print(f"🧪 PDF RAG API Load Test")
    print(f"URL: {args.url}")
    print(f"Requests: {args.requests}")
    print(f"Concurrency: {args.concurrency}")
    print(f"{'='*50}")
    
    results = await run_concurrent_requests(args.url, args.requests, args.concurrency)
    analyze_results(results)

if __name__ == "__main__":
    asyncio.run(main())
