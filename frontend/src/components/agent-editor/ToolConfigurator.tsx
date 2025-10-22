import React, { useMemo } from 'react';
import { Stack, Text, Checkbox, Panel, DefaultButton } from '@fluentui/react';
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

  // Create a set of selected tool keys for quick lookup
  const selectedToolKeys = useMemo(() => {
    return new Set(selectedTools.map(t => `${t.type}:${t.name}`));
  }, [selectedTools]);

  // Handle tool toggle
  const handleToolToggle = (tool: ToolItem) => {
    const toolKey = `${tool.type}:${tool.name}`;
    const isSelected = selectedToolKeys.has(toolKey);

    if (isSelected) {
      // Remove tool (but prevent removing if it's the last one)
      if (selectedTools.length > 1) {
        onChange(selectedTools.filter(t => `${t.type}:${t.name}` !== toolKey));
      }
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
                  padding: '12px',
                  borderRadius: 4,
                  backgroundColor: isSelected ? '#bdb9b9ff' : '#868585ff',
                  border: isSelected ? '1px solid #0078d4' : '1px solid #e1e1e1',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                }}
                onClick={() => handleToolToggle(tool)}
              >
                <Checkbox
                  label={tool.label}
                  checked={isSelected}
                  onChange={() => handleToolToggle(tool)}
                  onClick={(e: React.MouseEvent) => e.stopPropagation()}
                  styles={{
                    root: { margin: 0 },
                    label: { color: '#ffffffff'}
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
      {renderToolCategory('MCP', TOOL_CATEGORIES.MCP.tools)}
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
          <Text variant="small" styles={{ root: { color: '#333' } }}>
            <strong>{selectedTools.length} tool(s) selected:</strong>{' '}
            {selectedTools.map(t => t.name).join(', ')}
          </Text>
        </div>
      )}

      {/* Add Custom MCP Tool Panel */}
      <AddCustomToolPanel
        toolType={showAddCustom}
        onDismiss={() => setShowAddCustom(null)}
      />
    </Stack>
  );
};

/**
 * Panel for adding custom MCP/OpenAPI tools
 * (Implementation deferred to Phase 3.6)
 */
interface AddCustomToolPanelProps {
  toolType: 'mcp' | 'openapi' | 'a2a' | null;
  onDismiss: () => void;
}

const AddCustomToolPanel: React.FC<AddCustomToolPanelProps> = ({
  toolType,
  onDismiss,
}) => {
  const panelTitle = {
    mcp: 'Add Custom MCP Server',
    openapi: 'Add Custom OpenAPI API',
    a2a: 'Add Custom A2A Agent',
  }[toolType || 'mcp'];

  return (
    <Panel
      isOpen={toolType !== null}
      onDismiss={onDismiss}
      headerText={panelTitle}
      closeButtonAriaLabel="Close"
    >
      <Stack tokens={{ childrenGap: 16 }} styles={{ root: { marginTop: 16 } }}>
        <Text variant="small" styles={{ root: { color: '#666' } }}>
          Custom tools configuration coming in Phase 3.6. For now, please use pre-configured tools above.
        </Text>

        <Stack horizontal tokens={{ childrenGap: 12 }}>
          <DefaultButton
            onClick={onDismiss}
            text="Close"
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
      </Stack>
    </Panel>
  );
};
