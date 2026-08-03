from collections import defaultdict
from decimal import Decimal

def tarjan_scc(G: dict[str, list[str]]) -> list[list[str]]:
    """
    Return a list of strongly connected components in G.
    Each component is a list of nodes.

    Args:
        G: a dict mapping a node to a list of neighbor nodes 
        (no weights).

    Returns:
        A list containing lists of distinct SCCs.
    """
    index = 0
    indices = {}
    low_link = {}
    on_stack = set()
    stack = []
    sccs = []

    # Iterative DFS for each node we start from
    for start in G:
        if start in indices:
            continue

        # Start the first node explicitly
        indices[start] = index
        low_link[start] = index
        index += 1
        on_stack.add(start)
        stack.append(start)

        # Call stack: (node, iterator over neighbors, phase)
        # phase 0: first visit, set up
        # phase 1: backtracking after processing a neighbor
        call_stack = [(start, iter(G.get(start, [])), 0)]
        while call_stack:
            v, neighbor_iter, phase = call_stack[-1]
            # Try to process next neighbor
            try:
                w = next(neighbor_iter)
                if w not in indices:
                    # unvisted node -> recurse, mark for backtracking later
                    call_stack[-1] = (v, neighbor_iter, 1)
                    indices[w] = index
                    low_link[w] = index
                    index += 1
                    on_stack.add(w)
                    stack.append(w)
                    call_stack.append((w, iter(G.get(w, [])), 0))
                elif w in on_stack:
                    # Back edge -> update lowlink
                    low_link[v] = min(low_link[v], indices[w])
            # All neighbors processed, pop and check SCC root
            except StopIteration: 
                call_stack.pop()
                if call_stack:
                    # Update parent's lowlink
                    parent = call_stack[-1][0]
                    low_link[parent] = min(low_link[parent], low_link[v])

                # If v is a root node, pop the stack and form an SCC
                if indices[v] == low_link[v]:
                    scc = []
                    while True:
                        w = stack.pop()
                        on_stack.remove(w)
                        scc.append(w)
                        if w == v:
                            break
                    sccs.append(scc)
    return sccs


# TODO: add with greedy/DP to minimize payment count.
def multilateral_net(
        net_edges: list[tuple[str, str, Decimal]]
    ) -> list[tuple[str, str, Decimal]]:
    """
    Give netted edges from bilateral_net, apply SCC netting.
    Returns a new list of edges after eliminating internal cycles.

    A hub-based settlement where all internal obligations are resolved
    by making the first node the settlement bank. This is not minimal but 
    guarantees correctness.

    Builds a weighted adjacency list to use later in computing net positions.
    Takes the netted edges from bilateral_net and apply SCC netting using 
    Tarjan's algorithm. Maps a node in `sccs` to its scc index to determine 
    if 2 nodes are in the same cycle. Computes the node in each multi-node SCC. 
    Only keeps cross-SCC edges, internal edges (within a cycle) are discarded. 
    Uses hub settlement for each multi-node SCC.

    Args:
        net_edges: list of (payer, payee, amount) tuples from bilateral_net.
    
    Returns:
        List of `(payer, payee, net_amount)` where net_amount > 0. Internal 
        edges are replaced by hub-based settlement and cross-SCC edges are 
        preserved.

    """
    # 1. Build weighted adjacency list: node -> list of (neighbor, amount)
    G = defaultdict(list)
    for payer, payee, amt in net_edges:
        G[payer].append((payee, amt))
        G[payee] # ensure payee appears as key even w/ no outgoing edge

    # 2. Tarjan on the unweighted directed graph (only needs neighbor names)
    unweighted = {node: [neighbor for neighbor, _ in neighbors] for node, neighbors in G.items()}
    sccs = tarjan_scc(unweighted)

    # 3. Map node to its scc id (index); want to know if 2 nodes are in same circle
    node_scc = {}
    for idx, scc in enumerate(sccs):
        for node in scc:
            node_scc[node] = idx

    # 4. Compute net positions within each multi-node SCC
    # positive = new receiver inside SCC, they are owed that amount internally
    net_positions = defaultdict(Decimal)
    in_total = defaultdict(Decimal)
    out_total = defaultdict(Decimal)

    for scc in sccs:
        if len(scc) <= 1:
            continue
        # Calculate internal totals
        for u in scc:
            for v, amt in G[u]:
                if node_scc[v] == node_scc[u]:
                    out_total[u] += amt
                    in_total[v] += amt
        # Net position per node inside SCC
        for node in scc:
            net_positions[node] = in_total[node] - out_total[node]

    # 5. Rebuild edges, keep cross-SCC edges, replace internal ones via hub
    new_edges = []
    for u, neighbors in G.items():
        for v, amt in neighbors:
            if node_scc[u] != node_scc[v]:
                new_edges.append((u, v, amt))

    # 6. Hub settlement for each multi-node SCC
    for scc in sccs:
        if len(scc) <= 1:
            continue
        hub = scc[0]
        for node in scc:
            if hub == node:
                continue
            net = net_positions[node]
            if net > 0: # hub pays node
                new_edges.append((hub, node, net))
            elif net < 0: # node pays hub
                new_edges.append((node, hub, -net))

    return new_edges
