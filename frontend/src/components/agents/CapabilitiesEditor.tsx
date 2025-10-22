/**
 * CapabilitiesEditor Component
 * 
 * Provides a UI for editing agent capabilities.
 * Users can add new capabilities and remove existing ones.
 * 
 * Features:
 * - Add/remove capabilities
 * - Input validation (no empty strings, no duplicates)
 * - FluentUI components for consistent styling
 * - Flexible for use in edit dialogs and creation forms
 */

import React, { useState } from 'react';
import {
  Button,
  Input,
  Label,
  Tag,
  Text,
  makeStyles,
  tokens,
} from '@fluentui/react-components';
import {
  Delete20Regular as DeleteIcon,
  Add20Regular as AddIcon,
} from '@fluentui/react-icons';

const useStyles = makeStyles({
  container: {
    display: 'flex',
    flexDirection: 'column',
    gap: tokens.spacingVerticalM,
  },
  tagContainer: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: tokens.spacingHorizontalM,
  },
  inputRow: {
    display: 'flex',
    gap: tokens.spacingHorizontalM,
    alignItems: 'center',
  },
  input: {
    flex: 1,
  },
  emptyState: {
    color: tokens.colorNeutralForeground3,
  },
});

export interface CapabilitiesEditorProps {
  /** Current list of capabilities */
  capabilities: string[];
  
  /** Called when capabilities list changes */
  onChange: (capabilities: string[]) => void;
  
  /** Optional label for the editor */
  label?: string;
  
  /** Optional placeholder text for input */
  placeholder?: string;
  
  /** Optional help text */
  helpText?: string;
  
  /** Optional: disable the editor */
  disabled?: boolean;
}

/**
 * CapabilitiesEditor Component
 * 
 * Usage:
 * ```tsx
 * const [capabilities, setCapabilities] = useState<string[]>([]);
 * 
 * <CapabilitiesEditor
 *   capabilities={capabilities}
 *   onChange={setCapabilities}
 *   label="Agent Capabilities"
 *   placeholder="e.g., document_search, issue_triage"
 * />
 * ```
 */
export const CapabilitiesEditor: React.FC<CapabilitiesEditorProps> = ({
  capabilities,
  onChange,
  label = 'Capabilities',
  placeholder = 'e.g., document_retrieval, issue_triage',
  helpText,
  disabled = false,
}) => {
  const styles = useStyles();
  const [inputValue, setInputValue] = useState('');

  const handleAddCapability = () => {
    const trimmed = inputValue.trim();
    
    // Validation
    if (!trimmed) {
      return;
    }
    
    // Check for duplicates (case-insensitive)
    if (capabilities.some(cap => cap.toLowerCase() === trimmed.toLowerCase())) {
      setInputValue('');
      return;
    }
    
    // Add capability
    onChange([...capabilities, trimmed]);
    setInputValue('');
  };

  const handleRemoveCapability = (index: number) => {
    onChange(capabilities.filter((_, i) => i !== index));
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddCapability();
    }
  };

  return (
    <div className={styles.container}>
      <Label required={false}>{label}</Label>
      
      {/* Capabilities Tag Display */}
      {capabilities.length > 0 && (
        <div className={styles.tagContainer}>
          {capabilities.map((capability, index) => (
            <Tag
              key={`${capability}-${index}`}
              value={capability}
              shape="rounded"
              dismissIcon={
                !disabled ? (
                  <Button
                    icon={<DeleteIcon />}
                    size="small"
                    appearance="subtle"
                    onClick={() => handleRemoveCapability(index)}
                    title="Remove capability"
                    aria-label={`Remove ${capability}`}
                  />
                ) : undefined
              }
            >
              {capability}
            </Tag>
          ))}
        </div>
      )}
      
      {/* Input to Add New Capability */}
      {!disabled && (
        <div className={styles.inputRow}>
          <Input
            value={inputValue}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={placeholder}
            disabled={disabled}
            className={styles.input}
            aria-label="Enter new capability"
          />
          <Button
            icon={<AddIcon />}
            onClick={handleAddCapability}
            disabled={!inputValue.trim() || disabled}
            title="Add capability"
            aria-label="Add capability"
          />
        </div>
      )}
      
      {/* Help Text */}
      {helpText && (
        <Text size={200} className={styles.emptyState}>
          {helpText}
        </Text>
      )}
      
      {/* Empty State Message */}
      {capabilities.length === 0 && (
        <Text size={200} className={styles.emptyState}>
          No capabilities defined yet. Add one to describe what this agent can do.
        </Text>
      )}
    </div>
  );
};
