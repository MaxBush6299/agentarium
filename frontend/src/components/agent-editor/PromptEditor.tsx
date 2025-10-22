import React, { useMemo } from 'react';
import { TextField, Stack, Text } from '@fluentui/react';
import styles from './PromptEditor.module.css';

interface PromptEditorProps {
  value: string;
  onChange: (value: string) => void;
  error?: string;
  maxLength?: number;
}

/**
 * PromptEditor Component
 * 
 * Provides a textarea for editing agent system prompts with:
 * - Character count and limit tracking
 * - Token estimate (rough: chars / 4)
 * - Line numbers (visual indicator)
 * - Real-time validation feedback
 */
export const PromptEditor: React.FC<PromptEditorProps> = ({
  value,
  onChange,
  error,
  maxLength = 4000,
}) => {
  // Calculate character count and token estimate
  const stats = useMemo(() => {
    const charCount = value.length;
    // Rough token estimate: ~4 characters per token
    const tokenEstimate = Math.ceil(charCount / 4);
    const percentUsed = (charCount / maxLength) * 100;
    
    return { charCount, tokenEstimate, percentUsed };
  }, [value, maxLength]);

  // Determine color based on usage percentage
  const getUsageColor = (percent: number): string => {
    if (percent >= 90) return '#d13438'; // Red (danger)
    if (percent >= 75) return '#f7630c'; // Orange (warning)
    return '#107c10'; // Green (ok)
  };

  const handleChange = (newValue?: string) => {
    if (newValue !== undefined) {
      onChange(newValue.slice(0, maxLength));
    }
  };

  return (
    <Stack tokens={{ childrenGap: 12 }}>
      <div>

        <Text variant="small" styles={{ root: { color: '#d0d0d0', marginTop: 4 } }}>
          Define how the agent behaves and responds to user queries
        </Text>
      </div>

      {/* Textarea */}
      <TextField
        multiline
        rows={10}
        value={value}
        onChange={(_: any, newValue: string | undefined) => handleChange(newValue)}
        placeholder="You are an expert assistant with knowledge of..."
        className={styles.promptTextarea}
        styles={{
          root: { width: '100%' },
          fieldGroup: {
            borderRadius: 4,
            fontSize: 13,
            fontFamily: '"Courier New", monospace',
          },
        }}
        onBlur={() => {
          // Trim whitespace on blur
          onChange(value.trim());
        }}
      />

      {/* Error Message */}
      {error && (
        <Text
          variant="small"
          styles={{
            root: {
              color: '#d13438',
              fontWeight: 500,
            },
          }}
        >
          ⚠️ {error}
        </Text>
      )}

      {/* Stats Footer */}
      <Stack horizontal tokens={{ childrenGap: 24 }}>
        {/* Character Count */}
        <Stack tokens={{ childrenGap: 4 }}>
          <Text variant="small" styles={{ root: { color: '#666' } }}>
            Characters
          </Text>
          <Stack horizontal tokens={{ childrenGap: 8 }} verticalAlign="center">
            <Text
              variant="large"
              styles={{
                root: {
                  fontWeight: 600,
                  color: getUsageColor(stats.percentUsed),
                  fontSize: 16,
                },
              }}
            >
              {stats.charCount}
            </Text>
            <Text variant="small" styles={{ root: { color: '#999' } }}>
              / {maxLength}
            </Text>
          </Stack>
        </Stack>

        {/* Token Estimate */}
        <Stack tokens={{ childrenGap: 4 }}>
          <Text variant="small" styles={{ root: { color: '#666' } }}>
            Estimated Tokens
          </Text>
          <Text
            variant="large"
            styles={{
              root: {
                fontWeight: 600,
                color: '#0078d4',
                fontSize: 16,
              },
            }}
          >
            ~{stats.tokenEstimate}
          </Text>
        </Stack>

        {/* Usage Bar */}
        <Stack tokens={{ childrenGap: 4 }} styles={{ root: { flex: 1 } }}>
          <Text variant="small" styles={{ root: { color: '#666' } }}>
            Usage
          </Text>
          <div className={styles.usageBar}>
            <div
              className={styles.usageFill}
              style={{
                width: `${Math.min(stats.percentUsed, 100)}%`,
                backgroundColor: getUsageColor(stats.percentUsed),
              }}
            />
          </div>
          <Text variant="small" styles={{ root: { color: '#999', fontSize: 12 } }}>
            {stats.percentUsed.toFixed(1)}% used
          </Text>
        </Stack>
      </Stack>

      {/* Helpful Hint */}
      <Text
        variant="small"
        styles={{
          root: {
            color: '#666',
            fontStyle: 'italic',
            padding: '8px 12px',
            backgroundColor: '#f3f2f1',
            borderRadius: 4,
            borderLeft: '4px solid #0078d4',
          },
        }}
      >
        💡 Be specific about the agent's role, capabilities, and behavior. Good prompts lead to better responses.
      </Text>
    </Stack>
  );
};
