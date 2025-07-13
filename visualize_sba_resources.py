import requests
import matplotlib.pyplot as plt
import networkx as nx

# Fetch SBA resources from the API
API_URL = "http://localhost:5000/api/resources"
try:
    response = requests.get(API_URL)
    response.raise_for_status()
    resources = response.json()
except Exception as e:
    print(f"Failed to fetch SBA resources: {e}")
    resources = []

# Create a graph
G = nx.Graph()
for resource in resources:
    G.add_node(resource['name'], desc=resource['description'])

# Example: Connect all resources to a central SBA node
G.add_node("SBA Resources", desc="Central Node")
for resource in resources:
    G.add_edge("SBA Resources", resource['name'])

# Draw the graph
plt.figure(figsize=(10, 7))
pos = nx.spring_layout(G, seed=42)
nx.draw(G, pos, with_labels=True, node_color='skyblue', node_size=2000, font_size=10, font_weight='bold', edge_color='#1976d2')
plt.title("SBA Resources Network Graph")
plt.tight_layout()
plt.show()

# For Plotly interactive visualization
try:
    import plotly.graph_objects as go
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]
    edge_trace = go.Scatter(x=edge_x, y=edge_y, line=dict(width=1, color='#888'), hoverinfo='none', mode='lines')
    node_x = []
    node_y = []
    node_text = []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(f"{node}: {G.nodes[node].get('desc', '')}")
    node_trace = go.Scatter(x=node_x, y=node_y, mode='markers+text', text=node_text, textposition='top center', marker=dict(size=30, color='skyblue', line=dict(width=2)), hoverinfo='text')
    fig = go.Figure(data=[edge_trace, node_trace], layout=go.Layout(
        title='SBA Resources Interactive Graph',
        showlegend=False,
        hovermode='closest',
        margin=dict(b=20,l=5,r=5,t=40),
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=False, zeroline=False)
    ))
    fig.show()
except ImportError:
    print("Plotly not installed. Only matplotlib visualization shown.")
