"""
reset.py
Resets the Minecraft world state between simulation seeds.
Uses RCON to clear inventories, teleport agents to spawn, reset time, etc.
"""

from orchestrator.minecraft import rcon_client

# Spawn coordinates for agents (spread them around the starting area)
SPAWN_POSITIONS = [
    (0, 64, 0), (5, 64, 0), (-5, 64, 0), (0, 64, 5), (0, 64, -5),
    (10, 64, 0), (-10, 64, 0), (0, 64, 10), (0, 64, -10), (5, 64, 5),
    (-5, 64, 5), (5, 64, -5), (-5, 64, -5), (10, 64, 5), (-10, 64, 5),
    (10, 64, -5), (-10, 64, -5), (0, 64, 15), (5, 64, 15), (-5, 64, 15),
]


async def reset_world(seed: int, agent_names: list[str]) -> None:
    """
    Prepare the world for a new simulation seed.
    Clears inventories, teleports all agents to spawn, sets time to dawn.
    """
    print(f"[reset] Resetting world for seed {seed}...")

    # Set time to dawn
    rcon_client.set_time(0)
    rcon_client.set_weather("clear")

    # Give each agent their starting kit and teleport to spawn
    for i, name in enumerate(agent_names):
        x, y, z = SPAWN_POSITIONS[i % len(SPAWN_POSITIONS)]
        rcon_client.clear_inventory(name)
        rcon_client.tp_agent(name, x, y, z)
        # Starting kit: some food and a wooden sword
        rcon_client.give_item(name, "bread", 10)
        rcon_client.give_item(name, "wooden_sword", 1)

    print(f"[reset] World reset complete for seed {seed}.")


async def trigger_breach_event(victim_names: list[str]) -> None:
    """
    Simulates a zombie breach: clears a random portion of food from victims.
    Called when S_r < 0 and breach probability triggers.
    """
    import random
    victims = random.sample(victim_names, k=max(1, len(victim_names) // 4))
    for name in victims:
        rcon_client.send_command(f"clear {name} minecraft:bread")
        rcon_client.send_command(f"clear {name} minecraft:cooked_beef")
    print(f"[breach] Breach event! Victims lost food: {victims}")
