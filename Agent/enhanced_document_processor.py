#!/usr/bin/env python3
import os
import json
import time
import logging
import argparse
import subprocess
import glob
import re
from datetime import datetime
from dotenv import load_dotenv
import hashlib
import ipfshttpclient
import networkx as nx
from pathlib import Path
from prometheus_client import Gauge, Counter
from opentelemetry import trace
from functools import lru_cache
import redis
from vector_search import upsert_document, similar_docs
import sys
import schedule
import concurrent.futures
from typing import Dict, List, Optional, Union, Type, Tuple
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta

# Add the parent directory to the system path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the distributed storage module
from ipfs_storage.distributed_storage import DistributedStorage
from Agent.job_queue import DistributedJobQueue

# Import our custom modules
from phi3_wrapper import Phi3Processor
from llm_client import LLMClient, LLMType
from job_queue import dequeue_document
from extraction.locality_detector import add_locality_relations_to_graph
from graph_db.schema import NodeType, EdgeType, EDGE_TIMESTAMP, SCHEMA_VERSION
from graph_db.schema import NODE_LICENSE, NODE_SOURCE_URL, NODE_VALUE, NODE_UNIT
from graph_db.edge_mapping import canonical_edge
from utils.prompt_hot_reload import start as start_prompt_hot_reload
from utils.chunking import chunk_document
from utils.merger import smart_union

# Import telemetry ingestors
from telemetry_ingestors import (
    BaseTelemetryIngestor,
    TrafficDataIngestor,
    WeatherDataIngestor,
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("document_processor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("document_processor")

# Load environment variables
load_dotenv()

# Configuration
WEB_API_ENDPOINT = os.getenv('WEB_API_ENDPOINT', 'https://example.com/api/ipfs_hashes.php')
API_KEY = os.getenv('API_KEY')
DATA_DIR = 'data'
ANALYSIS_DIR = os.path.join(DATA_DIR, 'analysis')
PROCESSED_DIR = os.path.join(DATA_DIR, 'processed')
DB_PATH = os.path.join(DATA_DIR, 'ipfs_hashes.json')
GRAPH_DATA_PATH = os.path.join(DATA_DIR, 'graph_data.json')
DOCUMENT_EXTENSIONS = ['.txt', '.pdf', '.docx', '.doc', '.rtf', '.json', '.csv']
GRAPH_IPNS_KEY = os.getenv('GRAPH_IPNS_KEY', 'self')

# Metrics
PROCESSING_IN_FLIGHT = Gauge('processing_in_flight', 'Current number of documents being processed')
TELEMETRY_READINGS_INGESTED = Counter('telemetry_readings_ingested_total', 'Total number of telemetry readings ingested', ['source'])
TELEMETRY_READINGS_REJECTED = Counter('telemetry_readings_rejected_total', 'Total number of telemetry readings rejected', ['reason'])
COMPUTE_COST = Counter('compute_cost_dollars', 'Estimated compute cost in dollars')
GPU_UTILIZATION = Gauge('gpu_utilization_percent', 'GPU utilization percentage', ['gpu_id'])
BATCH_SIZE = Gauge('batch_size_current', 'Current processing batch size')
PROCESSING_QUEUE_SIZE = Gauge('processing_queue_size', 'Number of items in processing queue')

@dataclass
class ComputeConfig:
    """Configuration for compute resources and cost tracking."""
    cost_per_hour: float = 50.0  # Cost in dollars per hour
    gpu_count: int = 16          # Number of H100 GPUs
    start_time: datetime = None   # When processing started
    total_cost: float = 0.0      # Running total cost
    max_budget: float = float('inf')  # Maximum budget in dollars
    idle_shutdown_minutes: int = 10  # Shutdown after N minutes of idle time

class EnhancedDocumentProcessor:
    def __init__(self, 
                 llm_type=None, 
                 model_path=None, 
                 llama_path=None, 
                 api_base=None,
                 api_key=None,
                 model_name=None,
                 threads=None,  # Now optional, will detect GPU count
                 ctx_size=32768,  # Increased for DeepSeek models
                 batch_size=32,   # Optimized for H100s
                 storage_path="/mnt/storage/temp_storage", 
                 redis_url="redis://localhost:6379/0",
                 replication_factor=2, 
                 storage_capacity_gb=2000.0,  # Increased for H100 cluster
                 temperature=0.2,
                 max_parallel_jobs=32,
                 compute_config=None):
        """Initialize the document processor with LLM settings.
        
        Args:
            llm_type: Type of LLM to use (phi3, openai, openai_compatible)
            model_path: Path to the local model file (for phi3)
            llama_path: Path to the llama.cpp executable (for phi3)
            api_base: Base URL for API calls (for openai/openai_compatible)
            api_key: API key for model access (for openai/openai_compatible)
            model_name: Model name/identifier (for openai/openai_compatible)
            threads: Number of threads for inference
            ctx_size: Context size for the model
            batch_size: Batch size for processing
            storage_path: Path for temporary document storage
            redis_url: Redis connection string for coordination
            replication_factor: Number of replicas for document storage
            storage_capacity_gb: Local storage capacity in GB
            temperature: Model temperature setting
        """
        # Initialize parameters
        self.llm_type = llm_type or os.getenv("LLM_TYPE", "ollama")
        self.model_path = model_path
        self.llama_path = llama_path
        self.api_base = api_base or os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model_name or os.getenv("LLM_MODEL", "deepseek-r1:70b")
        
        # Auto-detect GPU count and optimize threads
        detected_gpus = self._detect_gpu_count()
        self.threads = threads or detected_gpus * 2  # 2 threads per GPU is optimal for H100s
        self.ctx_size = ctx_size
        self.batch_size = batch_size
        self.temperature = temperature
        self.max_parallel_jobs = max_parallel_jobs
        
        # Initialize compute cost tracking
        self.compute_config = compute_config or ComputeConfig(
            gpu_count=detected_gpus,
            start_time=datetime.now()
        )
        
        # Thread pool for parallel processing
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_parallel_jobs
        )
        
        # Processing queue and lock
        self.job_queue_lock = threading.Lock()
        self.cost_lock = threading.Lock()
        
        # Initialize LLM client
        self.llm_client = LLMClient(
            llm_type=self.llm_type,
            model_path=self.model_path,
            llama_executable=self.llama_path,
            api_key=self.api_key,
            api_base=self.api_base,
            model=self.model_name,
            threads=self.threads,
            ctx_size=self.ctx_size,
            temperature=self.temperature
        )
        
        # For backward compatibility - existing code uses Phi3Processor directly
        if self.llm_type == "phi3":
            self.phi3_processor = Phi3Processor(
                model_path=self.model_path,
                llama_executable=self.llama_path,
                threads=self.threads,
                ctx_size=self.ctx_size
            )
        else:
            # Create a compatibility layer to redirect to the llm_client
            self.phi3_processor = PhiCompatLayer(self.llm_client)
        
        # Initialize distributed storage
        self.storage = DistributedStorage(
            redis_url=redis_url,
            local_storage_path=storage_path,
            replication_factor=replication_factor,
            local_storage_capacity_gb=storage_capacity_gb
        )
        
        # Set up local storage for telemetry data that can't go on IPFS
        self.telemetry_storage_path = os.path.join(
            os.path.dirname(storage_path),
            'telemetry_data'
        )
        os.makedirs(self.telemetry_storage_path, exist_ok=True)
        
        # Initialize job queue
        self.job_queue = DistributedJobQueue(redis_url=redis_url)
        
        # Register as a worker
        self.worker_id = self.job_queue.register_worker(capabilities={
            "cpu_count": os.cpu_count(),
            "gpu_available": self._check_gpu_available(),
            "model_type": self.llm_type,
            "model": self.model_name if self.llm_type != "phi3" else "phi-3",
            "threads": threads,
            "ctx_size": ctx_size,
            "schema_version": SCHEMA_VERSION
        })
        
        # Initialize telemetry ingestors
        self.telemetry_ingestors = self._init_telemetry_ingestors()
        
        logger.info(f"Initialized document processor with worker ID: {self.worker_id}")
        logger.info(f"Using LLM type: {self.llm_type}, Model: {self.model_name if self.llm_type != 'phi3' else 'phi-3'}")
        
    def _detect_gpu_count(self) -> int:
        """Detect the number of available GPUs for inference."""
        try:
            import torch
            if torch.cuda.is_available():
                return torch.cuda.device_count()
            return 0
        except ImportError:
            # Try with nvidia-smi as fallback
            try:
                import subprocess
                output = subprocess.check_output("nvidia-smi -L", shell=True).decode()
                # Count number of lines which should equal number of GPUs
                return len([line for line in output.split('\n') if line.strip().startswith('GPU ')])
            except:
                # Default to 16 for H100 cluster if detection fails
                logger.warning("Could not detect GPU count, defaulting to 16 H100s")
                return 16
    
    def _check_gpu_available(self) -> bool:
        """Check if GPU is available for inference."""
        return self._detect_gpu_count() > 0
        
    def _get_gpu_utilization(self) -> Dict[int, float]:
        """Get current GPU utilization for all GPUs.
        
        Returns:
            Dictionary mapping GPU ID to utilization percentage
        """
        try:
            import subprocess
            output = subprocess.check_output(
                "nvidia-smi --query-gpu=index,utilization.gpu --format=csv,noheader,nounits", 
                shell=True
            ).decode()
            
            # Parse the output
            result = {}
            for line in output.strip().split('\n'):
                if line.strip():
                    gpu_id, util = line.split(',')
                    result[int(gpu_id)] = float(util)
                    # Update metrics
                    GPU_UTILIZATION.labels(gpu_id=gpu_id).set(float(util))
            
            return result
        except Exception as e:
            logger.warning(f"Error getting GPU utilization: {e}")
            return {}
    
    def _update_compute_cost(self, duration_seconds: float = None):
        """Update the computed cost based on elapsed time.
        
        Args:
            duration_seconds: Duration in seconds, or None to calculate from start time
        """
        with self.cost_lock:
            if duration_seconds is None and self.compute_config.start_time:
                # Calculate elapsed time
                elapsed = datetime.now() - self.compute_config.start_time
                duration_seconds = elapsed.total_seconds()
            
            if duration_seconds:
                # Calculate cost: cost_per_hour * (seconds / 3600)
                hourly_cost = self.compute_config.cost_per_hour
                cost = hourly_cost * (duration_seconds / 3600)
                
                # Update total
                self.compute_config.total_cost += cost
                
                # Update metric
                COMPUTE_COST.inc(cost)
                
                logger.info(f"Compute cost: ${cost:.2f} for {duration_seconds/60:.1f} minutes. "  
                           f"Total: ${self.compute_config.total_cost:.2f}")
                
                # Check against budget
                if self.compute_config.total_cost >= self.compute_config.max_budget:
                    logger.warning(f"Budget limit reached (${self.compute_config.max_budget})! Shutting down.")
                    # Initiate graceful shutdown
                    threading.Thread(target=self._graceful_shutdown).start()
    
    def _init_telemetry_ingestors(self) -> Dict[str, BaseTelemetryIngestor]:
        """Initialize telemetry data ingestors.
        
        Returns:
            Dictionary of ingestor instances by name
        """
        # Determine which data should use IPFS vs local storage
        # We'll use local storage for high-frequency telemetry data
        # that would create too many small files in IPFS
        high_frequency_types = ['weather', 'traffic']
        
        ingestors = {}
        
        # Traffic data ingestor
        traffic_ingestor = TrafficDataIngestor(
            graph_client=self.graph_client,
            storage_client=self.storage if 'traffic' not in high_frequency_types else None,
            store_in_ipfs='traffic' not in high_frequency_types,
            local_storage_path=os.path.join(self.telemetry_storage_path, 'traffic')
        )
        ingestors['traffic'] = traffic_ingestor
        
        # Weather data ingestor
        weather_ingestor = WeatherDataIngestor(
            graph_client=self.graph_client,
            storage_client=self.storage if 'weather' not in high_frequency_types else None,
            store_in_ipfs='weather' not in high_frequency_types,
            local_storage_path=os.path.join(self.telemetry_storage_path, 'weather')
        )
        ingestors['weather'] = weather_ingestor
        
        logger.info(f"Initialized {len(ingestors)} telemetry ingestors")
        return ingestors

    def process_document(self, document_path, metadata=None):
        """Process a document and store results.
        
        Args:
            document_path: Path to the document file
            metadata: Additional metadata about the document
            
        Returns:
            dict: Processing results with extracted information
        """
        # Store the document in distributed storage
        logger.info(f"Storing document {document_path} in distributed storage")
        storage_info = self.storage.store_file(document_path, metadata)
        file_id = storage_info["file_id"]
        
        # ... existing document processing code ...
        
        # Mark document as complete in IPFS and update storage info
        self.storage.retry_ipfs_uploads()
        
        # Return processing results
        return results
        
    def run(self, mode="worker"):
        """Run the document processor in the specified mode.
        
        Args:
            mode: Operating mode (worker, api, cli, telemetry)
        """
        if mode == "worker":
            self.run_worker()
        elif mode == "api":
            self.run_api()
        elif mode == "cli":
            self.run_cli()
        elif mode == "telemetry":
            self.run_telemetry_ingestors()
        else:
            logger.error(f"Unknown mode: {mode}")
            sys.exit(1)

    def _graceful_shutdown(self):
        """Perform graceful shutdown of the system."""
        logger.warning("Initiating graceful shutdown...")
        
        # Wait for in-flight jobs to complete with timeout
        shutdown_timeout = 300  # 5 minutes max wait
        start_shutdown = time.time()
        
        # Check in-flight jobs
        while PROCESSING_IN_FLIGHT._value.get() > 0:
            elapsed = time.time() - start_shutdown
            if elapsed > shutdown_timeout:
                logger.warning(f"Shutdown timeout after {shutdown_timeout}s. Force exiting.")
                break
            
            logger.info(f"Waiting for {PROCESSING_IN_FLIGHT._value.get()} jobs to complete before shutdown")
            time.sleep(10)
        
        # Shutdown executor
        logger.info("Shutting down thread pool")
        self.executor.shutdown(wait=True, cancel_futures=True)
        
        # Final cost report
        self._update_compute_cost()
        logger.info(f"Final compute cost: ${self.compute_config.total_cost:.2f}")
        
        # Exit the process
        logger.info("Shutdown complete. Exiting.")
        os._exit(0)
    
    def _batch_process_jobs(self, jobs):
        """Process a batch of jobs in parallel.
        
        Args:
            jobs: List of jobs to process
        """
        logger.info(f"Processing batch of {len(jobs)} jobs")
        BATCH_SIZE.set(len(jobs))
        
        # Submit all jobs to thread pool
        futures = []
        for job in jobs:
            PROCESSING_IN_FLIGHT.inc()
            future = self.executor.submit(self.process_job, job)
            futures.append((job, future))
        
        # Wait for completion
        for job, future in futures:
            try:
                result = future.result(timeout=3600)  # 1-hour timeout per job
                logger.info(f"Completed job {job['id']}")
            except Exception as e:
                logger.error(f"Error processing job {job['id']}: {e}", exc_info=True)
            finally:
                PROCESSING_IN_FLIGHT.dec()
        
        # Update cost after batch completion
        self._update_compute_cost()
    
    def run_worker(self):
        """Run in worker mode, processing jobs from the queue."""
        logger.info(f"Starting document processor worker {self.worker_id}")
        logger.info(f"Using {self.model_name} on {self.compute_config.gpu_count} H100 GPUs")
        logger.info(f"Compute cost tracking: ${self.compute_config.cost_per_hour}/hour")
        
        # Initialize cost tracking
        self.compute_config.start_time = datetime.now()
        
        # Schedule telemetry data collection
        self._schedule_telemetry_collection()
        
        # Schedule cost updates
        schedule.every(15).minutes.do(self._update_compute_cost)
        
        # Track last activity time for idle shutdown
        last_activity = time.time()
        idle_threshold = self.compute_config.idle_shutdown_minutes * 60
        
        while True:
            try:
                # Check for idle shutdown
                if time.time() - last_activity > idle_threshold:
                    logger.warning(f"System idle for {self.compute_config.idle_shutdown_minutes} minutes. "  
                                  f"Initiating shutdown to save costs.")
                    self._graceful_shutdown()
                
                # Batch dequeue jobs for efficient processing
                batch_size = min(self.batch_size, self.max_parallel_jobs)
                jobs = []
                
                with self.job_queue_lock:
                    for _ in range(batch_size):
                        job = self.job_queue.dequeue_job()
                        if job:
                            jobs.append(job)
                            PROCESSING_QUEUE_SIZE.inc()
                        else:
                            break
                
                if jobs:
                    # Process the batch
                    last_activity = time.time()
                    self._batch_process_jobs(jobs)
                else:
                    # No jobs available
                    logger.debug("No jobs available, waiting...")
                    # Run pending scheduled jobs (including telemetry)
                    schedule.run_pending()
                    time.sleep(5)
                    continue
                
                # Check for any scheduled tasks
                schedule.run_pending()
                
                # Update GPU metrics periodically
                self._get_gpu_utilization()
            
            except KeyboardInterrupt:
                logger.info("Shutting down worker")
                self._graceful_shutdown()
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}", exc_info=True)
                time.sleep(5)

    def _schedule_telemetry_collection(self):
        """Schedule telemetry data collection at regular intervals."""
        # Traffic data every 15 minutes
        schedule.every(15).minutes.do(self.collect_telemetry_data, 'traffic')
        
        # Weather data every hour
        schedule.every(60).minutes.do(self.collect_telemetry_data, 'weather')
        
        logger.info("Scheduled telemetry data collection")
    
    def collect_telemetry_data(self, ingestor_name):
        """Collect telemetry data from the specified ingestor.
        
        Args:
            ingestor_name: Name of the ingestor to run
            
        Returns:
            True to keep the scheduled job running
        """
        if ingestor_name not in self.telemetry_ingestors:
            logger.error(f"Unknown telemetry ingestor: {ingestor_name}")
            return True
        
        ingestor = self.telemetry_ingestors[ingestor_name]
        logger.info(f"Running telemetry ingestor: {ingestor_name}")
        
        try:
            processed_count = ingestor.run()
            TELEMETRY_READINGS_INGESTED.labels(source=ingestor_name).inc(processed_count)
            logger.info(f"Telemetry ingestor {ingestor_name} processed {processed_count} readings")
        except Exception as e:
            logger.error(f"Error running telemetry ingestor {ingestor_name}: {e}", exc_info=True)
        
        # Return True to keep the scheduled job running
        return True
    
    def run_telemetry_ingestors(self):
        """Run in telemetry mode, collecting data from external sources."""
        logger.info("Starting telemetry data collection")
        
        # Schedule telemetry collection
        self._schedule_telemetry_collection()
        
        # Run immediately once
        for name in self.telemetry_ingestors:
            self.collect_telemetry_data(name)
        
        # Keep running the scheduled jobs
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down telemetry collection")

# Compatibility layer to make LLMClient work with code expecting Phi3Processor
class PhiCompatLayer:
    """Adapter class to make the LLMClient interface compatible with Phi3Processor."""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
    
    def _run_model(self, prompt, max_tokens=1024):
        """Compatibility with Phi3Processor._run_model method."""
        return self.llm_client.generate(prompt, max_tokens)
    
    def extract_coordinates(self, text):
        """Extract coordinates from text."""
        prompt = f"""
Extract all geographic locations and their coordinates from the following text, focusing only on locations in Southeastern Virginia (757 area code). 
If coordinates aren't directly mentioned, don't invent them; just extract the location names.
Return the results as a JSON array of objects with "name", "lat", and "lng" fields.

Text: {text}

JSON Result:
"""
        response = self.llm_client.generate(prompt)
        try:
            # Try to find JSON array in response
            json_match = re.search(r'\[.*?\]', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            return []
        except Exception as e:
            logger.error(f"Error extracting coordinates: {e}")
            return []
    
    # Forward other method calls to the llm_client.generate
    def __getattr__(self, name):
        """Forward any other method calls to a compatible function."""
        def wrapper(*args, **kwargs):
            # If the first arg is a string, assume it's a prompt
            if args and isinstance(args[0], str):
                prompt = args[0]
                # Simulate behavior of Phi3Processor methods by returning specific response formats
                response = self.llm_client.generate(prompt)
                
                # For method names that expect JSON
                if name in ["extract_funding_info", "extract_key_entities", 
                           "extract_project_summary", "extract_classifications"]:
                    try:
                        return json.loads(response)
                    except:
                        logger.error(f"Failed to parse JSON response from {name}")
                        return {}
                
                # For method names that expect arrays
                if name in ["identify_relationships"]:
                    try:
                        json_match = re.search(r'\[.*?\]', response, re.DOTALL)
                        if json_match:
                            return json.loads(json_match.group(0))
                        return []
                    except:
                        return []
                
                # For method names that expect a simple string response
                if name in ["classify_document_type"]:
                    return response.strip()
                
                # Default fallback
                return response
            
            logger.warning(f"Unsupported method call: {name}")
            return None
        return wrapper

def extract_text_from_document(document_path):
    """Extract text from various document formats"""
    extension = os.path.splitext(document_path)[1].lower()
    
    try:
        if extension == '.txt':
            with open(document_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        elif extension == '.json':
            with open(document_path, 'r', encoding='utf-8', errors='ignore') as f:
                data = json.load(f)
                # Handle different JSON structures
                if isinstance(data, dict):
                    # Try common keys that might contain text
                    for key in ['text', 'content', 'body', 'description', 'abstract']:
                        if key in data and isinstance(data[key], str):
                            return data[key]
                    # If no specific key found, convert whole JSON to string
                    return json.dumps(data)
                elif isinstance(data, list):
                    # Join list items if they're strings
                    text_items = [item for item in data if isinstance(item, str)]
                    if text_items:
                        return ' '.join(text_items)
                    # Otherwise convert whole JSON to string
                    return json.dumps(data)
        elif extension == '.pdf':
            # Use pdftotext if available
            try:
                result = subprocess.run(['pdftotext', document_path, '-'], 
                                     capture_output=True, text=True, check=True)
                return result.stdout
            except:
                logger.warning(f"pdftotext not available for {document_path}. Install poppler-utils.")
                return ""
        elif extension in ['.docx', '.doc']:
            # Try using textract if available
            try:
                import textract
                return textract.process(document_path).decode('utf-8', errors='ignore')
            except ImportError:
                logger.warning("textract not available. Install with: pip install textract")
                return ""
        elif extension == '.csv':
            import csv
            text_content = []
            with open(document_path, 'r', encoding='utf-8', errors='ignore') as f:
                csv_reader = csv.reader(f)
                for row in csv_reader:
                    text_content.append(' '.join(row))
            return '\n'.join(text_content)
        else:
            logger.warning(f"Unsupported file format: {extension}")
            return ""

def hash_document(document_path):
    """Add document to IPFS and return the hash"""
    try:
        logger.info(f"Adding document to IPFS: {document_path}")
        result = subprocess.run(['ipfs', 'add', '-q', document_path], 
                             capture_output=True, text=True, check=True)
        ipfs_hash = result.stdout.strip()
        logger.info(f"Document added to IPFS with hash: {ipfs_hash}")
        return ipfs_hash
    except subprocess.CalledProcessError as e:
        logger.error(f"Error hashing document: {e}")
        return None

def is_hash_processed(ipfs_hash):
    """Check if this ipfs_hash already exists in the local database."""
    if not ipfs_hash or not os.path.exists(DB_PATH):
        return False
    try:
        with open(DB_PATH, "r") as f:
            db = json.load(f)
        return any(entry.get("ipfs_hash") == ipfs_hash for entry in db.get("documents", []))
    except Exception:
        return False

def compute_content_hash(text):
    """Return SHA-256 hex digest of the given text (UTF-8)."""
    return hashlib.sha256(text.encode('utf-8', errors='ignore')).hexdigest()

def is_content_hash_processed(content_hash):
    if not content_hash or not os.path.exists(DB_PATH):
        return False
    try:
        with open(DB_PATH, "r") as f:
            db = json.load(f)
        return any(entry.get("content_hash") == content_hash for entry in db.get("documents", []))
    except Exception:
        return False

def update_hash_database(document_path, ipfs_hash=None, analysis=None, content_hash=None):
    """Record the hash and analysis in a local database"""
    try:
        # Load existing database or create new one
        if os.path.exists(DB_PATH):
            with open(DB_PATH, 'r') as f:
                db = json.load(f)
        else:
            db = {'documents': []}
        
        # Add new entry with analysis
        entry = {
            'document': os.path.basename(document_path),
            'timestamp': datetime.now().isoformat()
        }
        
        if ipfs_hash:
            entry['ipfs_hash'] = ipfs_hash
        if content_hash:
            entry['content_hash'] = content_hash
        
        # Add analysis if available
        if analysis:
            entry['analysis'] = analysis
        
        # Avoid duplicates; enrich existing record if necessary
        found = False
        for existing in db['documents']:
            if (ipfs_hash and existing.get('ipfs_hash') == ipfs_hash) or (content_hash and existing.get('content_hash') == content_hash):
                found = True
                if analysis and 'analysis' not in existing:
                    existing['analysis'] = analysis
                    existing['timestamp'] = datetime.now().isoformat()
                break
        
        if not found:
            db['documents'].append(entry)
        
        # Save updated database
        with open(DB_PATH, 'w') as f:
            json.dump(db, f, indent=2)
        
        logger.info(f"Updated local hash database with {os.path.basename(document_path)}")
        return True
    except Exception as e:
        logger.error(f"Error updating hash database: {e}")
        return False

def update_graph_database(analysis):
    """Update the graph database with new entity and relationship data"""
    try:
        # Load existing graph data or create new
        if os.path.exists(GRAPH_DATA_PATH):
            with open(GRAPH_DATA_PATH, 'r') as f:
                graph = json.load(f)
        else:
            graph = {
                'nodes': [],
                'edges': [],
                'projects': [],
                'locations': []
            }
        
        if not analysis:
            return False
            
        # Extract document path for reference
        doc_path = analysis.get('document_path', '')
        doc_name = os.path.basename(doc_path)
        
        # Add project as a node
        project = analysis.get('project', {})
        if project and project.get('title'):
            project_id = f"project_{len(graph['projects'])}"
            project_data = {
                'id': project_id,
                'type': 'project',
                'title': project.get('title', ''),
                'summary': project.get('summary', ''),
                'start_date': project.get('start_date', ''),
                'end_date': project.get('end_date', ''),
                'status': project.get('status', ''),
                'document': doc_name
            }
            graph['projects'].append(project_data)
            graph['nodes'].append({
                'id': project_id,
                'label': project.get('title', ''),
                'type': 'project',
                'properties': project_data
            })
            
        # Add locations
        for location in analysis.get('locations', []):
            loc_name = location.get('name', '')
            if not loc_name:
                continue
                
            # Check if location already exists
            existing_loc = next((l for l in graph['locations'] if l.get('name') == loc_name), None)
            if not existing_loc:
                loc_id = f"location_{len(graph['locations'])}"
                loc_data = {
                    'id': loc_id,
                    'name': loc_name,
                    'lat': location.get('lat'),
                    'lng': location.get('lng'),
                    'documents': [doc_name]
                }
                graph['locations'].append(loc_data)
                graph['nodes'].append({
                    'id': loc_id,
                    'label': loc_name,
                    'type': 'location',
                    'properties': {
                        'lat': location.get('lat'),
                        'lng': location.get('lng')
                    }
                })
                
                # Link project to location if available
                if project and project.get('title'):
                    graph['edges'].append({
                        'source': project_id,
                        'target': loc_id,
                        'relationship': 'located_at',
                        'document': doc_name
                    })
            else:
                # Update existing location
                if doc_name not in existing_loc.get('documents', []):
                    existing_loc['documents'].append(doc_name)
                
                # Link project to existing location
                if project and project.get('title'):
                    graph['edges'].append({
                        'source': project_id,
                        'target': existing_loc['id'],
                        'relationship': 'located_at',
                        'document': doc_name
                    })
        
        # Add entities
        entities = analysis.get('entities', {})
        
        # Process people
        for person in entities.get('people', []):
            person_name = person.get('name', '')
            if not person_name:
                continue
                
            # Check if person already exists
            existing_person = next((n for n in graph['nodes'] if n.get('type') == 'person' and n.get('label') == person_name), None)
            if not existing_person:
                person_id = f"person_{len([n for n in graph['nodes'] if n.get('type') == 'person'])}"
                graph['nodes'].append({
                    'id': person_id,
                    'label': person_name,
                    'type': 'person',
                    'properties': {
                        'role': person.get('role', ''),
                        'documents': [doc_name]
                    }
                })
                
                # Link to project if available
                if project and project.get('title'):
                    graph['edges'].append({
                        'source': person_id,
                        'target': project_id,
                        'relationship': person.get('role', 'involved_in'),
                        'document': doc_name
                    })
            else:
                # Update existing person
                person_id = existing_person['id']
                if 'documents' not in existing_person['properties']:
                    existing_person['properties']['documents'] = []
                if doc_name not in existing_person['properties']['documents']:
                    existing_person['properties']['documents'].append(doc_name)
                
                # Link to project if available
                if project and project.get('title'):
                    graph['edges'].append({
                        'source': person_id,
                        'target': project_id,
                        'relationship': person.get('role', 'involved_in'),
                        'document': doc_name
                    })
        
        # Process organizations
        for org in entities.get('organizations', []):
            org_name = org.get('name', '')
            if not org_name:
                continue
                
            # Check if organization already exists
            existing_org = next((n for n in graph['nodes'] if n.get('type') == 'organization' and n.get('label') == org_name), None)
            if not existing_org:
                org_id = f"org_{len([n for n in graph['nodes'] if n.get('type') == 'organization'])}"
                graph['nodes'].append({
                    'id': org_id,
                    'label': org_name,
                    'type': 'organization',
                    'properties': {
                        'role': org.get('role', ''),
                        'documents': [doc_name]
                    }
                })
                
                # Link to project if available
                if project and project.get('title'):
                    graph['edges'].append({
                        'source': org_id,
                        'target': project_id,
                        'relationship': org.get('role', 'involved_in'),
                        'document': doc_name
                    })
            else:
                # Update existing organization
                org_id = existing_org['id']
                if 'documents' not in existing_org['properties']:
                    existing_org['properties']['documents'] = []
                if doc_name not in existing_org['properties']['documents']:
                    existing_org['properties']['documents'].append(doc_name)
                
                # Link to project if available
                if project and project.get('title'):
                    graph['edges'].append({
                        'source': org_id,
                        'target': project_id,
                        'relationship': org.get('role', 'involved_in'),
                        'document': doc_name
                    })
        
        # Process companies
        for company in entities.get('companies', []):
            company_name = company.get('name', '')
            if not company_name:
                continue
                
            # Check if company already exists
            existing_company = next((n for n in graph['nodes'] if n.get('type') == 'company' and n.get('label') == company_name), None)
            if not existing_company:
                company_id = f"company_{len([n for n in graph['nodes'] if n.get('type') == 'company'])}"
                graph['nodes'].append({
                    'id': company_id,
                    'label': company_name,
                    'type': 'company',
                    'properties': {
                        'role': company.get('role', ''),
                        'documents': [doc_name]
                    }
                })
                
                # Link to project if available
                if project and project.get('title'):
                    graph['edges'].append({
                        'source': company_id,
                        'target': project_id,
                        'relationship': company.get('role', 'involved_in'),
                        'document': doc_name
                    })
            else:
                # Update existing company
                company_id = existing_company['id']
                if 'documents' not in existing_company['properties']:
                    existing_company['properties']['documents'] = []
                if doc_name not in existing_company['properties']['documents']:
                    existing_company['properties']['documents'].append(doc_name)
                
                # Link to project if available
                if project and project.get('title'):
                    graph['edges'].append({
                        'source': company_id,
                        'target': project_id,
                        'relationship': company.get('role', 'involved_in'),
                        'document': doc_name
                    })
        
        # Add explicit relationships from analysis
        for rel in analysis.get('relationships', []):
            source_name = rel.get('source', '')
            target_name = rel.get('target', '')
            relationship = rel.get('relationship', '')
            
            if not source_name or not target_name or not relationship:
                continue
                
            # Find source and target nodes
            source_node = next((n for n in graph['nodes'] if n.get('label') == source_name), None)
            target_node = next((n for n in graph['nodes'] if n.get('label') == target_name), None)
            
            if source_node and target_node:
                # Check if relationship already exists
                existing_edge = next((e for e in graph['edges'] 
                                     if e.get('source') == source_node['id'] 
                                     and e.get('target') == target_node['id']
                                     and e.get('relationship') == relationship), None)
                
                if not existing_edge:
                    graph['edges'].append({
                        'source': source_node['id'],
                        'target': target_node['id'],
                        'relationship': relationship,
                        'document': doc_name
                    })
        
        # Detect document type and create corresponding node
        doc_type = analysis.get('document_type', '').lower()
        if doc_type in ['patent', 'research', 'research_paper', 'paper']:
            dtype_enum = 'patent' if 'patent' in doc_type else 'research_paper'
            type_node_id = f"{dtype_enum}_{len([n for n in graph['nodes'] if n.get('type') == dtype_enum])}"
            graph['nodes'].append({
                'id': type_node_id,
                'label': doc_name,
                'type': dtype_enum,
                'properties': {
                    'document': doc_name,
                    'cid': cid if 'cid' in locals() else None
                }
            })
            # link the document node to this type node
            graph['edges'].append({
                'source': doc_id,
                'target': type_node_id,
                'relationship': 'is_a',
                'document': doc_name
            })
        
        # Add funding node if present
        if 'funding' in analysis and analysis['funding'] and analysis['funding'].get('amount'):
            funding_id = f"funding_{len([n for n in graph['nodes'] if n.get('type') == 'funding'])}"
            graph['nodes'].append({
                'id': funding_id,
                'label': f"$ {analysis['funding'].get('amount')}",
                'type': 'funding',
                'properties': analysis['funding']
            })
            # Link funding to project or document
            target_ref = project_id if 'project_id' in locals() else doc_id
            graph['edges'].append({
                'source': funding_id,
                'target': target_ref,
                'relationship': 'funded_by',
                'document': doc_name
            })
        
        # Ensure Hampton Roads (region) node exists and link local projects/docs
        region_name = 'Hampton Roads'
        region_node = next((n for n in graph['nodes'] if n.get('type') == 'region' and n.get('label') == region_name), None)
        if not region_node:
            region_node = {
                'id': 'region_757',
                'label': region_name,
                'type': 'region',
                'properties': {
                    'country': 'USA',
                    'state': 'Virginia'
                }
            }
            graph['nodes'].append(region_node)
        
        # Link project/doc nodes to Hampton Roads region
        for loc_id in locality_ids:
            graph['edges'].append({
                'source': loc_id,
                'target': region_node['id'],
                'relationship': 'located_in_region',
                        'document': doc_name
                    })
        
        # Save updated graph data
        with open(GRAPH_DATA_PATH, 'w') as f:
            json.dump(graph, f, indent=2)
        
        # Publish to IPNS
        publish_graph_to_ipns()
        
        logger.info(f"Updated graph database with data from {doc_name}")
        return True
    except Exception as e:
        logger.error(f"Error updating graph database: {e}")
        return False

def publish_graph_to_ipns():
    """Pin latest graph_data.json to IPFS and publish CID via IPNS."""
    try:
        client = ipfshttpclient.connect()
        res = client.add(GRAPH_DATA_PATH)
        cid = res['Hash'] if isinstance(res, dict) else res[-1]['Hash']
        client.name.publish(f"/ipfs/{cid}", key=GRAPH_IPNS_KEY)
        logger.info(f"Published graph {cid} to IPNS key '{GRAPH_IPNS_KEY}'")
        return cid
    except Exception as e:
        logger.error(f"Failed to publish graph to IPNS: {e}")
        return None

def sync_with_web_server(ipfs_hash, document_path, analysis=None):
    """Send IPFS hash and analysis to the web server"""
    if not API_KEY:
        logger.warning("API_KEY not set, skipping sync with web server")
        return False
    
    try:
        # Prepare core payload
        payload = {
            'ipfs_hash': ipfs_hash,
            'document_name': os.path.basename(document_path),
            'document_type': 'unknown'
        }
        
        # Add analysis data if available
        if analysis:
            # Document type
            if 'document_type' in analysis:
                payload['document_type'] = analysis['document_type']
            
            # Project data
            if 'project' in analysis:
                payload['project'] = analysis['project']
                
            # Location data - map coordinates to geoJSON format
            if 'locations' in analysis and analysis['locations']:
                payload['geojson'] = {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "properties": {
                                "name": loc.get('name', ''),
                                "document": os.path.basename(document_path)
                            },
                            "geometry": {
                                "type": "Point",
                                "coordinates": [loc.get('lng', 0), loc.get('lat', 0)]
                            }
                        } for loc in analysis['locations'] if 'lat' in loc and 'lng' in loc
                    ]
                }
            
            # Funding data
            if 'funding' in analysis:
                payload['funding'] = analysis['funding']
                
            # Entity data
            if 'entities' in analysis:
                payload['entities'] = analysis['entities']
        
        # Send to web server
        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': API_KEY
        }
        
        import requests
        response = requests.post(WEB_API_ENDPOINT, json=payload, headers=headers)
        response.raise_for_status()
        
        logger.info(f"Successfully synced {os.path.basename(document_path)} with web server")
        return True
    except Exception as e:
        logger.error(f"Error syncing with web server: {e}")
        return False

def add_document_to_graph(doc_path, extracted_data, G=None):
    """Add document and its metadata to the graph."""
    if G is None:
        G = nx.DiGraph() if not os.path.exists(GRAPH_DATA_PATH) else load_graph()
    
    # Generate document ID
    doc_id = f"doc_{hashlib.md5(os.path.basename(doc_path).encode()).hexdigest()[:8]}"
    
    # Add document to IPFS and get CID
    cid = None
    try:
        from ipfs_storage.ipfs_client import add_or_reuse
        cid = add_or_reuse(doc_path)
        print(f"Added document to IPFS with CID: {cid}")
    except Exception as e:
        print(f"Warning: Could not add document to IPFS: {e}")
    
    # Current timestamp
    now_iso = datetime.now().isoformat()
    
    # Add document node with CID
    G.add_node(
        doc_id,
        label=os.path.basename(doc_path),
        type=NodeType.DOCUMENT.value,
        path=doc_path,
        cid=cid,  # Store the IPFS CID in the node
        date=now_iso
    )
    
    # Extract text content for locality detection
    text_content = extracted_data.get('text_content', '') or extract_text_from_document(doc_path)
    
    # Detect localities and add relations to graph
    locality_ids = add_locality_relations_to_graph(G, doc_id, text_content)
    
    # If localities were found, add them as attributes to the document node
    if locality_ids:
        # Get locality names
        locality_names = [G.nodes[loc_id].get('name', '') for loc_id in locality_ids]
        G.nodes[doc_id]['localities'] = locality_names
        
        # For the primary locality (highest confidence), set as main locality
        if locality_ids:
            # Find edge with highest confidence
            best_edge = None
            best_confidence = -1
            for loc_id in locality_ids:
                edge_data = G.get_edge_data(doc_id, loc_id)
                if edge_data and edge_data.get('confidence', 0) > best_confidence:
                    best_confidence = edge_data.get('confidence', 0)
                    best_edge = (doc_id, loc_id, edge_data)
            
            if best_edge:
                # Set primary locality
                loc_id = best_edge[1]
                G.nodes[doc_id]['primary_locality'] = G.nodes[loc_id].get('name', '')
                
                # Copy coordinates for map display
                if 'coordinates' in G.nodes[loc_id]:
                    G.nodes[doc_id]['coordinates'] = G.nodes[loc_id]['coordinates']
    
    # If document has a project, add project node and link to localities
    if 'project' in extracted_data and extracted_data['project'].get('title'):
        project_data = extracted_data['project']
        project_id = f"project_{hashlib.md5(project_data['title'].encode()).hexdigest()[:8]}"
        
        # Add project node
        G.add_node(
            project_id,
            label=project_data['title'],
            type=NodeType.PROJECT.value,
            title=project_data['title'],
            summary=project_data.get('summary', ''),
            start_date=project_data.get('start_date', ''),
            end_date=project_data.get('end_date', ''),
            cid=cid  # Use the same CID as the document
        )
        
        # Link document to project
        G.add_edge(
            doc_id,
            project_id,
            type="contains_document",
            timestamp=now_iso
        )
        
        # Link project to localities
        for loc_id in locality_ids:
            G.add_edge(
                project_id,
                loc_id,
                type=EdgeType.LOCATED_IN.value,
                timestamp=now_iso,
                source_document=doc_id
            )
            
            # For map visualization, copy coordinates to project
            if 'coordinates' in G.nodes[loc_id] and 'coordinates' not in G.nodes[project_id]:
                G.nodes[project_id]['coordinates'] = G.nodes[loc_id]['coordinates']
                G.nodes[project_id]['primary_locality'] = G.nodes[loc_id].get('name', '')
    
    return G

def store_metadata_in_ipfs(metadata, metadata_type="document"):
    """Store metadata in IPFS and return the CID."""
    try:
        import tempfile
        import json
        from ipfs_storage.ipfs_client import add_or_reuse
        
        # Create a temporary file to store the JSON
        with tempfile.NamedTemporaryFile(suffix='.json', mode='w', delete=False) as temp:
            json.dump(metadata, temp, indent=2)
            temp_path = temp.name
        
        # Add to IPFS and get CID
        cid = add_or_reuse(temp_path)
        
        # Clean up
        os.unlink(temp_path)
        
        return cid
    except Exception as e:
        print(f"Warning: Could not store metadata in IPFS: {e}")
        return None
        
@lru_cache(maxsize=10)
def load_prompt_template(version: str = "v1") -> str:
    """Load prompt template from file path Agent/prompts/extract_<version>.md"""
    from pathlib import Path as _P
    tpl = _P(f"Agent/prompts/extract_{version}.md")
    if tpl.exists():
        return tpl.read_text(encoding='utf-8')
    return "You are an AI assistant. Document:\n{document_text}\nReturn JSON: {schema}"

def process_text(document_text: str, phi3_processor) -> dict:
    """Run Phi-3 on *document_text* and return structured JSON with contact info."""
    import textwrap, json as _json

    prompt = textwrap.dedent(f"""\
        You are an AI assistant that extracts structured data about local development
        projects in the Virginia 757 area.

        Analyse the following document and return a **valid JSON** object matching
        exactly this schema (order and keys must stay the same):

        {{
            "project": {{
                "title": "",
                "summary": "",
                "start_date": "",
                "end_date": "",
                "status": ""
            }},
            "locations": [
                {{"name": "", "lat": 0.0, "lng": 0.0}}
            ],
            "entities": {{
                "people": [
                    {{"name": "", "role": ""}}
                ],
                "organizations": [
                    {{"name": "", "role": ""}}
                ],
                "companies": [
                    {{"name": "", "role": ""}}
                ]
            }},
            "relationships": [
                {{"source": "", "target": "", "relationship": ""}}
            ],
            "funding": {{
                "amount": "",
                "source": "",
                "details": ""
            }},
            "contact_info": {{
                "email": "",
                "phone": "",
                "website": ""
            }}
        }}

        Document:
        ----------------
        {document_text}
        ----------------

        Respond with ONLY the JSON – no commentary, markdown, or code fences.
    """)

    raw_output = phi3_processor.run_inference(prompt).strip()

    # Remove potential markdown fences/backticks
    if raw_output.startswith('```'):
        raw_output = raw_output.strip('`')
        raw_output = raw_output.lstrip('json').strip()

    try:
        result = _json.loads(raw_output)
    except Exception as ex:
        logger.error("Failed to parse Phi-3 output as JSON: %s", ex)
        result = {"error": str(ex), "raw_output": raw_output}

    # Attach original text for traceability
    result["text_content"] = document_text
    return result

def process_text_chunk(chunk: str, phi3_processor) -> dict:
    """Run Phi-3 on *chunk* and return structured JSON with contact info."""
    import textwrap, json as _json

    prompt_template = load_prompt_template()
    detected_type = detect_document_type(chunk)
    prompt = prompt_template.replace("{detected_type}", detected_type)

    raw_output = phi3_processor.run_inference(prompt).strip()

    # Remove potential markdown fences/backticks
    if raw_output.startswith('```'):
        raw_output = raw_output.strip('`')
        raw_output = raw_output.lstrip('json').strip()

    try:
        result = _json.loads(raw_output)
    except Exception as ex:
        logger.error("Failed to parse Phi-3 output as JSON: %s", ex)
        result = {"error": str(ex), "raw_output": raw_output}

    # Attach original text for traceability
    result["text_content"] = chunk
    return result

def detect_document_type(text: str) -> str:
    """Heuristic detector to bias prompt with detected_type placeholder."""
    patterns = {
        "patent": r"\bUnited\s+States\s+Patent\b|\bpatent\s+number\b",
        "research": r"\babstract\b.*\bmethodology\b|\breferences\b",
        "project": r"\bproject\s+title\b|\bconstruction\s+status\b",
    }
    for dtype, pat in patterns.items():
        if re.search(pat, text, re.IGNORECASE|re.DOTALL):
            return dtype
    return "other"

def ensure_processed_output(document_path: str, processed_data: dict, output_dir: str = PROCESSED_DIR):
    """Write *processed_data* to <output_dir>/<stem>.json. Return the path."""
    from pathlib import Path as _Path, PurePath as _PurePath

    _Path(output_dir).mkdir(parents=True, exist_ok=True)
    out_file = _Path(output_dir) / (_PurePath(document_path).stem + '.json')
    with open(out_file, 'w', encoding='utf-8') as fh:
        json.dump(processed_data, fh, ensure_ascii=False, indent=2)
    logger.info("Saved processed document to %s", out_file)
    return str(out_file)

def process_document(document_path, phi3_processor):
    """Main function to process a document and update the graph."""
    PROCESSING_IN_FLIGHT.inc()
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("process_document"):
        try:
            # Extract text from document
            document_text = extract_text_from_document(document_path)
            
            # Chunk text and process with Phi-3
            chunks = chunk_document(document_text)
            processed_data = smart_union([process_text_chunk(chunk, phi3_processor) for chunk in chunks])
            
            # upsert into vector DB and fetch similar docs
            try:
                upsert_document(processed_data, document_text)
                processed_data["similar_docs"] = similar_docs(document_text)
            except Exception as ex:
                logger.warning("Vector index error: %s", ex)
            
            # Store metadata in IPFS and get CID
            metadata_cid = store_metadata_in_ipfs(processed_data)
            
            # Update processed data with CID
            if metadata_cid:
                processed_data['metadata_cid'] = metadata_cid
            
            # Persist processed JSON using helper
            ensure_processed_output(document_path, processed_data)
            
            try:
                r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'), decode_responses=True)
                r.xadd('graph_updates', {'path': document_path, 'data': json.dumps(processed_data)}, maxlen=10000, approximate=True)
            except Exception as ex:
                logger.error('Failed to enqueue graph update: %s', ex)
            
            return processed_data
        finally:
            PROCESSING_IN_FLIGHT.dec()

def monitor_data_directory(phi3_processor):
    """Monitor the data directory for new documents"""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(ANALYSIS_DIR, exist_ok=True)
    
    logger.info("Starting document monitoring service")
    
    # Load existing database to check which files have been processed
    if os.path.exists(DB_PATH):
        with open(DB_PATH, 'r') as f:
            db = json.load(f)
            processed_files = [entry['document'] for entry in db.get('documents', [])]
    else:
        db = {'documents': []}
        processed_files = []
    
    while True:
        # Find all documents in the data directory
        all_files = []
        for ext in DOCUMENT_EXTENSIONS:
            all_files.extend(glob.glob(os.path.join(DATA_DIR, f"*{ext}")))
        
        # Process new files
        for file_path in all_files:
            filename = os.path.basename(file_path)
            if filename in processed_files or filename == 'ipfs_hashes.json' or filename == 'graph_data.json':
                continue
            
            logger.info(f"Found new document: {filename}")
            success = process_document(file_path, phi3_processor)
            
            if success:
                processed_files.append(filename)
            
            # Short pause between processing documents
            time.sleep(1)
        
        # Wait before next scan
        logger.info("Sleeping for 60 seconds before next scan")
        time.sleep(60)

def queue_worker(phi3_processor):
    """Continuously consume document paths from Redis queue and process them."""
    logger.info("Starting queue worker mode – waiting for jobs…")
    while True:
        job = dequeue_document()
        if not job:
            continue  # timeout, loop back
        
        path = job.get('path')
        if not path:
            logger.warning("Received job without path: %s", job)
            continue
        
        process_document(path, phi3_processor)

def main():
    parser = argparse.ArgumentParser(description='Enhanced Document Processor')
    parser.add_argument('--mode', type=str, default='worker', 
                        choices=['worker', 'api', 'cli', 'telemetry'],
                        help='Operating mode')
    parser.add_argument('--model', type=str, default='deepseek-r1:70b',
                        help='Ollama model to use for inference')
    parser.add_argument('--ollama_base', type=str, default='http://localhost:11434',
                        help='Ollama API base URL')
    parser.add_argument('--threads', type=int, default=None,
                        help='Number of threads for inference (auto-detected if not specified)')
    parser.add_argument('--ctx_size', type=int, default=32768,
                        help='Context size for model')
    parser.add_argument('--batch_size', type=int, default=32,
                        help='Batch size for processing')
    parser.add_argument('--max_parallel', type=int, default=32,
                        help='Maximum number of parallel jobs')
    parser.add_argument('--cost_per_hour', type=float, default=50.0,
                        help='Compute cost per hour in dollars')
    parser.add_argument('--max_budget', type=float, default=float('inf'),
                        help='Maximum budget in dollars')
    parser.add_argument('--idle_shutdown', type=int, default=10,
                        help='Shutdown after N minutes of idle time')
    parser.add_argument('--telemetry_types', type=str, default='traffic,weather',
                        help='Comma-separated list of telemetry types to collect')
    parser.add_argument("--single-file", help="Process a single file instead of monitoring")
    parser.add_argument("--storage-path", default="./temp_storage", help="Path for temporary document storage")
    parser.add_argument("--redis-url", default="redis://localhost:6379/0", help="Redis connection string")
    parser.add_argument("--replication", type=int, default=2, help="Storage replication factor")
    parser.add_argument("--storage-capacity", type=float, default=50.0, help="Local storage capacity in GB")

    args = parser.parse_args()

    # Configure compute tracking
    compute_config = ComputeConfig(
        cost_per_hour=args.cost_per_hour,
        max_budget=args.max_budget,
        idle_shutdown_minutes=args.idle_shutdown
    )

    processor = EnhancedDocumentProcessor(
        llm_type='ollama',
        model_name=args.model,
        api_base=args.ollama_base,
        threads=args.threads,
        ctx_size=args.ctx_size,
        batch_size=args.batch_size,
        max_parallel_jobs=args.max_parallel,
        compute_config=compute_config,
        storage_capacity_gb=args.storage_capacity,
        temperature=args.temperature
    )
    
    if args.single_file:
        logger.info(f"Processing single file: {args.single_file}")
        result = processor.process_document(args.single_file)
        logger.info(f"Processing complete: {result}")
    else:
        logger.info("Starting continuous processing mode")
        processor.run_processor()

if __name__ == "__main__":
    main()
