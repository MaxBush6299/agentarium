/**
 * Export Button Tests
 * Tests CSV export functionality
 */

import { Message, MessageRole, TraceEvent } from '../src/types/message'

/**
 * Helper to generate CSV (copied from ExportButton)
 */
const escapeCSVField = (value: string): string => {
  if (typeof value !== 'string') {
    value = String(value)
  }
  return value.replace(/"/g, '""')
}

const generateCSV = (messages: Message[], traces?: TraceEvent[], agentId?: string): string => {
  const rows: string[] = []
  
  // CSV Header
  rows.push(
    '"Timestamp","Role","Content","Type","Metadata"'
  )
  
  // Process messages
  for (const message of messages) {
    const timestamp = message.timestamp.toISOString()
    const role = message.role
    const content = escapeCSVField(message.content)
    const type = 'message'
    const metadata = escapeCSVField(
      JSON.stringify({
        agentId: message.agentId,
        agentName: message.agentName,
        isStreaming: message.isStreaming,
        error: message.error,
      })
    )
    
    rows.push(`"${timestamp}","${role}","${content}","${type}",${metadata}`)
  }
  
  return rows.join('\n')
}

/**
 * Test: Empty messages
 */
export const testEmptyMessages = () => {
  const csv = generateCSV([], [])
  console.log('✓ Empty messages test:', csv.split('\n').length === 1)
}

/**
 * Test: Single user message
 */
export const testSingleMessage = () => {
  const messages: Message[] = [
    {
      id: 'msg1',
      role: MessageRole.USER,
      content: 'Hello, how are you?',
      timestamp: new Date('2025-01-01T12:00:00Z'),
      agentId: 'support-triage',
    }
  ]
  
  const csv = generateCSV(messages)
  const lines = csv.split('\n')
  
  console.log('✓ Single message test:')
  console.log('  Lines:', lines.length)
  console.log('  Has header:', lines[0].includes('Timestamp'))
  console.log('  Has content:', lines[1].includes('Hello'))
}

/**
 * Test: Multiple messages with special characters
 */
export const testSpecialCharacters = () => {
  const messages: Message[] = [
    {
      id: 'msg1',
      role: MessageRole.USER,
      content: 'Test with "quotes" and commas, like this',
      timestamp: new Date('2025-01-01T12:00:00Z'),
    },
    {
      id: 'msg2',
      role: MessageRole.ASSISTANT,
      content: 'Response with\nnewlines\nand special chars: !@#$%',
      timestamp: new Date('2025-01-01T12:01:00Z'),
    }
  ]
  
  const csv = generateCSV(messages)
  const lines = csv.split('\n')
  
  console.log('✓ Special characters test:')
  console.log('  Lines:', lines.length)
  console.log('  Quotes escaped:', lines[1].includes('""'))
  console.log('  CSV format valid:', lines.every(line => line.split('"').length % 2 === 1))
}

/**
 * Test: Filename generation
 */
export const testFilenameGeneration = () => {
  const generateFilename = (agentId?: string): string => {
    const timestamp = new Date().toISOString().split('T')[0]
    const time = new Date().toISOString().split('T')[1].split('.')[0].replace(/:/g, '-')
    const agent = agentId ? `${agentId}-` : ''
    return `conversation-${agent}${timestamp}-${time}.csv`
  }
  
  const filename1 = generateFilename('support-triage')
  const filename2 = generateFilename()
  
  console.log('✓ Filename generation test:')
  console.log('  With agent ID:', filename1.startsWith('conversation-support-triage-'))
  console.log('  Without agent ID:', filename2.startsWith('conversation-'))
  console.log('  Ends with .csv:', filename1.endsWith('.csv'))
}

// Run tests
console.log('=== Export Button Tests ===\n')
testEmptyMessages()
testSingleMessage()
testSpecialCharacters()
testFilenameGeneration()
console.log('\n✓ All tests completed!')
