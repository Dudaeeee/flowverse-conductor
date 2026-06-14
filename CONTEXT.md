# Flowverse Conductor

Flowverse Conductor is the company context for reusable agent harness templates. It defines the language used when creating new project repositories that work consistently with Codex and Claude Code.

## Language

**Company Agent Harness**:
The company-owned reusable guidance, workflow, and skill layer that gives coding agents a consistent way to work across new projects.
_Avoid_: agent setup, AI config bundle

**Template Repository**:
The primary product of this context: a GitHub-hosted source repository whose files are downloaded or copied to start a new project, then adapted for that project's product, stack, and commands.
_Avoid_: GitHub Template Repository feature, upstream clone, retrofit installer

**Project Adaptation**:
The project-owned changes made after bootstrapping a repository from the template files. A project may change any file from the template when its local context requires it.
_Avoid_: forbidden customization, central override

**Post-Bootstrap Independence**:
The lifecycle model where a project does not track template repository updates after copying the starter files. The template is a starting point, not an upstream dependency.
_Avoid_: template sync, upstream tracking

**Agent-Harness-Only Template**:
A template repository that contains the agent collaboration layer but no application framework, product code, or runtime-specific starter app.
_Avoid_: app starter, framework template, full-stack template

**Tool Adapter**:
A tool-specific surface that lets one canonical harness work in a particular agent tool, such as Codex or Claude Code.
_Avoid_: separate harness, duplicate instructions

**First-Class Adapter**:
A tool adapter that this template intentionally ships, documents, and checks as part of the supported harness surface. Codex and Claude Code are the only first-class adapters in this context.
_Avoid_: best-effort integration, unofficial adapter

**Stable Adapter Name**:
The default rule that the Codex plugin package name remains `company-agent-harness` after file bootstrap because it names the company harness adapter, not the project product.
_Avoid_: project plugin rename, product-branded harness adapter

**Committed Adapter Mirror**:
A tool-specific copy of canonical skill files that is committed to the template repository so the created project works immediately in that tool.
_Avoid_: generated-only setup, untracked mirror

**Repo-Scoped Skill Mirror**:
The `.agents/skills/` copy of canonical skills that lets Codex read project skills without installing the Codex plugin.
_Avoid_: plugin-only skill access, manual Codex setup

**Agent Source**:
The canonical reusable agent definition under `harness/agents/` that is rendered into Codex and Claude Code agent formats.
_Avoid_: hand-maintained subagent copies, tool-specific source of truth

**Agent Mirror**:
The committed `.codex/agents/` and `.claude/agents/` files generated from canonical agent source so project-scoped agents are available immediately.
_Avoid_: untracked generated agents, per-tool drift

**Doctor Script**:
A checklist-style script that reports whether the file-bootstrapped repository's harness structure is complete and consistent without rewriting project files.
_Avoid_: init script, automatic migration

**Harness CI**:
A minimal continuous integration check for the template's harness structure, scripts, JSON metadata, and committed adapter mirrors. It does not build or test application code.
_Avoid_: app CI, full project pipeline

**GitHub-Hosted Template**:
A source repository that is expected to live on GitHub and use GitHub-native repository features such as GitHub Actions for harness validation.
_Avoid_: provider-agnostic template, optional GitHub setup

**File Bootstrap**:
The default project creation path where a GitHub Download ZIP or release archive is unpacked into a new project repository.
_Avoid_: GitHub Template Repository requirement, upstream fork, default git clone

**Release Archive**:
A versioned GitHub archive used as a stable file bootstrap source for new projects.
_Avoid_: upstream dependency, automatic update channel

**Rename Checklist**:
A human-run checklist for replacing starter repository names and placeholder publisher metadata after bootstrapping from the template files.
_Avoid_: automatic rename, rewrite script

**Lean Agent Guide**:
An always-loaded agent instruction file that contains only minimal harness rules and project profile pointers, while detailed workflows live in skills or docs.
_Avoid_: comprehensive playbook, full workflow manual

**Project Profile**:
The project-owned operational contract that tells agents the product context, stack, commands, environments, and constraints for the file-bootstrapped repository.
_Avoid_: informational README, optional notes

**Domain Glossary**:
The project-owned language record that defines domain terms used by humans and agents in the file-bootstrapped repository.
_Avoid_: implementation spec, scratchpad

**Decision Record**:
A short explanation of a durable project decision that would be surprising without context and costly to rediscover later.
_Avoid_: meeting notes, implementation checklist

**General Workflow Skill**:
A reusable skill that describes an engineering workflow independent of a product domain, application stack, or runtime.
_Avoid_: stack-specific skill, domain-specific skill

**Superpowers Baseline Methodology**:
The adapted development lifecycle used by this harness: brainstorm, isolate, plan, execute with review, test, verify, and finish.
_Avoid_: upstream vendor copy, optional checklist

**Retrofit Installer**:
A future migration path for adding the company agent harness to an existing repository. It is not the primary product of this context.
_Avoid_: template repository
