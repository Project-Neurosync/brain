"""
Production File Upload & Processing System for NeuroSync AI Backend
Handles multi-format file ingestion, content extraction, and processing pipeline.
"""

import os
import io
import uuid
import asyncio
import logging
import mimetypes
from typing import Dict, List, Any, Optional, Tuple, Union, BinaryIO
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from enum import Enum

import aiofiles
from pydantic import BaseModel

# File processing libraries
try:
    import PyPDF2
    import docx
    from PIL import Image
    import pytesseract
except ImportError:
    # These will be handled gracefully if not available
    PyPDF2 = None
    docx = None
    Image = None
    pytesseract = None

class FileType(str, Enum):
    """Supported file types."""
    PDF = "pdf"
    DOCX = "docx"
    DOC = "doc"
    TXT = "txt"
    MD = "md"
    PYTHON = "py"
    JAVASCRIPT = "js"
    TYPESCRIPT = "ts"
    HTML = "html"
    CSS = "css"
    JSON = "json"
    XML = "xml"
    CSV = "csv"
    IMAGE = "image"
    UNKNOWN = "unknown"

class ProcessingStatus(str, Enum):
    """File processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class FileMetadata(BaseModel):
    """File metadata information."""
    filename: str
    original_filename: str
    file_type: FileType
    mime_type: str
    size_bytes: int
    upload_timestamp: datetime
    processed_timestamp: Optional[datetime] = None
    checksum: str
    project_id: str
    uploaded_by: str
    source: str = "upload"  # upload, github, jira, etc.

class ProcessedContent(BaseModel):
    """Processed file content."""
    file_id: str
    metadata: FileMetadata
    extracted_text: str
    structured_content: Dict[str, Any]
    entities: List[Dict[str, Any]]
    importance_score: float
    processing_status: ProcessingStatus
    error_message: Optional[str] = None
    chunks: List[Dict[str, Any]] = []

class FileUploadResult(BaseModel):
    """Result of file upload operation."""
    file_id: str
    filename: str
    status: ProcessingStatus
    message: str
    size_bytes: int
    processing_time_ms: Optional[int] = None

class BatchProcessingResult(BaseModel):
    """Result of batch file processing."""
    total_files: int
    successful: int
    failed: int
    skipped: int
    processing_time_ms: int
    results: List[FileUploadResult]
    errors: List[str] = []

class FileProcessingSystem:
    """
    Production-ready file upload and processing system.
    Handles multi-format files with content extraction and intelligent processing.
    """
    
    def __init__(
        self,
        storage_path: str,
        vector_service=None,
        knowledge_graph_service=None,
        importance_filter=None,
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize the File Processing System."""
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Service dependencies
        self.vector_service = vector_service
        self.knowledge_graph_service = knowledge_graph_service
        self.importance_filter = importance_filter
        
        # Configuration
        self.config = config or {}
        self.max_file_size = self.config.get('max_file_size_mb', 50) * 1024 * 1024  # 50MB default
        self.max_batch_size = self.config.get('max_batch_size', 100)
        self.chunk_size = self.config.get('chunk_size', 1000)
        self.chunk_overlap = self.config.get('chunk_overlap', 200)
        self.supported_extensions = self.config.get('supported_extensions', {
            '.pdf': FileType.PDF,
            '.docx': FileType.DOCX,
            '.doc': FileType.DOC,
            '.txt': FileType.TXT,
            '.md': FileType.MD,
            '.py': FileType.PYTHON,
            '.js': FileType.JAVASCRIPT,
            '.ts': FileType.TYPESCRIPT,
            '.html': FileType.HTML,
            '.css': FileType.CSS,
            '.json': FileType.JSON,
            '.xml': FileType.XML,
            '.csv': FileType.CSV,
            '.png': FileType.IMAGE,
            '.jpg': FileType.IMAGE,
            '.jpeg': FileType.IMAGE,
        })
        
        # Thread pool for CPU-intensive operations
        self._executor = ThreadPoolExecutor(max_workers=4)
        
        # Logger
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"File Processing System initialized with storage: {self.storage_path}")
    
    async def upload_file(
        self,
        file_content: bytes,
        filename: str,
        project_id: str,
        user_id: str,
        source: str = "upload"
    ) -> FileUploadResult:
        """
        Upload and process a single file.
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            project_id: Project ID for isolation
            user_id: User uploading the file
            source: Source of the file (upload, github, etc.)
            
        Returns:
            FileUploadResult with processing status
        """
        start_time = datetime.now()
        
        try:
            # Validate file size
            if len(file_content) > self.max_file_size:
                return FileUploadResult(
                    file_id="",
                    filename=filename,
                    status=ProcessingStatus.FAILED,
                    message=f"File size exceeds limit ({self.max_file_size / 1024 / 1024:.1f}MB)",
                    size_bytes=len(file_content)
                )
            
            # Generate file ID and determine type
            file_id = str(uuid.uuid4())
            file_type = self._determine_file_type(filename)
            
            if file_type == FileType.UNKNOWN:
                return FileUploadResult(
                    file_id=file_id,
                    filename=filename,
                    status=ProcessingStatus.SKIPPED,
                    message="Unsupported file type",
                    size_bytes=len(file_content)
                )
            
            # Create metadata
            metadata = FileMetadata(
                filename=f"{file_id}_{filename}",
                original_filename=filename,
                file_type=file_type,
                mime_type=mimetypes.guess_type(filename)[0] or "application/octet-stream",
                size_bytes=len(file_content),
                upload_timestamp=datetime.now(),
                checksum=self._calculate_checksum(file_content),
                project_id=project_id,
                uploaded_by=user_id,
                source=source
            )
            
            # Save file to storage
            file_path = await self._save_file_to_storage(file_id, file_content, project_id)
            
            # Process file content
            processed_content = await self._process_file_content(file_path, metadata)
            
            # Calculate processing time
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return FileUploadResult(
                file_id=file_id,
                filename=filename,
                status=processed_content.processing_status,
                message="File processed successfully" if processed_content.processing_status == ProcessingStatus.COMPLETED else processed_content.error_message or "Processing failed",
                size_bytes=len(file_content),
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            self.logger.error(f"Error uploading file {filename}: {str(e)}")
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return FileUploadResult(
                file_id="",
                filename=filename,
                status=ProcessingStatus.FAILED,
                message=f"Upload failed: {str(e)}",
                size_bytes=len(file_content),
                processing_time_ms=processing_time
            )
    
    async def upload_batch(
        self,
        files: List[Tuple[bytes, str]],  # (content, filename) pairs
        project_id: str,
        user_id: str,
        source: str = "upload"
    ) -> BatchProcessingResult:
        """
        Upload and process multiple files in batch.
        
        Args:
            files: List of (file_content, filename) tuples
            project_id: Project ID for isolation
            user_id: User uploading the files
            source: Source of the files
            
        Returns:
            BatchProcessingResult with overall status
        """
        start_time = datetime.now()
        
        if len(files) > self.max_batch_size:
            return BatchProcessingResult(
                total_files=len(files),
                successful=0,
                failed=len(files),
                skipped=0,
                processing_time_ms=0,
                results=[],
                errors=[f"Batch size exceeds limit ({self.max_batch_size})"]
            )
        
        # Process files concurrently
        tasks = [
            self.upload_file(content, filename, project_id, user_id, source)
            for content, filename in files
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        successful = 0
        failed = 0
        skipped = 0
        errors = []
        valid_results = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed += 1
                errors.append(f"File {files[i][1]}: {str(result)}")
                valid_results.append(FileUploadResult(
                    file_id="",
                    filename=files[i][1],
                    status=ProcessingStatus.FAILED,
                    message=str(result),
                    size_bytes=len(files[i][0])
                ))
            else:
                valid_results.append(result)
                if result.status == ProcessingStatus.COMPLETED:
                    successful += 1
                elif result.status == ProcessingStatus.FAILED:
                    failed += 1
                else:
                    skipped += 1
        
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return BatchProcessingResult(
            total_files=len(files),
            successful=successful,
            failed=failed,
            skipped=skipped,
            processing_time_ms=processing_time,
            results=valid_results,
            errors=errors
        )
    
    async def _process_file_content(
        self,
        file_path: Path,
        metadata: FileMetadata
    ) -> ProcessedContent:
        """
        Process file content and extract information.
        
        Args:
            file_path: Path to the stored file
            metadata: File metadata
            
        Returns:
            ProcessedContent with extracted information
        """
        try:
            # Extract text content based on file type
            extracted_text = await self._extract_text_content(file_path, metadata.file_type)
            
            if not extracted_text.strip():
                return ProcessedContent(
                    file_id=metadata.filename.split('_')[0],
                    metadata=metadata,
                    extracted_text="",
                    structured_content={},
                    entities=[],
                    importance_score=0.0,
                    processing_status=ProcessingStatus.SKIPPED,
                    error_message="No text content extracted"
                )
            
            # Create structured content
            structured_content = {
                'text': extracted_text,
                'word_count': len(extracted_text.split()),
                'char_count': len(extracted_text),
                'language': 'en',  # TODO: Add language detection
                'extracted_at': datetime.now().isoformat()
            }
            
            # Extract entities (mock implementation)
            entities = await self._extract_entities(extracted_text, metadata)
            
            # Calculate importance score using ML filter
            importance_score = 0.5  # Default score
            if self.importance_filter:
                try:
                    importance_data = {
                        'content': extracted_text,
                        'data_type': 'DOCUMENT',
                        'source': metadata.source,
                        'author': metadata.uploaded_by,
                        'timestamp': metadata.upload_timestamp,
                        'project_id': metadata.project_id,
                        'metadata': {
                            'filename': metadata.original_filename,
                            'file_type': metadata.file_type,
                            'size_bytes': metadata.size_bytes
                        }
                    }
                    importance_score = await self.importance_filter.score_data_importance(importance_data)
                except Exception as e:
                    self.logger.warning(f"Failed to calculate importance score: {str(e)}")
            
            # Create text chunks for vector storage
            chunks = self._create_text_chunks(extracted_text, metadata)
            
            # Store in vector database if available and important enough
            if self.vector_service and importance_score > 0.3:
                try:
                    await self._store_in_vector_db(chunks, metadata, importance_score)
                except Exception as e:
                    self.logger.warning(f"Failed to store in vector database: {str(e)}")
            
            # Store entities in knowledge graph if available
            if self.knowledge_graph_service and entities:
                try:
                    await self._store_in_knowledge_graph(entities, metadata)
                except Exception as e:
                    self.logger.warning(f"Failed to store in knowledge graph: {str(e)}")
            
            metadata.processed_timestamp = datetime.now()
            
            return ProcessedContent(
                file_id=metadata.filename.split('_')[0],
                metadata=metadata,
                extracted_text=extracted_text,
                structured_content=structured_content,
                entities=entities,
                importance_score=importance_score,
                processing_status=ProcessingStatus.COMPLETED,
                chunks=chunks
            )
            
        except Exception as e:
            self.logger.error(f"Error processing file {metadata.filename}: {str(e)}")
            return ProcessedContent(
                file_id=metadata.filename.split('_')[0],
                metadata=metadata,
                extracted_text="",
                structured_content={},
                entities=[],
                importance_score=0.0,
                processing_status=ProcessingStatus.FAILED,
                error_message=str(e)
            )
    
    async def _extract_text_content(self, file_path: Path, file_type: FileType) -> str:
        """Extract text content from file based on type."""
        def _extract():
            try:
                if file_type == FileType.PDF:
                    return self._extract_pdf_text(file_path)
                elif file_type == FileType.DOCX:
                    return self._extract_docx_text(file_path)
                elif file_type in [FileType.TXT, FileType.MD, FileType.PYTHON, FileType.JAVASCRIPT, 
                                 FileType.TYPESCRIPT, FileType.HTML, FileType.CSS, FileType.JSON, FileType.XML]:
                    return self._extract_plain_text(file_path)
                elif file_type == FileType.CSV:
                    return self._extract_csv_text(file_path)
                elif file_type == FileType.IMAGE:
                    return self._extract_image_text(file_path)
                else:
                    return ""
            except Exception as e:
                self.logger.error(f"Error extracting text from {file_path}: {str(e)}")
                return ""
        
        return await asyncio.get_event_loop().run_in_executor(self._executor, _extract)
    
    def _extract_pdf_text(self, file_path: Path) -> str:
        """Extract text from PDF file."""
        if not PyPDF2:
            raise ImportError("PyPDF2 not available for PDF processing")
        
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    
    def _extract_docx_text(self, file_path: Path) -> str:
        """Extract text from DOCX file."""
        if not docx:
            raise ImportError("python-docx not available for DOCX processing")
        
        doc = docx.Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    
    def _extract_plain_text(self, file_path: Path) -> str:
        """Extract text from plain text files."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, 'r', encoding='latin-1') as file:
                return file.read()
    
    def _extract_csv_text(self, file_path: Path) -> str:
        """Extract text from CSV file."""
        import csv
        text = ""
        with open(file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                text += " ".join(row) + "\n"
        return text
    
    def _extract_image_text(self, file_path: Path) -> str:
        """Extract text from image using OCR."""
        if not pytesseract or not Image:
            return ""  # OCR not available
        
        try:
            image = Image.open(file_path)
            return pytesseract.image_to_string(image)
        except Exception:
            return ""
    
    async def _extract_entities(
        self,
        text: str,
        metadata: FileMetadata
    ) -> List[Dict[str, Any]]:
        """Extract entities from text content."""
        # Mock entity extraction - in production, use NLP libraries
        entities = []
        
        # Extract file-based entity
        entities.append({
            'type': 'File',
            'name': metadata.original_filename,
            'properties': {
                'file_type': metadata.file_type,
                'size_bytes': metadata.size_bytes,
                'uploaded_by': metadata.uploaded_by,
                'source': metadata.source
            }
        })
        
        # Extract simple patterns (URLs, emails, etc.)
        import re
        
        # URLs
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, text)
        for url in urls[:5]:  # Limit to first 5
            entities.append({
                'type': 'URL',
                'name': url,
                'properties': {'mentioned_in': metadata.original_filename}
            })
        
        # Email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        for email in emails[:5]:  # Limit to first 5
            entities.append({
                'type': 'Person',
                'name': email,
                'properties': {'email': email, 'mentioned_in': metadata.original_filename}
            })
        
        return entities
    
    def _create_text_chunks(
        self,
        text: str,
        metadata: FileMetadata
    ) -> List[Dict[str, Any]]:
        """Create text chunks for vector storage."""
        chunks = []
        
        # Simple chunking by character count
        for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
            chunk_text = text[i:i + self.chunk_size]
            if chunk_text.strip():
                chunks.append({
                    'id': f"{metadata.filename.split('_')[0]}_chunk_{len(chunks)}",
                    'text': chunk_text,
                    'metadata': {
                        'source': metadata.source,
                        'filename': metadata.original_filename,
                        'file_type': metadata.file_type,
                        'chunk_index': len(chunks),
                        'project_id': metadata.project_id,
                        'uploaded_by': metadata.uploaded_by,
                        'upload_timestamp': metadata.upload_timestamp.isoformat()
                    }
                })
        
        return chunks
    
    async def _store_in_vector_db(
        self,
        chunks: List[Dict[str, Any]],
        metadata: FileMetadata,
        importance_score: float
    ) -> None:
        """Store chunks in vector database."""
        if not self.vector_service:
            return
        
        documents = []
        for chunk in chunks:
            documents.append({
                'id': chunk['id'],
                'content': chunk['text'],
                'metadata': {
                    **chunk['metadata'],
                    'importance_score': importance_score
                }
            })
        
        await self.vector_service.add_documents(
            project_id=metadata.project_id,
            documents=documents
        )
    
    async def _store_in_knowledge_graph(
        self,
        entities: List[Dict[str, Any]],
        metadata: FileMetadata
    ) -> None:
        """Store entities in knowledge graph."""
        if not self.knowledge_graph_service:
            return
        
        # Add entities to knowledge graph
        for entity in entities:
            await self.knowledge_graph_service.add_entity(
                project_id=metadata.project_id,
                entity_type=entity['type'],
                entity_id=entity['name'],
                properties=entity.get('properties', {})
            )
    
    async def _save_file_to_storage(
        self,
        file_id: str,
        content: bytes,
        project_id: str
    ) -> Path:
        """Save file to storage with project isolation."""
        project_dir = self.storage_path / project_id
        project_dir.mkdir(exist_ok=True)
        
        file_path = project_dir / file_id
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        return file_path
    
    def _determine_file_type(self, filename: str) -> FileType:
        """Determine file type from filename."""
        extension = Path(filename).suffix.lower()
        return self.supported_extensions.get(extension, FileType.UNKNOWN)
    
    def _calculate_checksum(self, content: bytes) -> str:
        """Calculate file checksum."""
        import hashlib
        return hashlib.md5(content).hexdigest()
    
    async def get_file_info(self, file_id: str, project_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a processed file."""
        # This would query the database for file information
        # For now, return mock data
        return {
            'file_id': file_id,
            'project_id': project_id,
            'status': ProcessingStatus.COMPLETED,
            'processed_at': datetime.now().isoformat()
        }
    
    async def delete_file(self, file_id: str, project_id: str, user_id: str) -> bool:
        """Delete a file and its associated data."""
        try:
            # Remove from storage
            file_path = self.storage_path / project_id / file_id
            if file_path.exists():
                file_path.unlink()
            
            # Remove from vector database
            if self.vector_service:
                # This would remove file chunks from vector DB
                pass
            
            # Remove from knowledge graph
            if self.knowledge_graph_service:
                # This would remove file entities from graph
                pass
            
            self.logger.info(f"Deleted file {file_id} from project {project_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting file {file_id}: {str(e)}")
            return False
