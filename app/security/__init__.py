"""
app/security — SSRF protection and target validation components.

Security boundary: no raw user URL may reach the network client.
Every outbound connection must go through ValidatedTarget.
"""
