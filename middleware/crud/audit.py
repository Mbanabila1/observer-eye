"""
Audit trail system for CRUD operations.
Tracks all CRUD operations with detailed logging and change tracking.
"""

import json
import hashlib
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass, asdict
import structlog

from .models import CRUDOperation, AuditLogEntry
from .exceptions import CRUDError

logger = structlog.get_logger(__name__)


@dataclass
class ChangeRecord:
    """Record of a field change"""
    field: str
    old_value: Any
    new_value: Any
    change_type: str  # 'created', 'updated', 'deleted'


class AuditTrail:
    """
    Audit trail system for tracking CRUD operations.
    Provides comprehensive logging and change tracking.
    """
    
    def __init__(self, enable_detailed_logging: bool = True):
        self.enable_detailed_logging = enable_detailed_logging
        self.logger = structlog.get_logger(__name__)
    
    async def log_operation(
        self,
        operation: CRUDOperation,
        entity_type: str,
        entity_id: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        old_data: Optional[Dict[str, Any]] = None,
        new_data: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> AuditLogEntry:
        """
        Log a CRUD operation to the audit trail.
        
        Args:
            operation: CRUD operation type
            entity_type: Type of entity being operated on
            entity_id: ID of the entity
            user_id: ID of user performing the operation
            ip_address: IP address of the request
            user_agent: User agent string
            old_data: Previous entity data (for updates/deletes)
            new_data: New entity data (for creates/updates)
            success: Whether the operation was successful
            error_message: Error message if operation failed
            additional_context: Additional context information
        
        Returns:
            AuditLogEntry: The created audit log entry
        """
        try:
            # Calculate changes
            changes = self._calculate_changes(old_data, new_data, operation)
            
            # Create audit log entry
            audit_entry = AuditLogEntry(
                operation=operation,
                entity_type=entity_type,
                entity_id=entity_id,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                changes=changes,
                old_values=old_data or {},
                new_values=new_data or {},
                timestamp=datetime.utcnow(),
                success=success,
                error_message=error_message
            )
            
            # Log to structured logger
            log_data = {
                "audit_operation": operation.value,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "user_id": user_id,
                "ip_address": ip_address,
                "success": success,
                "changes_count": len(changes),
                "timestamp": audit_entry.timestamp.isoformat()
            }
            
            if additional_context:
                log_data.update(additional_context)
            
            if success:
                self.logger.info("CRUD operation completed", **log_data)
            else:
                log_data["error_message"] = error_message
                self.logger.error("CRUD operation failed", **log_data)
            
            # Store audit entry (this would typically go to a database)
            await self._store_audit_entry(audit_entry)
            
            return audit_entry
            
        except Exception as e:
            self.logger.error(
                "Failed to log audit entry",
                operation=operation.value,
                entity_type=entity_type,
                entity_id=entity_id,
                error=str(e)
            )
            raise CRUDError(f"Audit logging failed: {str(e)}")
    
    def _calculate_changes(
        self,
        old_data: Optional[Dict[str, Any]],
        new_data: Optional[Dict[str, Any]],
        operation: CRUDOperation
    ) -> Dict[str, Any]:
        """
        Calculate changes between old and new data.
        
        Args:
            old_data: Previous entity data
            new_data: New entity data
            operation: CRUD operation type
        
        Returns:
            Dict containing change information
        """
        changes = {
            "operation_type": operation.value,
            "field_changes": [],
            "summary": {}
        }
        
        if operation == CRUDOperation.CREATE:
            if new_data:
                changes["summary"] = {
                    "action": "created",
                    "fields_set": len(new_data),
                    "new_fields": list(new_data.keys())
                }
                for field, value in new_data.items():
                    changes["field_changes"].append({
                        "field": field,
                        "change_type": "created",
                        "old_value": None,
                        "new_value": self._sanitize_value(value)
                    })
        
        elif operation == CRUDOperation.UPDATE:
            if old_data and new_data:
                modified_fields = []
                added_fields = []
                removed_fields = []
                
                # Find modified and added fields
                for field, new_value in new_data.items():
                    old_value = old_data.get(field)
                    if field not in old_data:
                        added_fields.append(field)
                        changes["field_changes"].append({
                            "field": field,
                            "change_type": "added",
                            "old_value": None,
                            "new_value": self._sanitize_value(new_value)
                        })
                    elif old_value != new_value:
                        modified_fields.append(field)
                        changes["field_changes"].append({
                            "field": field,
                            "change_type": "modified",
                            "old_value": self._sanitize_value(old_value),
                            "new_value": self._sanitize_value(new_value)
                        })
                
                # Find removed fields
                for field in old_data:
                    if field not in new_data:
                        removed_fields.append(field)
                        changes["field_changes"].append({
                            "field": field,
                            "change_type": "removed",
                            "old_value": self._sanitize_value(old_data[field]),
                            "new_value": None
                        })
                
                changes["summary"] = {
                    "action": "updated",
                    "modified_fields": len(modified_fields),
                    "added_fields": len(added_fields),
                    "removed_fields": len(removed_fields),
                    "total_changes": len(modified_fields) + len(added_fields) + len(removed_fields)
                }
        
        elif operation == CRUDOperation.DELETE:
            if old_data:
                changes["summary"] = {
                    "action": "deleted",
                    "fields_removed": len(old_data),
                    "deleted_fields": list(old_data.keys())
                }
                for field, value in old_data.items():
                    changes["field_changes"].append({
                        "field": field,
                        "change_type": "deleted",
                        "old_value": self._sanitize_value(value),
                        "new_value": None
                    })
        
        return changes
    
    def _sanitize_value(self, value: Any) -> Any:
        """
        Sanitize sensitive values for logging.
        
        Args:
            value: Value to sanitize
        
        Returns:
            Sanitized value
        """
        if value is None:
            return None
        
        # Convert to string for analysis
        str_value = str(value).lower()
        
        # List of sensitive field patterns
        sensitive_patterns = [
            'password', 'passwd', 'pwd', 'secret', 'token', 'key',
            'api_key', 'auth', 'credential', 'private', 'confidential'
        ]
        
        # Check if this looks like a sensitive value
        if any(pattern in str_value for pattern in sensitive_patterns):
            return "***REDACTED***"
        
        # Truncate very long values
        if isinstance(value, str) and len(value) > 1000:
            return value[:1000] + "...[truncated]"
        
        # Handle complex objects
        if isinstance(value, (dict, list)):
            try:
                json_str = json.dumps(value)
                if len(json_str) > 1000:
                    return f"<{type(value).__name__} with {len(value)} items>"
                return value
            except (TypeError, ValueError):
                return f"<{type(value).__name__} object>"
        
        return value
    
    async def _store_audit_entry(self, audit_entry: AuditLogEntry) -> None:
        """
        Store audit entry to persistent storage.
        This would typically save to a database or audit log service.
        
        Args:
            audit_entry: Audit entry to store
        """
        # In a real implementation, this would save to Django's AuditLog model
        # For now, we'll just log it
        if self.enable_detailed_logging:
            self.logger.info(
                "Audit entry created",
                audit_data=audit_entry.dict()
            )
    
    def generate_audit_hash(self, data: Dict[str, Any]) -> str:
        """
        Generate a hash for audit data integrity.
        
        Args:
            data: Data to hash
        
        Returns:
            SHA-256 hash of the data
        """
        # Sort keys for consistent hashing
        sorted_data = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(sorted_data.encode()).hexdigest()
    
    async def get_entity_history(
        self,
        entity_type: str,
        entity_id: str,
        limit: int = 100
    ) -> List[AuditLogEntry]:
        """
        Get audit history for a specific entity.
        
        Args:
            entity_type: Type of entity
            entity_id: ID of entity
            limit: Maximum number of entries to return
        
        Returns:
            List of audit log entries
        """
        # This would query the audit log database
        # For now, return empty list
        return []
    
    async def get_user_activity(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditLogEntry]:
        """
        Get audit history for a specific user.
        
        Args:
            user_id: ID of user
            start_date: Start date for filtering
            end_date: End date for filtering
            limit: Maximum number of entries to return
        
        Returns:
            List of audit log entries
        """
        # This would query the audit log database
        # For now, return empty list
        return []
    
    def create_change_summary(self, changes: Dict[str, Any]) -> str:
        """
        Create a human-readable summary of changes.
        
        Args:
            changes: Changes dictionary
        
        Returns:
            Human-readable change summary
        """
        if not changes or not changes.get("field_changes"):
            return "No changes recorded"
        
        summary = changes.get("summary", {})
        operation = summary.get("action", "unknown")
        
        if operation == "created":
            field_count = summary.get("fields_set", 0)
            return f"Entity created with {field_count} fields"
        
        elif operation == "updated":
            modified = summary.get("modified_fields", 0)
            added = summary.get("added_fields", 0)
            removed = summary.get("removed_fields", 0)
            
            parts = []
            if modified > 0:
                parts.append(f"{modified} modified")
            if added > 0:
                parts.append(f"{added} added")
            if removed > 0:
                parts.append(f"{removed} removed")
            
            return f"Entity updated: {', '.join(parts)} fields"
        
        elif operation == "deleted":
            field_count = summary.get("fields_removed", 0)
            return f"Entity deleted ({field_count} fields removed)"
        
        return f"Entity {operation}"