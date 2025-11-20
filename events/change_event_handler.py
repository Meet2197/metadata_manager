# events/change_event_handler.py
from typing import Dict, Any, Optional
from core.models.relationships import ChangeEvent
from events.event_publisher import EventPublisher
import logging
import json

logger = logging.getLogger(__name__)


class ChangeEventHandler:
    """Handler for change events"""
    
    def __init__(self):
        self.publisher = EventPublisher()
        
    def publish_event(self, entity_type: str, entity_id: str, entity_fqn: str,
                     event_type: str, current_version: Dict, 
                     previous_version: Optional[Dict] = None, user: Any = None):
        """Publish a change event"""
        try:
            # Calculate change description
            change_description = self._calculate_changes(previous_version, current_version)
            
            # Create event record
            event = ChangeEvent.objects.create(
                entity_type=entity_type,
                entity_id=entity_id,
                entity_fqn=entity_fqn,
                event_type=event_type,
                previous_version=previous_version,
                current_version=current_version,
                change_description=change_description,
                user=user
            )
            
            # Publish to message queue
            self.publisher.publish({
                'event_id': str(event.id),
                'entity_type': entity_type,
                'entity_id': entity_id,
                'entity_fqn': entity_fqn,
                'event_type': event_type,
                'change_description': change_description,
                'timestamp': event.timestamp.isoformat(),
                'user': user.username if user else None
            })
            
            logger.info(f"Published change event: {entity_fqn} - {event_type}")
            
        except Exception as e:
            logger.error(f"Error publishing event: {str(e)}")
            raise
            
    def _calculate_changes(self, previous: Optional[Dict], current: Dict) -> Dict:
        """Calculate what changed between versions"""
        if not previous:
            return {'type': 'created'}
            
        changes = {'type': 'updated', 'fields': []}
        
        for key, value in current.items():
            if key in previous:
                if previous[key] != value:
                    changes['fields'].append({
                        'field': key,
                        'old_value': previous[key],
                        'new_value': value
                    })
            else:
                changes['fields'].append({
                    'field': key,
                    'old_value': None,
                    'new_value': value
                })
                
        return changes