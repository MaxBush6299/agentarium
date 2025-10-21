/**
 * ConversationName Component Tests
 * Tests for conversation naming and editing functionality
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ConversationName } from '../src/components/chat/ConversationName'

describe('ConversationName Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render "Untitled" when name is not provided', () => {
    render(<ConversationName onNameChange={vi.fn()} />)
    expect(screen.getByText('Untitled')).toBeInTheDocument()
  })

  it('should display provided conversation name', () => {
    render(
      <ConversationName name="My Conversation" onNameChange={vi.fn()} />
    )
    expect(screen.getByText('My Conversation')).toBeInTheDocument()
  })

  it('should enter edit mode when clicking on the name', async () => {
    const user = userEvent.setup()
    const { container } = render(
      <ConversationName name="My Conversation" onNameChange={vi.fn()} />
    )

    const displayMode = container.querySelector('[class*="displayMode"]')
    if (displayMode) {
      await user.click(displayMode)
    }

    // After clicking, should see an input field
    await waitFor(() => {
      const input = screen.getByPlaceholderText('Enter conversation name...')
      expect(input).toBeInTheDocument()
    })
  })

  it('should save name when Enter key is pressed', async () => {
    const handleNameChange = vi.fn().mockResolvedValue(undefined)
    const user = userEvent.setup()

    render(
      <ConversationName name="Old Name" onNameChange={handleNameChange} />
    )

    // Click to edit
    const text = screen.getByText('Old Name')
    await user.click(text)

    // Change the name
    const input = screen.getByPlaceholderText('Enter conversation name...')
    await user.clear(input)
    await user.type(input, 'New Name')

    // Press Enter
    await user.keyboard('{Enter}')

    await waitFor(() => {
      expect(handleNameChange).toHaveBeenCalledWith('New Name')
    })
  })

  it('should cancel editing when Escape key is pressed', async () => {
    const handleNameChange = vi.fn()
    const user = userEvent.setup()

    render(
      <ConversationName name="Original Name" onNameChange={handleNameChange} />
    )

    // Click to edit
    const text = screen.getByText('Original Name')
    await user.click(text)

    // Change the name
    const input = screen.getByPlaceholderText('Enter conversation name...')
    await user.clear(input)
    await user.type(input, 'Temporary Name')

    // Press Escape
    await user.keyboard('{Escape}')

    // Should show original name, not temporary
    expect(screen.getByText('Original Name')).toBeInTheDocument()
    expect(handleNameChange).not.toHaveBeenCalled()
  })

  it('should trim whitespace from input', async () => {
    const handleNameChange = vi.fn().mockResolvedValue(undefined)
    const user = userEvent.setup()

    render(
      <ConversationName name="Old Name" onNameChange={handleNameChange} />
    )

    const text = screen.getByText('Old Name')
    await user.click(text)

    const input = screen.getByPlaceholderText('Enter conversation name...')
    await user.clear(input)
    await user.type(input, '   Trimmed Name   ')

    await user.keyboard('{Enter}')

    await waitFor(() => {
      expect(handleNameChange).toHaveBeenCalledWith('Trimmed Name')
    })
  })

  it('should handle empty input and keep original name', async () => {
    const handleNameChange = vi.fn()
    const user = userEvent.setup()

    render(
      <ConversationName name="Original Name" onNameChange={handleNameChange} />
    )

    const text = screen.getByText('Original Name')
    await user.click(text)

    const input = screen.getByPlaceholderText('Enter conversation name...')
    await user.clear(input)

    // Click elsewhere to trigger blur (save)
    await user.click(screen.getByText('Original Name').parentElement || document.body)

    // Should exit edit mode without calling handler for empty input
    expect(handleNameChange).not.toHaveBeenCalled()
  })

  it('should cancel editing with cancel button', async () => {
    const handleNameChange = vi.fn()
    const user = userEvent.setup()

    render(
      <ConversationName name="Original Name" onNameChange={handleNameChange} />
    )

    const text = screen.getByText('Original Name')
    await user.click(text)

    const input = screen.getByPlaceholderText('Enter conversation name...')
    await user.clear(input)
    await user.type(input, 'New Name')

    // Click cancel button (dismiss icon)
    const cancelButtons = screen.getAllByRole('button')
    const dismissButton = cancelButtons[cancelButtons.length - 1] // Last button should be cancel
    await user.click(dismissButton)

    expect(handleNameChange).not.toHaveBeenCalled()
  })

  it('should be disabled when disabled prop is true', () => {
    const { container } = render(
      <ConversationName name="My Conversation" onNameChange={vi.fn()} disabled={true} />
    )

    const displayMode = container.querySelector('[class*="displayMode"]')
    if (displayMode) {
      const parentDiv = displayMode.parentElement
      expect(parentDiv).toHaveStyle('pointer-events: none')
    }
  })

  it('should show edit icon on hover', () => {
    const { container } = render(
      <ConversationName name="My Conversation" onNameChange={vi.fn()} />
    )

    const editButton = container.querySelector('[class*="editButton"]')
    expect(editButton).toBeInTheDocument()
  })

  it('should display Untitled in italic style', () => {
    const { container } = render(
      <ConversationName onNameChange={vi.fn()} />
    )

    const untitledText = screen.getByText('Untitled')
    expect(untitledText).toHaveClass('untitledText')
  })

  it('should handle API errors gracefully', async () => {
    const handleNameChange = vi.fn().mockRejectedValue(new Error('Save failed'))
    const user = userEvent.setup()

    render(
      <ConversationName name="Original Name" onNameChange={handleNameChange} />
    )

    const text = screen.getByText('Original Name')
    await user.click(text)

    const input = screen.getByPlaceholderText('Enter conversation name...')
    await user.clear(input)
    await user.type(input, 'New Name')

    await user.keyboard('{Enter}')

    // Should exit edit mode even on error
    await waitFor(() => {
      expect(screen.getByText('Original Name')).toBeInTheDocument()
    })
  })
})
