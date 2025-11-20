# events/event_publisher.py
import pika
import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class EventPublisher:
    """Publisher for sending events to message queue"""
    
    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange = settings.RABBITMQ_EXCHANGE
        self.routing_key = 'metadata.changes'
        
    def connect(self):
        """Connect to RabbitMQ"""
        try:
            credentials = pika.PlainCredentials(
                settings.RABBITMQ_USER,
                settings.RABBITMQ_PASSWORD
            )
            parameters = pika.ConnectionParameters(
                host=settings.RABBITMQ_HOST,
                port=settings.RABBITMQ_PORT,
                credentials=credentials
            )
            
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declare exchange
            self.channel.exchange_declare(
                exchange=self.exchange,
                exchange_type='topic',
                durable=True
            )
            
        except Exception as e:
            logger.error(f"RabbitMQ connection error: {str(e)}")
            raise
            
    def publish(self, message: dict):
        """Publish message to queue"""
        if not self.connection or self.connection.is_closed:
            self.connect()
            
        try:
            self.channel.basic_publish(
                exchange=self.exchange,
                routing_key=self.routing_key,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Persistent
                    content_type='application/json'
                )
            )
            
            logger.debug(f"Published message: {self.routing_key}")
            
        except Exception as e:
            logger.error(f"Error publishing message: {str(e)}")
            raise
            
    def close(self):
        """Close connection"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()