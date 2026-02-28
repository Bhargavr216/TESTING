import json
import logging
from typing import Any
try:
    from azure.eventhub import EventHubProducerClient, EventData
except ImportError:
    # Fallback for local dev without azure-eventhub installed
    EventHubProducerClient = None
    EventData = None

class AzureEventHubProducer:
    @staticmethod
    def trigger_event(connection_string: str, event_hub_name: str, payload: Any):
        """
        Triggers a real event to Azure Event Hub.
        """
        if not EventHubProducerClient:
            logging.warning("azure-eventhub package not installed. Skipping real trigger.")
            return False
            
        try:
            producer = EventHubProducerClient.from_connection_string(
                conn_str=connection_string, 
                eventhub_name=event_hub_name
            )
            
            with producer:
                event_data_batch = producer.create_batch()
                
                # If payload is a list, send all items
                if isinstance(payload, list):
                    for item in payload:
                        event_data_batch.add(EventData(json.dumps(item)))
                else:
                    event_data_batch.add(EventData(json.dumps(payload)))
                
                producer.send_batch(event_data_batch)
                logging.info(f"Successfully triggered event to {event_hub_name}")
                return True
        except Exception as e:
            logging.error(f"Failed to trigger event to Azure Event Hub: {str(e)}")
            return False
