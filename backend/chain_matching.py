"""
Chain Matching Module

Handles discovery of multi-way exchange chains (3+ participants).
Works in conjunction with existing bilateral matching system.

Architecture:
1. Unilateral Edges: Save ALL matching possibilities (even 1-way)
2. Graph Building: Create graph of wants → offers relationships
3. Cycle Detection: Use DFS to find closed loops
4. Chain Creation: Create ExchangeChain records when cycles found
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Dict, Set, Tuple, Optional
from backend.models import Item, User, Match, Notification
from backend.schemas import NotificationCreate
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# STEP 1: UNILATERAL EDGE CREATION
# ============================================================================

def create_unilateral_edge(db: Session, from_item: Item, to_item: Item, score: float) -> Dict:
    """
    Create unilateral edge: from_item.want matches to_item.offer
    
    Args:
        db: Database session
        from_item: Item with wants (what user wants)
        to_item: Item with offers (what other user offers)
        score: Matching score (0.0-1.0)
    
    Returns:
        Edge dictionary for graph building
    
    Note:
        This is a directed edge: from_item.user WANTS to_item.user's offer
    """
    
    edge = {
        "from_user": from_item.user_id,
        "from_item": from_item.id,
        "to_user": to_item.user_id,
        "to_item": to_item.id,
        "score": score,
        "direction": "unilateral"
    }
    
    logger.debug(f"Created unilateral edge: User {from_item.user_id} wants from User {to_item.user_id}")
    return edge


def get_all_unilateral_edges(db: Session, category: Optional[str] = None) -> List[Dict]:
    """
    Get all unilateral matching edges (even 1-way matches).
    These form the basis for chain discovery.
    
    Strategy:
    - Find all offers and wants
    - Calculate pairwise similarities
    - Check location overlap (at least one matching city)
    - Return edges with score > threshold
    """
    
    # Get all active items
    items = db.query(Item).filter(Item.active == True).all()
    
    edges = []
    threshold = 0.3  # Minimum score for edge inclusion
    
    for item in items:
        if item.kind == 2:  # wants (wants to get something)
            # Get item owner's locations
            item_user = db.query(User).filter(User.id == item.user_id).first()
            if not item_user or not item_user.locations:
                continue
            
            # Find items this user wants
            candidates = db.query(Item).filter(
                and_(
                    Item.kind == 1,  # offers
                    Item.user_id != item.user_id,  # not own items
                    Item.category == item.category,
                    Item.active == True
                )
            ).all()
            
            for candidate in candidates:
                # Check location overlap
                candidate_user = db.query(User).filter(User.id == candidate.user_id).first()
                if not candidate_user or not candidate_user.locations:
                    continue
                
                # Must have at least one matching location
                matching_locations = set(item_user.locations) & set(candidate_user.locations)
                if not matching_locations:
                    continue
                
                # Calculate similarity (simplified)
                score = _calculate_similarity(item, candidate)
                
                if score > threshold:
                    edge = create_unilateral_edge(db, item, candidate, score)
                    edges.append(edge)
    
    logger.info(f"Found {len(edges)} unilateral edges (with location filtering)")
    return edges


# ============================================================================
# STEP 2: GRAPH BUILDING & DFS CYCLE DETECTION
# ============================================================================

class ChainGraph:
    """Graph representation for chain discovery using DFS"""
    
    def __init__(self, edges: List[Dict]):
        self.edges = edges
        self.graph = self._build_adjacency_list()
    
    def _build_adjacency_list(self) -> Dict:
        """Build adjacency list: user_id → [(neighbor_user_id, score), ...]"""
        graph = {}
        
        for edge in self.edges:
            from_user = edge["from_user"]
            to_user = edge["to_user"]
            score = edge["score"]
            
            if from_user not in graph:
                graph[from_user] = []
            
            graph[from_user].append((to_user, score, edge))
        
        return graph
    
    def find_cycles(self, min_length: int = 3, max_length: int = 10) -> List[List[Dict]]:
        """
        Find all cycles in the graph using DFS.
        
        Cycles represent valid exchange chains where:
        - Each user appears exactly once
        - All connections are valid (score > threshold)
        - Length is between min_length and max_length
        """
        
        cycles = []
        visited_globally = set()
        
        for start_user in self.graph:
            visited = set()
            path = []
            path_edges = []
            
            self._dfs_cycle(
                start_user, start_user, visited, path, path_edges,
                cycles, min_length, max_length
            )
        
        # Remove duplicates (same cycle starting from different users)
        unique_cycles = self._deduplicate_cycles(cycles)
        logger.info(f"Found {len(unique_cycles)} unique cycles")
        return unique_cycles
    
    def _dfs_cycle(self, current: int, start: int, visited: Set[int], 
                   path: List[int], path_edges: List[Dict],
                   cycles: List, min_len: int, max_len: int):
        """
        DFS helper to find cycles.
        
        Args:
            current: Current node (user_id)
            start: Starting node for cycle
            visited: Set of visited nodes in this path
            path: Current path of users
            path_edges: Edges traversed in path
            cycles: List to accumulate found cycles
            min_len: Minimum cycle length
            max_len: Maximum cycle length
        """
        
        if current in self.graph:
            for next_user, score, edge in self.graph[current]:
                
                # Check if we've completed a valid cycle back to start
                if next_user == start and len(path) >= min_len:
                    if len(path) <= max_len:
                        cycles.append(list(path_edges))
                    return
                
                # Continue DFS if node not visited
                if next_user not in visited and len(path) < max_len:
                    visited.add(next_user)
                    path.append(next_user)
                    path_edges.append(edge)
                    
                    self._dfs_cycle(
                        next_user, start, visited, path, path_edges,
                        cycles, min_len, max_len
                    )
                    
                    path.pop()
                    path_edges.pop()
                    visited.remove(next_user)
    
    def _deduplicate_cycles(self, cycles: List[List[Dict]]) -> List[List[Dict]]:
        """Remove duplicate cycles (same cycle from different starting points)"""
        
        unique = []
        seen = set()
        
        for cycle in cycles:
            # Create canonical representation
            user_sequence = tuple(sorted([edge["from_user"] for edge in cycle]))
            
            if user_sequence not in seen:
                seen.add(user_sequence)
                unique.append(cycle)
        
        return unique


def _calculate_similarity(item_a: Item, item_b: Item) -> float:
    """Calculate similarity between two items"""
    
    # Same category: base score
    base_score = 1.0 if item_a.category == item_b.category else 0.5
    
    # Text similarity (simplified)
    text_score = 0.3  # Default
    if item_a.description and item_b.description:
        # Basic word overlap
        words_a = set((item_a.description or "").lower().split())
        words_b = set((item_b.description or "").lower().split())
        
        if words_a and words_b:
            overlap = len(words_a & words_b)
            text_score = overlap / max(len(words_a), len(words_b))
    
    return base_score * 0.7 + text_score * 0.3


# ============================================================================
# STEP 3: EXCHANGE CHAIN CREATION
# ============================================================================

def create_exchange_chain(db: Session, cycle_edges: List[Dict]) -> Optional[Dict]:
    """
    Create ExchangeChain record from discovered cycle.
    
    Args:
        db: Database session
        cycle_edges: List of edges forming a cycle
    
    Returns:
        Created chain or None if validation fails
    """
    
    if len(cycle_edges) < 3:
        logger.warning("Chain must have at least 3 participants")
        return None
    
    # Extract participants and items
    participants = []
    items_map = {}
    total_score = 0.0
    
    for edge in cycle_edges:
        participants.append(edge["from_user"])
        items_map[edge["from_user"]] = edge["from_item"]
        total_score += edge["score"]
    
    # Validate: no duplicate participants
    if len(set(participants)) != len(participants):
        logger.warning("Invalid chain: duplicate participants")
        return None
    
    avg_score = total_score / len(cycle_edges)
    
    # Create chain record
    chain = {
        "participants": participants,
        "items": items_map,
        "total_score": avg_score,
        "status": "proposed",
        "type": f"chain_{len(participants)}_way"
    }
    
    logger.info(f"Created {len(participants)}-way exchange chain with score {avg_score:.2f}")
    return chain


def save_exchange_chain_to_db(db: Session, chain: Dict) -> Optional[int]:
    """Save exchange chain to database"""
    
    try:
        from backend.models import ExchangeChain
        
        db_chain = ExchangeChain(
            participants=chain["participants"],
            items=chain["items"],
            total_score=chain["total_score"],
            status=chain["status"]
        )
        
        db.add(db_chain)
        db.commit()
        db.refresh(db_chain)
        
        logger.info(f"Saved exchange chain ID {db_chain.id}")
        return db_chain.id
    
    except Exception as e:
        logger.error(f"Failed to save exchange chain: {e}")
        db.rollback()
        return None


# ============================================================================
# STEP 4: NOTIFICATION CREATION FOR CHAINS
# ============================================================================

def create_chain_notifications(db: Session, chain: Dict, chain_id: int):
    """
    Create notifications for all participants in exchange chain.
    
    Each participant is informed about:
    - Who will give them items (previous in cycle)
    - Who will receive their items (next in cycle)
    - The chain score
    """
    
    participants = chain["participants"]
    items_map = chain["items"]
    
    for i, participant_id in enumerate(participants):
        prev_participant = participants[i - 1]  # Last person in chain
        next_participant = participants[(i + 1) % len(participants)]
        
        # Get users to access contact info
        from_user = db.query(User).filter(User.id == prev_participant).first()
        to_user = db.query(User).filter(User.id == next_participant).first()
        
        if not from_user or not to_user:
            continue
        
        payload = {
            "type": "exchange_chain",
            "chain_id": chain_id,
            "chain_length": len(participants),
            "chain_score": chain["total_score"],
            "giver": {
                "user_id": from_user.id,
                "username": from_user.username,
                "contact": from_user.contact
            },
            "receiver": {
                "user_id": to_user.id,
                "username": to_user.username,
                "contact": to_user.contact
            },
            "message": f"Вы участник {len(participants)}-сторонней цепочки обмена!"
        }
        
        notification = NotificationCreate(
            user_id=participant_id,
            payload=payload
        )
        
        # Create notification
        from backend.crud import create_notification
        create_notification(db, notification)


# ============================================================================
# MAIN ORCHESTRATION
# ============================================================================

def discover_and_create_chains(db: Session) -> int:
    """
    Main function to discover all possible exchange chains.
    
    Flow:
    1. Get all unilateral edges
    2. Build graph
    3. Find cycles
    4. Create chain records
    5. Send notifications
    
    Returns:
        Number of chains created
    """
    
    logger.info("=== Starting chain discovery ===")
    
    # Step 1: Get edges
    edges = get_all_unilateral_edges(db)
    
    if not edges:
        logger.info("No unilateral edges found")
        return 0
    
    # Step 2: Build graph
    graph = ChainGraph(edges)
    
    # Step 3: Find cycles
    cycles = graph.find_cycles(min_length=3, max_length=10)
    
    if not cycles:
        logger.info("No valid cycles found")
        return 0
    
    # Step 4 & 5: Create chains and notifications
    chains_created = 0
    
    for cycle_edges in cycles:
        chain = create_exchange_chain(db, cycle_edges)
        
        if chain:
            chain_id = save_exchange_chain_to_db(db, chain)
            
            if chain_id:
                create_chain_notifications(db, chain, chain_id)
                chains_created += 1
    
    logger.info(f"=== Chain discovery complete: {chains_created} chains created ===")
    return chains_created
