#!/usr/bin/env node
/**
 * self-driving-agents — install a self-driving agent.
 *
 * npx @vectorize-io/self-driving-agents install <agent> --harness openclaw [--agent <name>]
 *
 * Agent resolution:
 *   marketing-agent            → vectorize-io/self-driving-agents/marketing-agent (default repo)
 *   my-org/my-repo/my-agent   → my-org/my-repo/my-agent on GitHub
 *   ./local-dir                → local directory
 *   /absolute/path             → local directory
 *
 * Directory layout (recursive):
 *   bank-template.json   — optional: bank config at this level
 *   *.md, *.txt, ...     — content files (found recursively, excluding bank-template.json)
 */
/**
 * Whether a string is a valid agent name. Used by --empty mode where the
 * first positional arg becomes the agent name (no path, no GitHub fetch).
 *
 * Rules: starts with [a-z0-9], then lowercase alphanumerics or hyphens, max
 * 64 chars. Matches the lowercase-with-hyphens convention the create-agent
 * skill expects.
 */
export declare function isValidAgentName(name: string): boolean;
