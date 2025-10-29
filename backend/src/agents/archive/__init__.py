"""
Archive for Legacy Handoff Implementations

This folder contains outdated multi-agent routing implementations that have
been replaced by the official HandoffBuilder pattern.

**DEPRECATED FILES:**
- handoff_router.py: Custom intent-based routing logic
- handoff_orchestrator.py: Custom orchestration with state management  
- intelligent_orchestrator.py: Failed attempt at evaluator-based routing

**REPLACEMENT:**
Use `handoff_builder_orchestrator.py` instead for all new multi-agent workflows.

These files are kept for historical reference and debugging only. They should
NOT be imported or used in new code.

## Why These Were Archived

1. **Custom Code Complexity**: Each implementation added custom routing logic
   that needed to be maintained separately
   
2. **Handoff Pattern Not Official**: These were experiments before Microsoft's
   agent-framework team released the official HandoffBuilder pattern
   
3. **Inconsistent Architecture**: Different files had different approaches to
   managing agent routing, context transfer, and state
   
4. **HandoffBuilder is Better**: The official pattern is:
   - Simpler and more maintainable
   - Officially supported by agent-framework team
   - Follows best practices from OpenAI Workshop
   - Extensible for custom routing strategies

## If You Need to Debug Old Issues

If working on historical bugs or understanding why certain patterns were rejected:
1. See `handoff_router.py` for simple keyword-based routing
2. See `handoff_orchestrator.py` for state management patterns
3. See `intelligent_orchestrator.py` for evaluator feedback loops

But for any NEW work, use `handoff_builder_orchestrator.py` exclusively.
"""
