import pytest
from loadout.loadout_system import LoadoutManager, Gear, Loadout


def test_clone_loadout_creates_independent_copy():
    """
    SPEC: Cloning a loadout creates a new independent loadout with:
    - New unique name provided by user
    - All gear items copied from original
    - Original loadout unchanged
    - Modifications to clone do not affect original
    """
    manager = LoadoutManager()

    # Setup: Create original loadout with gear items
    gear1 = Gear(name="Backpack", weight=1500)
    gear2 = Gear(name="Tent", weight=2000)
    original = manager.create_loadout(name="Hiking Setup", loadout_type="hiking")
    original.add_gear(gear1)
    original.add_gear(gear2)
    original_gear_count = len(original.gear_items)

    # Action: Clone the loadout
    cloned = manager.clone_loadout(original_id=original.id, new_name="Hiking Setup 2")

    # Assert: Cloned loadout has correct properties
    assert cloned.name == "Hiking Setup 2"
    assert cloned.id != original.id
    assert len(cloned.gear_items) == original_gear_count

    # Assert: All gear items are present in clone
    original_gear_ids = {g.id for g in original.gear_items}
    cloned_gear_ids = {g.id for g in cloned.gear_items}
    assert original_gear_ids == cloned_gear_ids

    # Assert: Original is unchanged
    assert original.name == "Hiking Setup"
    assert len(original.gear_items) == original_gear_count

    # Assert: Modification to clone does not affect original
    new_gear = Gear(name="Sleeping Bag", weight=1200)
    cloned.add_gear(new_gear)
    assert len(cloned.gear_items) == original_gear_count + 1
    assert len(original.gear_items) == original_gear_count


def test_clone_loadout_preserves_loadout_metadata():
    """
    SPEC: Cloning preserves loadout type and other metadata from original
    """
    manager = LoadoutManager()
    original = manager.create_loadout(name="Original", loadout_type="backpacking")
    original.purpose = "summer backpacking trip"
    original.tags = ["summer", "long-distance"]

    cloned = manager.clone_loadout(original_id=original.id, new_name="Cloned")

    assert cloned.loadout_type == original.loadout_type
    assert cloned.purpose == original.purpose
    assert cloned.tags == original.tags


def test_clone_nonexistent_loadout_raises_error():
    """
    SPEC: Attempting to clone a nonexistent loadout raises appropriate error
    """
    manager = LoadoutManager()

    with pytest.raises(ValueError, match="Loadout not found"):
        manager.clone_loadout(original_id=99999, new_name="New")


def test_clone_persists_to_database():
    """
    SPEC: Cloned loadout is saved to database and can be retrieved
    """
    manager = LoadoutManager()
    original = manager.create_loadout(name="Original", loadout_type="hiking")
    original_id = original.id

    cloned = manager.clone_loadout(original_id=original_id, new_name="Cloned")
    cloned_id = cloned.id

    # Verify cloned loadout can be retrieved from database
    retrieved = manager.get_loadout(cloned_id)
    assert retrieved is not None
    assert retrieved.name == "Cloned"
    assert retrieved.id == cloned_id
