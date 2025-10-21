# Export Button Feature - Phase 3.6

## Overview

The **ExportButton** component enables users to export chat conversations and tool execution traces to CSV format for analysis, sharing, and archival.

## Features

### What Gets Exported

1. **Messages**
   - User messages
   - Assistant responses
   - Timestamp of each message
   - Agent ID and name (if available)
   - Any error messages

2. **Tool Traces** (when available)
   - Tool call name
   - Status (pending, success, error)
   - Latency (ms)
   - Token counts (input, output, total)
   - Input parameters summary
   - Output summary
   - Errors if any occurred
   - Hierarchical/nested traces for A2A calls

### CSV Format

**Columns:**
- `Timestamp` - ISO 8601 timestamp of message/trace
- `Role` - "user", "assistant", or "tool"
- `Content` - The message text or tool name
- `Type` - "message", "tool_call", "a2a_call", "model_call"
- `Metadata` - JSON object with additional context

**Example Output:**
```csv
"Timestamp","Role","Content","Type","Metadata"
"2025-01-15T14:30:00Z","user","How do I troubleshoot Azure AD?","message","{""agentId"":""support-triage""}"
"2025-01-15T14:30:01Z","tool","search_docs","tool_call","{""status"":""success"",""latencyMs"":245}"
"2025-01-15T14:30:02Z","assistant","Here are the steps to troubleshoot Azure AD...","message","{""agentId"":""support-triage""}"
```

### Filename Convention

Files are named: `conversation-{agent-id}-{date}-{time}.csv`

Example: `conversation-support-triage-2025-01-15-14-30-45.csv`

## Implementation Details

### Component: `ExportButton.tsx`

**Location:** `frontend/src/components/chat/ExportButton.tsx`

**Props:**
```typescript
interface ExportButtonProps {
  messages: Message[]           // Chat messages to export
  traces?: TraceEvent[]         // Tool traces (optional)
  agentId?: string             // Agent ID for filename
}
```

**Features:**
- Fluent UI Button with download icon
- Tooltip on hover
- Disabled state when no messages
- Exports in-progress indication
- Error handling with user alert
- Client-side only (no backend call needed)

### Integration with ChatPage

The ExportButton is added to the chat header:

```tsx
<div className={styles.chatHeaderActions}>
  <ExportButton 
    messages={messages} 
    traces={traces} 
    agentId={locationState?.agentId} 
  />
</div>
```

### CSV Generation Functions

**Key Functions:**

1. **`generateCSV(messages, traces?, agentId?)`**
   - Converts messages and traces to CSV format
   - Ensures proper escaping of special characters
   - Returns CSV string

2. **`tracesToCSVRows(traces, afterTimestamp?)`**
   - Converts trace events to CSV rows
   - Handles hierarchical traces with indentation
   - Summarizes input/output for readability

3. **`escapeCSVField(value)`**
   - Escapes quotes and wraps fields
   - Ensures CSV format compliance

4. **`downloadCSV(csv, filename)`**
   - Creates blob and triggers download
   - Cleans up resources after download

## Usage

### For End Users

1. Have a conversation with an agent
2. Click the "Export" button in the chat header (download icon)
3. CSV file automatically downloads to your default Downloads folder
4. Open with Excel, Google Sheets, or any text editor

### For Developers

**Import the component:**
```tsx
import { ExportButton } from '../components/chat/ExportButton'
```

**Use in your component:**
```tsx
<ExportButton 
  messages={messages}
  traces={traces}
  agentId="support-triage"
/>
```

## Testing

### Manual Test Cases

1. **Empty conversation:** Click export with no messages → Should show alert
2. **Single message:** Send one message, export → Verify CSV format
3. **Long conversation:** Multiple messages/traces → Verify all data included
4. **Special characters:** Send message with quotes, commas, newlines → Verify escaping
5. **Tool traces:** Send message that triggers tool calls → Verify traces in export
6. **Different agents:** Test with different agent IDs → Verify in filename

### Test File

Unit tests available at: `frontend/tests/exportButton.test.ts`

Run with:
```bash
cd frontend
npm test -- exportButton.test.ts
```

## Future Enhancements

### Phase 3.7+

1. **JSON Export Format**
   - Full structured data export
   - Better for programmatic processing

2. **Export Options Modal**
   - Choose export format (CSV, JSON, PDF)
   - Select which fields to include
   - Filter by date range or message type

3. **Export Templates**
   - Business report format
   - Technical analysis format
   - Executive summary format

4. **Email Export**
   - Send export directly to email
   - Scheduled exports

5. **Database Archival**
   - Auto-save exports to Cosmos DB
   - Search and retrieve past exports

## Browser Compatibility

- ✅ Chrome/Edge (v90+)
- ✅ Firefox (v88+)
- ✅ Safari (v14+)
- ✅ All Chromium-based browsers

Uses standard Web APIs:
- `Blob` API for file creation
- `URL.createObjectURL()` for download
- `<a>` element click for triggering download

## Performance Considerations

- **Time Complexity:** O(n) where n = number of messages + traces
- **Space Complexity:** O(m) where m = CSV output size
- **No backend call:** Processing is entirely client-side
- **Large conversations:** Tested with 1000+ messages, 500+ traces

## Security Considerations

- ⚠️ **Data in CSV:** Exported data is plain text - handle carefully if contains PII
- ✅ **Client-side only:** No data sent to backend during export
- ✅ **No external requests:** All processing local
- ⚠️ **Browser storage:** Downloaded file location determined by browser settings

## Known Limitations

1. **CSV Size:** Very large conversations (10K+ messages) may be slow
2. **Special Characters:** Line breaks in content appear as literal `\n` in CSV
3. **Media:** Images, files in traces are not included (only summarized)
4. **Real-time updates:** Export only includes messages already in chat history

## Related Components

- `MessageList.tsx` - Displays messages
- `TracePanel.tsx` - Displays traces
- `ChatPage.tsx` - Parent component

## Status

✅ **IMPLEMENTED** - Phase 3.6

- Component: Complete
- Integration: Complete
- Testing: Basic tests created
- Documentation: Complete
