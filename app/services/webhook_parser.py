# app/services/webhook_parser.py
import hmac
import hashlib
import json
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from app.core.config import settings

class WebhookVerifier:
    """
    Verify GitHub/GitLab webhook signatures
    """
    
    @staticmethod
    def verify_github_signature(
        payload_body: bytes, 
        signature_header: str, 
        secret: str
    ) -> bool:
        """
        Verify GitHub webhook signature
        """
        if not signature_header:
            return False
        
        # GitHub sends signature as "sha256=..."
        if signature_header.startswith("sha256="):
            signature_header = signature_header[7:]
        
        # Create HMAC hex digest
        mac = hmac.new(
            secret.encode('utf-8'), 
            msg=payload_body, 
            digestmod=hashlib.sha256
        )
        expected_signature = mac.hexdigest()
        
        # Compare signatures
        return hmac.compare_digest(expected_signature, signature_header)
    
    @staticmethod
    def verify_gitlab_signature(
        payload_body: bytes,
        token_header: str,
        secret: str
    ) -> bool:
        """
        Verify GitLab webhook signature
        """
        return token_header == secret

class GitHubWebhookParser:
    """
    Parse GitHub webhook payloads
    """
    
    @staticmethod
    def parse_push_event(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Parse GitHub push event"""
        return {
            "event_type": "push",
            "ref": payload.get("ref", ""),
            "before": payload.get("before", ""),
            "after": payload.get("after", ""),
            "repository": payload.get("repository", {}),
            "commits": payload.get("commits", []),
            "head_commit": payload.get("head_commit", {}),
        }
    
    @staticmethod
    def parse_workflow_run_event(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Parse GitHub workflow_run event"""
        workflow_run = payload.get("workflow_run", {})
        return {
            "event_type": "workflow_run",
            "action": payload.get("action", ""),
            "workflow_name": workflow_run.get("name", ""),
            "status": workflow_run.get("status", ""),
            "conclusion": workflow_run.get("conclusion", ""),
            "html_url": workflow_run.get("html_url", ""),
            "head_sha": workflow_run.get("head_sha", ""),
            "repository": payload.get("repository", {}),
        }
    
    @staticmethod
    def parse_check_run_event(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Parse GitHub check_run event"""
        check_run = payload.get("check_run", {})
        return {
            "event_type": "check_run",
            "action": payload.get("action", ""),
            "status": check_run.get("status", ""),
            "conclusion": check_run.get("conclusion", ""),
            "name": check_run.get("name", ""),
            "html_url": check_run.get("html_url", ""),
            "head_sha": check_run.get("head_sha", ""),
            "repository": payload.get("repository", {}),
        }
    
    @staticmethod
    def parse_ping_event(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Parse GitHub ping event"""
        return {
            "event_type": "ping",
            "zen": payload.get("zen", ""),
            "hook_id": payload.get("hook_id", ""),
        }
    
    @staticmethod
    def parse_event(headers: Dict[str, str], payload: Dict[str, Any]) -> Dict[str, Any]:
        """Parse any GitHub webhook event"""
        event_type = headers.get("x-github-event", "")
        
        parsers = {
            "push": GitHubWebhookParser.parse_push_event,
            "workflow_run": GitHubWebhookParser.parse_workflow_run_event,
            "check_run": GitHubWebhookParser.parse_check_run_event,
            "ping": GitHubWebhookParser.parse_ping_event,
        }
        
        if event_type in parsers:
            return parsers[event_type](payload)
        
        # Default parsing for unknown events
        return {
            "event_type": event_type,
            "action": payload.get("action", ""),
            "raw_payload": payload,
        }