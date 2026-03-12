"""Loadout system for managing gear configurations."""

import uuid
from typing import Dict, List, Optional


class Gear:
    """Represents a single gear item."""
    
    def __init__(self, name: str, weight: float = 0.0):
        """Initialize a Gear item.
        
        Args:
            name: Name of the gear item
            weight: Weight in grams (default 0)
        """
        self.id = str(uuid.uuid4())
        self.name = name
        self.weight = weight
    
    def __repr__(self) -> str:
        return f"Gear(id={self.id}, name={self.name}, weight={self.weight})"


class Loadout:
    """Represents a loadout configuration with associated gear items."""
    
    def __init__(self, loadout_id: str, name: str, loadout_type: str = "general"):
        """Initialize a Loadout.
        
        Args:
            loadout_id: Unique identifier for the loadout
            name: Display name for the loadout
            loadout_type: Type of loadout (e.g., 'hiking', 'backpacking', 'general')
        """
        self.id = loadout_id
        self.name = name
        self.loadout_type = loadout_type
        self.gear_items: List[Gear] = []
        self.purpose: Optional[str] = None
        self.tags: List[str] = []
    
    def add_gear(self, gear: Gear) -> None:
        """Add a gear item to this loadout.
        
        Args:
            gear: The Gear item to add
        """
        self.gear_items.append(gear)
    
    def remove_gear(self, gear_id: str) -> None:
        """Remove a gear item from this loadout by ID.
        
        Args:
            gear_id: The ID of the gear item to remove
        """
        self.gear_items = [g for g in self.gear_items if g.id != gear_id]
    
    def __repr__(self) -> str:
        return f"Loadout(id={self.id}, name={self.name}, type={self.loadout_type}, gear_count={len(self.gear_items)})"


class LoadoutManager:
    """Manages loadout persistence and operations."""
    
    def __init__(self):
        """Initialize the LoadoutManager with in-memory database."""
        self._loadouts: Dict[str, Loadout] = {}
    
    def create_loadout(self, name: str, loadout_type: str = "general") -> Loadout:
        """Create a new loadout.
        
        Args:
            name: Display name for the loadout
            loadout_type: Type of loadout (e.g., 'hiking', 'backpacking')
        
        Returns:
            The newly created Loadout object
        """
        loadout_id = str(uuid.uuid4())
        loadout = Loadout(loadout_id=loadout_id, name=name, loadout_type=loadout_type)
        self._loadouts[loadout_id] = loadout
        return loadout
    
    def get_loadout(self, loadout_id: str) -> Optional[Loadout]:
        """Retrieve a loadout by ID.
        
        Args:
            loadout_id: The ID of the loadout to retrieve
        
        Returns:
            The Loadout object if found, None otherwise
        """
        return self._loadouts.get(loadout_id)
    
    def delete_loadout(self, loadout_id: str) -> bool:
        """Delete a loadout by ID.
        
        Args:
            loadout_id: The ID of the loadout to delete
        
        Returns:
            True if the loadout was deleted, False if not found
        """
        if loadout_id in self._loadouts:
            del self._loadouts[loadout_id]
            return True
        return False
    
    def list_loadouts(self) -> List[Loadout]:
        """List all loadouts.
        
        Returns:
            A list of all Loadout objects
        """
        return list(self._loadouts.values())
    
    def clone_loadout(self, original_id: str, new_name: str) -> Loadout:
        """Clone an existing loadout with a new name.
        
        Creates a new Loadout object with:
        - A new unique ID
        - The provided name
        - All gear items from the original (referenced, not duplicated)
        - The same metadata (loadout_type, purpose, tags)
        
        The original loadout is not modified in any way.
        
        Args:
            original_id: The ID of the loadout to clone
            new_name: The name for the new cloned loadout
        
        Returns:
            The newly created cloned Loadout object
        
        Raises:
            ValueError: If the original loadout is not found
        """
        # Retrieve the original loadout
        original = self.get_loadout(original_id)
        if original is None:
            raise ValueError("Loadout not found")
        
        # Create a new loadout with a new ID and the provided name
        cloned = self.create_loadout(name=new_name, loadout_type=original.loadout_type)
        
        # Copy all gear items (by reference)
        for gear in original.gear_items:
            cloned.add_gear(gear)
        
        # Copy metadata
        cloned.purpose = original.purpose
        cloned.tags = original.tags.copy() if original.tags else []
        
        # The new loadout is already persisted to the database via create_loadout()
        return cloned
