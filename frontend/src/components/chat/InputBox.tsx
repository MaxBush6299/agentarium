import React, { useState, useRef, KeyboardEvent } from 'react';
import {
  Button,
  Textarea,
  makeStyles,
  shorthands,
  tokens,
  Text,
} from '@fluentui/react-components';
import { Send24Regular } from '@fluentui/react-icons';
import type { InputBoxProps } from '../../types/message';

const useStyles = makeStyles({
  container: {
    display: 'flex',
    flexDirection: 'column',
    ...shorthands.gap(tokens.spacingVerticalS),
    ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalL),
    ...shorthands.borderTop('1px', 'solid', tokens.colorNeutralStroke2),
    backgroundColor: tokens.colorNeutralBackground1,
  },
  inputRow: {
    display: 'flex',
    ...shorthands.gap(tokens.spacingHorizontalM),
    alignItems: 'flex-end',
  },
  textarea: {
    flex: 1,
    minHeight: '44px',
    maxHeight: '200px',
  },
  sendButton: {
    minWidth: '44px',
    height: '44px',
  },
  footer: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  hint: {
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorNeutralForeground3,
  },
  charCount: {
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorNeutralForeground3,
  },
  charCountWarning: {
    color: tokens.colorPaletteRedForeground1,
  },
});

export const InputBox: React.FC<InputBoxProps> = ({
  onSend,
  disabled = false,
  placeholder = 'Type your message...',
  maxLength = 4000,
}) => {
  const styles = useStyles();
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    const trimmedMessage = message.trim();
    if (trimmedMessage && !disabled) {
      onSend(trimmedMessage);
      setMessage('');
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    // Send on Enter, newline on Shift+Enter
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  const handleChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = event.target.value;
    if (newValue.length <= maxLength) {
      setMessage(newValue);
    }
  };

  const charCount = message.length;
  const isNearLimit = charCount >= maxLength * 0.9;
  const canSend = message.trim().length > 0 && !disabled;

  return (
    <div className={styles.container}>
      <div className={styles.inputRow}>
        <Textarea
          ref={textareaRef}
          className={styles.textarea}
          value={message}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          resize="vertical"
          aria-label="Message input"
        />
        <Button
          className={styles.sendButton}
          appearance="primary"
          icon={<Send24Regular />}
          onClick={handleSend}
          disabled={!canSend}
          aria-label="Send message"
        />
      </div>
      <div className={styles.footer}>
        <Text className={styles.hint}>
          Press <strong>Enter</strong> to send, <strong>Shift+Enter</strong> for new line
        </Text>
        <Text
          className={`${styles.charCount} ${
            isNearLimit ? styles.charCountWarning : ''
          }`}
        >
          {charCount} / {maxLength}
        </Text>
      </div>
    </div>
  );
};
