import { useCallback, useMemo } from 'react';
import ReactFlow, {
  ReactFlowProvider,
  addEdge,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  FitViewOptions,
  Node,
  Edge,
} from 'reactflow';
import { useCyberStore } from '../../store/cyberStore';
import AssetNode from './AssetNode';
import { AssetType } from '../../types';

const nodeTypes = {
  assetNode: AssetNode,
};

const fitViewOptions: FitViewOptions = {
  padding: 0.2,
};

const TIER_ORDER: AssetType[] = ['firewall', 'vpn', 'server', 'database', 'endpoint', 'unknown'];
const TIER_X = {
  firewall: 100,
  vpn: 350,
  server: 600,
  database: 850,
  endpoint: 1100,
  unknown: 1350,
};
const NODE_GAP = 150;

function AssetGraphInner() {
  const { assets, riskScores, setSelectedAsset } = useCyberStore();

  // Group assets by type
  const groupedAssets = useMemo(() => {
    const groups: Record<AssetType, typeof assets> = {
      firewall: [],
      vpn: [],
      server: [],
      database: [],
      endpoint: [],
      unknown: [],
    };
    assets.forEach(asset => {
      const type = (asset.asset_type.toLowerCase() as AssetType) || 'unknown';
      groups[type in groups ? type : 'unknown'].push(asset);
    });
    return groups;
  }, [assets]);

  // Create nodes
  const initialNodes: Node[] = useMemo(() => {
    const nodes: Node[] = [];
    TIER_ORDER.forEach(tier => {
      groupedAssets[tier].forEach((asset, idx) => {
        const riskScore = riskScores.find(r => r.asset_id === asset.asset_id);
        nodes.push({
          id: asset.asset_id,
          type: 'assetNode',
          position: {
            x: TIER_X[tier],
            y: 100 + idx * NODE_GAP,
          },
          data: {
            label: asset.name,
            type: asset.asset_type,
            criticality: riskScore?.severity || asset.criticality,
          },
        });
      });
    });
    return nodes;
  }, [groupedAssets, riskScores]);

  // Create edges (deterministic)
  const initialEdges: Edge[] = useMemo(() => {
    const edges: Edge[] = [];
    let edgeId = 0;

    // Firewall -> VPN
    groupedAssets.firewall.forEach(fw => {
      groupedAssets.vpn.forEach(vpn => {
        edges.push({ id: `e-${edgeId++}`, source: fw.asset_id, target: vpn.asset_id, animated: false });
      });
    });
    // VPN -> Server
    groupedAssets.vpn.forEach(vpn => {
      groupedAssets.server.forEach(srv => {
        edges.push({ id: `e-${edgeId++}`, source: vpn.asset_id, target: srv.asset_id, animated: false });
      });
    });
    // Server -> Database
    groupedAssets.server.forEach(srv => {
      groupedAssets.database.forEach(db => {
        edges.push({ id: `e-${edgeId++}`, source: srv.asset_id, target: db.asset_id, animated: false });
      });
    });
    // Server -> Endpoint
    groupedAssets.server.forEach(srv => {
      groupedAssets.endpoint.forEach(ep => {
        edges.push({ id: `e-${edgeId++}`, source: srv.asset_id, target: ep.asset_id, animated: false });
      });
    });

    return edges;
  }, [groupedAssets]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback(
    (params: any) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    const asset = assets.find(a => a.asset_id === node.id);
    if (asset) setSelectedAsset(asset);
  }, [assets, setSelectedAsset]);

  return (
    <div className="h-[calc(100vh-200px)]">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={fitViewOptions}
      >
        <Background />
        <Controls />
      </ReactFlow>
    </div>
  );
}

export default function AssetGraph() {
  return (
    <ReactFlowProvider>
      <AssetGraphInner />
    </ReactFlowProvider>
  );
}
