import { useCyberStore } from '../store/cyberStore';

let ws: WebSocket | null = null;

function getApiBaseUrl() {
  return import.meta.env.VITE_API_BASE_URL || '';
}

export function connectWebSocket() {
  const { addLog } = useCyberStore.getState();
  const apiBase = getApiBaseUrl();
  
  let wsUrl: string;
  if (apiBase) {
    const url = new URL(apiBase);
    const protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
    wsUrl = `${protocol}//${url.host}/ws/logs`;
  } else {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    wsUrl = `${protocol}//${window.location.host}/ws/logs`;
  }
  
  ws = new WebSocket(wsUrl);
  
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      
      // Handle different message types
      if (data.type === 'containment_update') {
        // Update containment history in store
        const { containmentHistory } = useCyberStore.getState();
        const updatedHistory = [...containmentHistory];
        const index = updatedHistory.findIndex(a => a.action_id === data.data.action_id);
        
        if (index !== -1) {
          updatedHistory[index] = data.data;
        } else {
          updatedHistory.push(data.data);
        }
        
        useCyberStore.setState({ containmentHistory: updatedHistory });
        
        // Also fetch the latest incidents to update statuses
        useCyberStore.getState().refreshPlatform();
        
      } else if (data.type === 'incident_update') {
        // Update the specific incident's status
        const { incidents } = useCyberStore.getState();
        const updatedIncidents = incidents.map(incident => {
          if (incident.incident_id === data.data.incident_id) {
            return { ...incident, status: data.data.status };
          }
          return incident;
        });
        
        useCyberStore.setState({ incidents: updatedIncidents });
        
      } else {
        // Assume it's a log event
        addLog(data);
      }
      
    } catch (e) {
      console.error('Failed to parse WS message', e);
    }
  };
  
  ws.onclose = () => {
    setTimeout(() => connectWebSocket(), 3000);
  };
}

export function disconnectWebSocket() {
  if (ws) {
    ws.close();
    ws = null;
  }
}
