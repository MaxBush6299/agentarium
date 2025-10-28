import React, { useMemo, useEffect, useState } from 'react';
import { Stack, Text, Checkbox, Panel, DefaultButton, TextField, Dropdown } from '@fluentui/react';
import { ToolData, TOOL_CATEGORIES } from '../../pages/agent-editor/agentSchema';

interface ToolConfiguratorProps {
  selectedTools: ToolData[];
  onChange: (tools: ToolData[]) => void;
  error?: string;
}

interface ToolItem {
  type: 'mcp' | 'openapi' | 'a2a';
  name: string;
  label: string;
}

/**
 * ToolConfigurator Component
 * 
 * Allows users to select which tools the agent should have access to.
 * Organized by tool type: MCP, OpenAPI, A2A
 * 
 * Features:
 * - Visual categories for tool organization
 * - Checkboxes to enable/disable individual tools
 * - Validation: at least one tool must be selected
 * - "Add Custom Tool" buttons (for future implementation)
 */
export const ToolConfigurator: React.FC<ToolConfiguratorProps> = ({
  selectedTools,
  onChange,
  error,
}) => {
  const [showAddCustom, setShowAddCustom] = React.useState<'mcp' | 'openapi' | 'a2a' | null>(null);
  const [customTools, setCustomTools] = useState<any[]>([]);

  // Fetch custom tools on mount
  useEffect(() => {
    const fetchCustomTools = async () => {
      try {
        const response = await fetch('/api/custom-tools');
        if (response.ok) {
          const data = await response.json();
          setCustomTools(data.tools || []);
        }
      } catch (err) {
        console.error('Failed to fetch custom tools:', err);
      }
    };
    
    fetchCustomTools();
  }, []);

  // Combine custom tools with built-in tools for display
  const getMCPToolsWithCustom = () => {
    const builtInTools = TOOL_CATEGORIES.MCP.tools;
    const customMCPTools = customTools.map(tool => ({
      type: 'mcp' as const,
      name: tool.id,
      label: tool.name,
    }));
    return [...builtInTools, ...customMCPTools];
  };

  // Create a set of selected tool keys for quick lookup
  const selectedToolKeys = useMemo(() => {
    return new Set(selectedTools.map(t => `${t.type}:${t.name}`));
  }, [selectedTools]);

  // Handle tool toggle
  const handleToolToggle = (tool: ToolItem) => {
    const toolKey = `${tool.type}:${tool.name}`;
    const isSelected = selectedToolKeys.has(toolKey);

    if (isSelected) {
      // Remove tool - allow deselecting all tools
      onChange(selectedTools.filter(t => `${t.type}:${t.name}` !== toolKey));
    } else {
      // Add tool
      onChange([
        ...selectedTools,
        {
          type: tool.type,
          name: tool.name,
          enabled: true,
        },
      ]);
    }
  };

  // Render a tool category section
  const renderToolCategory = (
    categoryKey: keyof typeof TOOL_CATEGORIES,
    tools: readonly ToolItem[]
  ) => {
    if (tools.length === 0) return null;

    const category = TOOL_CATEGORIES[categoryKey];

    return (
      <Stack key={categoryKey} tokens={{ childrenGap: 12 }} styles={{ root: { marginBottom: 24 } }}>
        <div>
          <Text variant="mediumPlus" styles={{ root: { fontWeight: 600, color:'#d0d0d0' } }}>
            {category.label}
          </Text>
        </div>

        {/* Tools in this category */}
        <Stack tokens={{ childrenGap: 8 }}>
          {tools.map(tool => {
            const toolKey = `${tool.type}:${tool.name}`;
            const isSelected = selectedToolKeys.has(toolKey);

            return (
              <div
                key={toolKey}
                style={{
                  padding: '14px 16px',
                  borderRadius: 6,
                  backgroundColor: isSelected ? '#1a76a1' : '#5bc3e8',
                  border: isSelected ? '2px solid #3fb0dd' : '1px solid #3fb0dd',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  boxShadow: isSelected ? '0 2px 8px rgba(59, 176, 221, 0.3)' : 'none',
                }}
                onClick={() => handleToolToggle(tool)}
                onMouseEnter={(e) => {
                  if (!isSelected) {
                    e.currentTarget.style.backgroundColor = '#7ad4f0';
                    e.currentTarget.style.borderColor = '#9be3f7';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isSelected) {
                    e.currentTarget.style.backgroundColor = '#5bc3e8';
                    e.currentTarget.style.borderColor = '#3fb0dd';
                  }
                }}
              >
                <Checkbox
                  label={tool.label}
                  checked={isSelected}
                  onChange={() => handleToolToggle(tool)}
                  styles={{
                    root: { 
                      margin: 0,
                      color: '#ffffff',
                    },
                    checkbox: {
                      borderColor: isSelected ? '#f0fcff' : '#7ad4f0',
                      backgroundColor: isSelected ? '#3fb0dd' : 'transparent',
                    },
                    label: { 
                      color: '#ffffffb2',
                      fontWeight: isSelected ? 600 : 500,
                      fontSize: '14px',
                    },
                    text: {
                      color: '#ffffffe1',
                      fontWeight: isSelected ? 600 : 500,
                    }
                  }}
                />
              </div>
            );
          })}
        </Stack>

        {/* Add Custom Tool Button */}
        {categoryKey !== 'A2A' && (
          <DefaultButton
            text={`+ Add Custom ${category.label.replace(' Tools', '')}`}
            onClick={() => setShowAddCustom(categoryKey as 'mcp' | 'openapi')}
            styles={{
              root: {
                marginTop: 8,
                fontSize: 13,
                background: '#243240',
                color: '#7ad4f0',
                border: '1px solid #2d3e4a',
              },
              rootHovered: {
                background: '#1a76a1',
                color: '#f0fcff',
                border: '1px solid #3fb0dd',
              },
            }}
          />
        )}
      </Stack>
    );
  };

  return (
    <Stack tokens={{ childrenGap: 16 }}>
      <div>

        <Text variant="small" styles={{ root: { color: '#d0d0d0', marginTop: 4 } }}>
          Select which tools the agent can use to answer questions and perform tasks
        </Text>
      </div>

      {/* Tool Categories */}
      {renderToolCategory('MCP', getMCPToolsWithCustom())}
      {renderToolCategory('OPENAPI', TOOL_CATEGORIES.OPENAPI.tools)}
      {renderToolCategory('A2A', TOOL_CATEGORIES.A2A.tools)}

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

      {/* Selected Tools Summary */}
      {selectedTools.length > 0 && (
        <div
          style={{
            padding: 12,
            borderRadius: 4,
            backgroundColor: '#f0f9ff',
            borderLeft: '4px solid #107c10',
          }}
        >
          <Text variant="small" styles={{ root: { color: '#f8f0f0ff' } }}>
            <strong>{selectedTools.length} tool(s) selected:</strong>{' '}
            {selectedTools.map(t => t.name).join(', ')}
          </Text>
        </div>
      )}

      {/* Add Custom MCP Tool Panel */}
      <AddCustomToolPanel
        toolType={showAddCustom}
        onDismiss={() => setShowAddCustom(null)}
        onToolRegistered={() => {
          // Refresh custom tools list
          fetch('/api/custom-tools')
            .then(r => r.json())
            .then(data => setCustomTools(data.tools || []))
            .catch(err => console.error('Failed to refresh custom tools:', err));
        }}
      />
    </Stack>
  );
};

/**
 * Panel for adding custom MCP/OpenAPI tools
 * Allows users to register custom MCP servers without code changes
 */
interface AddCustomToolPanelProps {
  toolType: 'mcp' | 'openapi' | 'a2a' | null;
  onDismiss: () => void;
  onToolRegistered?: () => void;
}

const AddCustomToolPanel: React.FC<AddCustomToolPanelProps> = ({
  toolType,
  onDismiss,
  onToolRegistered,
}) => {
  const [toolName, setToolName] = React.useState('');
  const [toolDescription, setToolDescription] = React.useState('');
  const [toolUrl, setToolUrl] = React.useState('');
  const [authType, setAuthType] = React.useState<'none' | 'apikey' | 'oauth'>('none');
  const [apiKey, setApiKey] = React.useState('');
  const [clientId, setClientId] = React.useState('');
  const [clientSecret, setClientSecret] = React.useState('');
  const [tokenUrl, setTokenUrl] = React.useState('');
  const [scope, setScope] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState('');
  const [success, setSuccess] = React.useState(false);

  const panelTitle = {
    mcp: 'Add Custom MCP Server',
    openapi: 'Add Custom OpenAPI API',
    a2a: 'Add Custom A2A Agent',
  }[toolType || 'mcp'];

  const handleSubmit = async () => {
    // Validate required fields
    if (!toolName.trim()) {
      setError('Tool name is required');
      return;
    }
    if (!toolUrl.trim()) {
      setError('Tool URL is required');
      return;
    }

    // Validate auth config
    if (authType === 'apikey' && !apiKey.trim()) {
      setError('API Key is required for API Key authentication');
      return;
    }
    if (authType === 'oauth') {
      if (!clientId.trim() || !clientSecret.trim() || !tokenUrl.trim()) {
        setError('Client ID, Client Secret, and Token URL are required for OAuth');
        return;
      }
    }

    setLoading(true);
    setError('');

    try {
      const payload = {
        name: toolName.trim(),
        description: toolDescription.trim() || `${toolType || 'custom'} tool`,
        url: toolUrl.trim(),
        auth_type: authType,
        ...(authType === 'apikey' && { apikey_config: { api_key: apiKey } }),
        ...(authType === 'oauth' && {
          oauth_config: {
            client_id: clientId,
            client_secret: clientSecret,
            token_url: tokenUrl,
            scope: scope || `api://${clientId}/.default`,
          },
        }),
      };

      const response = await fetch('/api/custom-tools', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to register custom tool');
      }

      setSuccess(true);
      // Reset form
      setToolName('');
      setToolDescription('');
      setToolUrl('');
      setAuthType('none');
      setApiKey('');
      setClientId('');
      setClientSecret('');
      setTokenUrl('');
      setScope('');

      // Call the callback to refresh custom tools
      if (onToolRegistered) {
        onToolRegistered();
      }

      // Close panel after 2 seconds
      setTimeout(() => {
        onDismiss();
        setSuccess(false);
      }, 2000);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Panel
      isOpen={toolType !== null}
      onDismiss={onDismiss}
      headerText={panelTitle}
      closeButtonAriaLabel="Close"
      styles={{
        root: {
          backgroundColor: '#1e1e1e',
        },
        header: {
          backgroundColor: '#2d2d2d',
          borderBottom: '1px solid #3d3d3d',
          padding: '16px',
        },
        headerText: {
          color: '#e0e0e0',
          fontWeight: 600,
        },
        content: {
          backgroundColor: '#1e1e1e',
          color: '#d0d0d0',
          padding: '0 16px 16px 16px',
        },
        contentInner: {
          backgroundColor: '#1e1e1e',
          color: '#d0d0d0',
        },
        navigation: {
          backgroundColor: '#1e1e1e',
        },
        closeButton: {
          color: '#d0d0d0',
          ':hover': {
            color: '#e0e0e0',
            backgroundColor: '#3d3d3d',
          },
        },
      }}
      layerProps={{
        styles: {
          root: {
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
          },
        },
      }}
    >
      <Stack tokens={{ childrenGap: 16 }} styles={{ root: { marginTop: 16 } }}>
        {success && (
          <div
            style={{
              padding: 12,
              borderRadius: 4,
              backgroundColor: '#dffcf0',
              border: '1px solid #107c10',
            }}
          >
            <Text variant="small" styles={{ root: { color: '#107c10', fontWeight: 600 } }}>
              ✓ Custom tool registered successfully!
            </Text>
          </div>
        )}

        {error && (
          <div
            style={{
              padding: 12,
              borderRadius: 4,
              backgroundColor: '#fed9cc',
              border: '1px solid #d13438',
            }}
          >
            <Text variant="small" styles={{ root: { color: '#d13438' } }}>
              {error}
            </Text>
          </div>
        )}

        {/* Tool Name */}
        <TextField
          label="Tool Name"
          placeholder="e.g., Adventure Works Database"
          value={toolName}
          onChange={(_: any, val: string | undefined) => setToolName(val || '')}
          disabled={loading}
          styles={{
            root: { color: '#d0d0d0' },
            field: { 
              backgroundColor: '#2d2d2d',
              color: '#e0e0e0',
              borderColor: '#3d3d3d !important',
            },
            fieldGroup: { borderColor: '#3d3d3d' },
          }}
        />

        {/* Tool Description */}
        <TextField
          label="Description"
          placeholder="What does this tool do?"
          value={toolDescription}
          onChange={(_: any, val: string | undefined) => setToolDescription(val || '')}
          multiline
          rows={2}
          disabled={loading}
          styles={{
            root: { color: '#d0d0d0' },
            field: { 
              backgroundColor: '#2d2d2d',
              color: '#e0e0e0',
              borderColor: '#3d3d3d !important',
            },
            fieldGroup: { borderColor: '#3d3d3d' },
          }}
        />

        {/* Tool URL */}
        <TextField
          label="Server URL"
          placeholder="https://example.com/mcp or http://localhost:8001"
          value={toolUrl}
          onChange={(_: any, val: string | undefined) => setToolUrl(val || '')}
          disabled={loading}
          styles={{
            root: { color: '#d0d0d0' },
            field: { 
              backgroundColor: '#2d2d2d',
              color: '#e0e0e0',
              borderColor: '#3d3d3d !important',
            },
            fieldGroup: { borderColor: '#3d3d3d' },
          }}
        />

        {/* Auth Type */}
        <Dropdown
          label="Authentication"
          selectedKey={authType}
          onChange={(_: any, option: any) => setAuthType(option?.key || 'none')}
          options={[
            { key: 'none', text: 'None' },
            { key: 'apikey', text: 'API Key' },
            { key: 'oauth', text: 'OAuth 2.0' },
          ]}
          disabled={loading}
          styles={{
            root: { color: '#d0d0d0' },
            label: { color: '#d0d0d0' },
            dropdown: {
              backgroundColor: '#2d2d2d',
              color: '#e0e0e0',
              borderColor: '#3d3d3d',
            },
            title: {
              backgroundColor: '#2d2d2d',
              color: '#e0e0e0',
              borderColor: '#3d3d3d',
            },
            dropdownItem: { color: '#e0e0e0' },
            dropdownItemSelected: { backgroundColor: '#0078d4', color: '#ffffff' },
          }}
        />

        {/* API Key Config */}
        {authType === 'apikey' && (
          <TextField
            label="API Key"
            type="password"
            placeholder="Your API key"
            value={apiKey}
            onChange={(_: any, val: string | undefined) => setApiKey(val || '')}
            disabled={loading}
            styles={{
              root: { color: '#d0d0d0' },
              field: { 
                backgroundColor: '#2d2d2d',
                color: '#e0e0e0',
                borderColor: '#3d3d3d !important',
              },
              fieldGroup: { borderColor: '#3d3d3d' },
            }}
          />
        )}

        {/* OAuth Config */}
        {authType === 'oauth' && (
          <Stack tokens={{ childrenGap: 12 }}>
            <TextField
              label="Client ID"
              placeholder="Your OAuth client ID"
              value={clientId}
              onChange={(_: any, val: string | undefined) => setClientId(val || '')}
              disabled={loading}
              styles={{
                root: { color: '#d0d0d0' },
                field: { 
                  backgroundColor: '#2d2d2d',
                  color: '#e0e0e0',
                  borderColor: '#3d3d3d !important',
                },
                fieldGroup: { borderColor: '#3d3d3d' },
              }}
            />
            <TextField
              label="Client Secret"
              type="password"
              placeholder="Your OAuth client secret"
              value={clientSecret}
              onChange={(_: any, val: string | undefined) => setClientSecret(val || '')}
              disabled={loading}
              styles={{
                root: { color: '#d0d0d0' },
                field: { 
                  backgroundColor: '#2d2d2d',
                  color: '#e0e0e0',
                  borderColor: '#3d3d3d !important',
                },
                fieldGroup: { borderColor: '#3d3d3d' },
              }}
            />
            <TextField
              label="Token URL"
              placeholder="https://login.microsoftonline.com/.../oauth2/v2.0/token"
              value={tokenUrl}
              onChange={(_: any, val: string | undefined) => setTokenUrl(val || '')}
              disabled={loading}
              styles={{
                root: { color: '#d0d0d0' },
                field: { 
                  backgroundColor: '#2d2d2d',
                  color: '#e0e0e0',
                  borderColor: '#3d3d3d !important',
                },
                fieldGroup: { borderColor: '#3d3d3d' },
              }}
            />
            <TextField
              label="Scope (optional)"
              placeholder="api://client-id/.default"
              value={scope}
              onChange={(_: any, val: string | undefined) => setScope(val || '')}
              disabled={loading}
              styles={{
                root: { color: '#d0d0d0' },
                field: { 
                  backgroundColor: '#2d2d2d',
                  color: '#e0e0e0',
                  borderColor: '#3d3d3d !important',
                },
                fieldGroup: { borderColor: '#3d3d3d' },
              }}
            />
          </Stack>
        )}

        {/* Buttons */}
        <Stack horizontal tokens={{ childrenGap: 12 }}>
          <DefaultButton
            onClick={handleSubmit}
            text="Register Tool"
            disabled={loading}
            styles={{
              root: {
                background: '#4a4a4a',
                color: '#ffffff',
                border: '1px solid #5a5a5a',
              },
              rootHovered: {
                background: '#5a5a5a',
                color: '#ffffff',
                border: '1px solid #6a6a6a',
              },
            }}
          />
          <DefaultButton
            onClick={onDismiss}
            text="Cancel"
            disabled={loading}
            styles={{
              root: {
                background: '#4a4a4a',
                color: '#ffffff',
                border: '1px solid #5a5a5a',
              },
              rootHovered: {
                background: '#5a5a5a',
                color: '#ffffff',
                border: '1px solid #6a6a6a',
              },
            }}
          />
        </Stack>

        {/* Info Text */}
        <Text
          variant="small"
          styles={{
            root: {
              color: '#d0d0d0',
              marginTop: 12,
              fontStyle: 'italic',
            },
          }}
        >
          Credentials are securely stored and used only for authenticating with the MCP server.
          Do not share credentials with others.
        </Text>
      </Stack>
    </Panel>
  );
};
