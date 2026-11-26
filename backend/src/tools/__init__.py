"""Tools: everything agents can look up or do.

Thin, typed wrappers over the services. The logic lives in each entity's service
(src/properties, src/bills, ...); a tool only picks what an agent needs and returns
plain dicts. Agents import tools, never services or repositories, so this module is
the full list of what agents are allowed to touch.

Every tool takes the landlord's client_id where data is per landlord.
"""
