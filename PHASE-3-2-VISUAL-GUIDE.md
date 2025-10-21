# Phase 3.2 Visual Implementation Guide

## Chat Page Header Layout

### Before (Phase 3.1):
```
┌─────────────────────────────────────────────────────────────┐
│ Chat with Agent: support-triage                 [Export CSV] │
│ Thread: 550e8400-e29b-41d4-a716-446655440000              │
└─────────────────────────────────────────────────────────────┘
```

### After (Phase 3.2):
```
┌──────────────────────────────────────────────────────────────┐
│ My Support Tickets                [Support Triage ▼] [Export] │
│ Thread: 550e8400-e29b-41d4-a716-446655440000                │
└──────────────────────────────────────────────────────────────┘
```

## Component Structure

### AgentSelector Dropdown

#### Closed State:
```
┌─────────────────────────────┐
│ Support Triage              │
│ [Edit icon on hover] ▼      │
└─────────────────────────────┘
```

#### Open State:
```
┌──────────────────────────────────┐
│ Support Triage          [active]  │ ← Current selection
├──────────────────────────────────┤
│ Azure Ops               [active]  │
├──────────────────────────────────┤
│ SQL Agent             [inactive]  │
├──────────────────────────────────┤
│ News Agent            [inactive]  │
└──────────────────────────────────┘
```

#### Status Badges:
```
[active]   - Green badge, success color
[inactive] - Gray badge, warning color
```

### ConversationName Display

#### View Mode:
```
My Support Ticket ✏️
↑ Click to edit
```

#### Edit Mode (Click activated):
```
┌─────────────────────────┬───┐
│ My Support Ticket       │ ✕ │ ← Cancel (dismiss icon)
└─────────────────────────┴───┘
 Enter: Save | Escape: Cancel
```

#### New Conversation (Untitled):
```
_Untitled_ ✏️
(italic, light gray color)
```

## Interaction Flows

### Agent Switching Flow

1. User clicks on different agent in dropdown
2. AgentSelector fires `onAgentChange(newAgentId)`
3. ChatPage handleAgentChange executes:
   ```
   setCurrentAgentId(newAgentId)
   setMessages([])           // Clear conversation
   clearTraces()             // Clear traces
   setConversationName('')   // Reset name
   ```
4. Header updates to show new agent
5. Conversation name reverts to "Untitled"
6. Ready for new message

### Conversation Naming Flow

1. User clicks on conversation name to enter edit mode
2. Input field appears with current name selected
3. User types new name (or clears for empty)
4. User presses Enter or clicks outside
5. `onNameChange(trimmedName)` called
   - If empty: becomes "Untitled"
   - If text: saved to server (when API integrated)
6. Edit mode exits
7. Header shows new name

## State Management

### ChatPage State:
```typescript
// Agent and conversation state
currentAgentId: 'support-triage'    // Track selected agent
conversationName: 'My Support...'   // Track conversation name

// Chat state (existing)
messages: Message[]                 // Chat messages
isLoading: boolean                  // Streaming state
traces: TraceEvent[]                // Tool traces
```

### Component Props Flow:
```
ChatPage
├─ AgentSelector
│  ├─ selectedAgentId = currentAgentId
│  ├─ onAgentChange = handleAgentChange
│  └─ disabled = isLoading
│
└─ ConversationName
   ├─ name = conversationName
   ├─ onNameChange = handleNameChange
   └─ disabled = isLoading
```

## Event Flow Diagram

```
User clicks agent dropdown
         ↓
  AgentSelector.onOptionSelect()
         ↓
  handleAgentChange(agentId)
         ├─ setCurrentAgentId(agentId)
         ├─ setMessages([])
         ├─ clearTraces()
         ├─ setConversationName('')
         └─ console.log('Switched to agent:', agentId)
         ↓
  State updated
         ↓
  ChatPage re-renders
  ├─ AgentSelector shows new agent
  ├─ ConversationName shows "Untitled"
  └─ MessageList is empty
```

## Keyboard Shortcuts

### ConversationName Edit Mode:
- **Enter** - Save and exit edit mode
- **Escape** - Cancel, discard changes, exit edit mode
- **Click X button** - Cancel, exit edit mode

### Message Input (existing):
- **Enter** - Send message
- **Shift+Enter** - New line
- **Tab** - Next focusable element

## Error Handling

### AgentSelector Errors:
```
┌─────────────────────────────┐
│ ⚠ Failed to load agents     │
└─────────────────────────────┘
```

### ConversationName Save Errors:
```
Component remains in view mode with previous name
Error logged to console
User can retry by clicking again
```

## Loading States

### AgentSelector Loading:
```
┌─────────────────────────────┐
│ ⟳ Loading agents...         │
└─────────────────────────────┘
```

### ConversationName Saving:
- Input field disabled
- Cancel button disabled
- 50% opacity on disabled buttons
- Save happens on blur or Enter

## Accessibility

### AgentSelector:
- Keyboard navigable (arrow keys in dropdown)
- Screen reader support via Fluent UI
- Status badges visually distinct and labeled

### ConversationName:
- Click target 32px minimum height
- Edit icon clearly visible
- Tooltip text "Click to edit"
- Input placeholder: "Enter conversation name..."
- Clear visual feedback on focus/hover

## Responsive Design

### Desktop (1024px+):
```
Full header with all components visible
AgentSelector: 200px width
ConversationName: flex: 1 (grows)
```

### Tablet (768px-1024px):
```
Components remain, slightly reduced spacing
ConversationName truncates with ellipsis if needed
```

### Mobile (< 768px):
```
Stack vertically or show agent selector in sidebar
(Phase 3.7 consideration for thread management)
```

## Color Scheme

### AgentSelector:
- Text: `colorNeutralForeground1` (default text)
- Hover: `colorNeutralBackground1Hover` (light gray)
- Button: `colorNeutralStroke2` (border)

### ConversationName:
- Display: `colorNeutralForeground1` (default text)
- Untitled: `colorNeutralForeground3` (gray, italic)
- Edit hover: `colorNeutralBackground1Hover` (light gray)
- Input: `colorNeutralForeground1` (text)
- Icons: `colorNeutralForeground2` (medium gray)

## Icon Reference

### AgentSelector:
- **ChevronDown24Regular** - Dropdown arrow

### ConversationName:
- **EditRegular** - Edit mode trigger (size 16px)
- **DismissRegular** - Cancel button (size 16px)

## Success Indicators

✅ Agent selector shows all 5 agents
✅ Status badges display correctly
✅ Switching agents clears conversation
✅ Conversation name editable inline
✅ Keyboard shortcuts work (Enter/Escape)
✅ No console errors
✅ Responsive on all screen sizes
✅ Accessible with keyboard navigation
✅ Touch-friendly on mobile

## Known Limitations

⏳ Conversation name not yet persisted to server
⏳ New thread not created on agent switch
⏳ Thread history not visible (Phase 3.7)
⏳ Agent-specific settings not configurable (Phase 3.3)
