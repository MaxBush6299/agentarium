import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Stack,
  Text,
  TextField,
  DefaultButton,
  Spinner,
  MessageBar,
  MessageBarType,
  Dropdown,
  IDropdownOption,
} from '@fluentui/react';
import { PromptEditor } from '../../components/agent-editor/PromptEditor';
import { ToolConfigurator } from '../../components/agent-editor/ToolConfigurator';
import { ModelSelector } from '../../components/agent-editor/ModelSelector';
import { CapabilitiesEditor } from '../../components/agents/CapabilitiesEditor';
import { ToolData } from './agentSchema';
import '../../styles/agent-editor.css';

interface AgentForm {
  id: string;
  name: string;
  description: string;
  system_prompt: string;
  model: string;
  temperature: number;
  max_tokens: number;
  max_messages: number;
  status: 'active' | 'inactive' | 'maintenance';
  capabilities: string[];
  tools: ToolData[];
}

interface FormErrors {
  [key: string]: string | undefined;
}

/**
 * AgentEditorPage
 * 
 * Full-page agent configuration editor with the following sections:
 * 1. Basic Info (name, description, status)
 * 2. Model Selection
 * 3. System Prompt (using PromptEditor)
 * 4. Tools (using ToolConfigurator)
 * 5. Advanced Settings (temperature, max_tokens, max_messages)
 * 
 * Features:
 * - Load existing agent from Cosmos DB
 * - Real-time form validation
 * - Save changes via PUT endpoint
 * - Navigate back to agents directory on success
 */

export const AgentEditorPage: React.FC = () => {
  const navigate = useNavigate();
  const { agentId } = useParams<{ agentId: string }>();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [formData, setFormData] = useState<AgentForm>({
    id: agentId || '',
    name: '',
    description: '',
    system_prompt: '',
    model: 'gpt-4o',
    temperature: 0.7,
    max_tokens: 4000,
    max_messages: 20,
    status: 'active',
    capabilities: [],
    tools: [],
  });
  const [formErrors, setFormErrors] = useState<FormErrors>({});

  // Load agent from API (only for edit mode)
  useEffect(() => {
    const loadAgent = async () => {
      if (!agentId) {
        // Creating new agent - no need to load
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const response = await fetch(`/api/agents/${agentId}`);

        if (!response.ok) {
          throw new Error(`Failed to load agent: ${response.statusText}`);
        }

        const agent = await response.json();

        // Populate form with agent data
        setFormData({
          id: agent.id,
          name: agent.name,
          description: agent.description,
          system_prompt: agent.system_prompt,
          model: agent.model,
          temperature: agent.temperature ?? 0.7,
          max_tokens: agent.max_tokens ?? 4000,
          max_messages: agent.max_messages ?? 20,
          status: agent.status,
          tools: agent.tools || [],
          capabilities: agent.capabilities || [],
        });

        setError(null);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Unknown error loading agent';
        setError(errorMessage);
        console.error('Error loading agent:', err);
      } finally {
        setLoading(false);
      }
    };

    loadAgent();
  }, [agentId]);

  // Validate form
  const validateForm = (): boolean => {
    const errors: FormErrors = {};

    if (!formData.name || formData.name.length < 3) {
      errors.name = 'Name must be at least 3 characters';
    }
    if (!formData.description || formData.description.length < 10) {
      errors.description = 'Description must be at least 10 characters';
    }
    if (!formData.system_prompt || formData.system_prompt.length < 50) {
      errors.system_prompt = 'System prompt must be at least 50 characters';
    }
    if (formData.system_prompt.length > 4000) {
      errors.system_prompt = 'System prompt must be less than 4000 characters';
    }
    if (!formData.model) {
      errors.model = 'Model selection is required';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Handle form submission
  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }

    try {
      setSaving(true);
      setError(null);

      const isCreating = !agentId;
      const url = isCreating ? '/api/agents' : `/api/agents/${agentId}`;
      const method = isCreating ? 'POST' : 'PUT';

      const payload = {
        name: formData.name,
        description: formData.description,
        system_prompt: formData.system_prompt,
        model: formData.model,
        temperature: formData.temperature,
        max_tokens: formData.max_tokens,
        max_messages: formData.max_messages,
        status: formData.status,
        tools: formData.tools,
        capabilities: formData.capabilities,
      };

      // Add ID for POST requests (creating new agent)
      if (isCreating) {
        (payload as any).id = `agent-${Date.now()}`;
      }

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to save agent: ${response.statusText}`);
      }

      setSuccess(true);

      // Redirect after 2 seconds
      setTimeout(() => {
        navigate('/agents');
      }, 2000);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error saving agent';
      setError(errorMessage);
      console.error('Error saving agent:', err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Stack
        tokens={{ childrenGap: 20 }}
        styles={{
          root: {
            padding: 40,
            maxWidth: 1200,
            margin: '0 auto',
          },
        }}
      >
        <Spinner label="Loading agent configuration..." />
      </Stack>
    );
  }

  return (
    <div style={{ 
      background: 'linear-gradient(135deg, #1a1a1a 0%, #1f1f1f 100%)',
      height: '100vh',
      width: '100%',
      overflowY: 'auto',
      overflowX: 'hidden',
      display: 'flex',
      flexDirection: 'column',
    }}>
      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
        <Stack
          tokens={{ childrenGap: 24 }}
          styles={{
            root: {
              maxWidth: 1000,
              margin: '0 auto',
              width: '100%',
              padding: '40px 20px',
              flex: 1,
            },
          }}
        >
          {/* Header */}
          <div style={{ borderBottom: '2px solid #3a3a3a', paddingBottom: 24, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 16 }}>
            <DefaultButton
              onClick={() => navigate('/agents')}
              text="← Back"
              styles={{
                root: {
                  minWidth: 'auto',
                  padding: '8px 16px',
                  height: '32px',
                  fontSize: '13px',
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
            <div style={{ flex: 1, textAlign: 'center' }}>
              <Text variant="medium" styles={{ root: { fontWeight: 600, color: '#ffffff', fontSize: '18px' } }}>
                {agentId ? 'Edit Agent' : 'Create New Agent'}
              </Text>
              <Text variant="medium" styles={{ root: { color: '#b4b4b4', marginTop: 4 } }}>
                {formData.name || 'Agent Configuration'}
              </Text>
            </div>
            <div style={{ width: '120px' }} />
          </div>

        {/* Success Message */}
        {success && (
          <MessageBar messageBarType={MessageBarType.success} styles={{ root: { borderRadius: 6 } }}>
            Agent configuration saved successfully. Redirecting to agents directory...
          </MessageBar>
        )}

        {/* Error Message */}
        {error && (
          <MessageBar
            messageBarType={MessageBarType.error}
            onDismiss={() => setError(null)}
            styles={{ root: { borderRadius: 6 } }}
          >
            {error}
          </MessageBar>
        )}

        {/* Form */}
        <Stack tokens={{ childrenGap: 24 }}>
          {/* ===== SECTION 1: BASIC INFO ===== */}
          <div style={{
            background: '#252525',
            borderRadius: 8,
            padding: 24,
            boxShadow: '0 2px 8px rgba(0, 0, 0, 0.4)',
            border: '1px solid #3a3a3a',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 20 }}>
              <div style={{
                width: 4,
                height: 20,
                background: 'linear-gradient(135deg, #0078d4 0%, #50e6ff 100%)',
                borderRadius: 2,
              }} />
              <Text styles={{ root: { fontWeight: 600, color: '#ffffff', fontSize: 16 } }}>
                Basic Information
              </Text>
            </div>

            <Stack tokens={{ childrenGap: 16 }}>
              <TextField
                label="Agent Name"
                value={formData.name}
                onChange={(_: any, val: string | undefined) => setFormData({ ...formData, name: val || '' })}
                errorMessage={formErrors.name}
                placeholder="e.g., Support Triage Agent"
              />

              <TextField
                label="Description"
                value={formData.description}
                onChange={(_: any, val: string | undefined) => setFormData({ ...formData, description: val || '' })}
                multiline
                rows={3}
                errorMessage={formErrors.description}
                placeholder="What does this agent do?"
              />

              <Dropdown
                label="Status"
                selectedKey={formData.status}
                onChange={(_: any, option: IDropdownOption | undefined) => {
                  if (option) {
                    setFormData({
                      ...formData,
                      status: option.key as 'active' | 'inactive' | 'maintenance',
                    });
                  }
                }}
                options={[
                  { key: 'active', text: 'Active' },
                  { key: 'inactive', text: 'Inactive' },
                  { key: 'maintenance', text: 'Maintenance' },
                ]}
              />
            </Stack>
          </div>

          {/* ===== SECTION 2: MODEL SELECTION ===== */}
          <div style={{
            background: '#252525',
            borderRadius: 8,
            padding: 24,
            boxShadow: '0 2px 8px rgba(0, 0, 0, 0.4)',
            border: '1px solid #3a3a3a',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 20 }}>
              <div style={{
                width: 4,
                height: 20,
                background: 'linear-gradient(135deg, #0078d4 0%, #50e6ff 100%)',
                borderRadius: 2,
              }} />
              <Text styles={{ root: { fontWeight: 600, color: '#ffffff', fontSize: 16 } }}>
                Model Configuration
              </Text>
            </div>

            <Stack tokens={{ childrenGap: 16 }}>
              <ModelSelector
                value={formData.model}
                onChange={(deploymentName) =>
                  setFormData({ ...formData, model: deploymentName })
                }
                label="LLM Model"
                required={true}
              />

              <Stack horizontal tokens={{ childrenGap: 16 }}>
                <div style={{ flex: 1 }}>
                  <TextField
                    label="Temperature"
                    type="number"
                    value={String(formData.temperature)}
                    onChange={(_: any, val: string | undefined) =>
                      setFormData({
                        ...formData,
                        temperature: val ? parseFloat(val) : 0.7,
                      })
                    }
                    step={0.1}
                    min={0}
                    max={2}
                    description="0 = deterministic, 2 = creative"
                  />
                </div>

                <div style={{ flex: 1 }}>
                  <TextField
                    label="Max Tokens"
                    type="number"
                    value={String(formData.max_tokens)}
                    onChange={(_: any, val: string | undefined) =>
                      setFormData({
                        ...formData,
                        max_tokens: val ? parseInt(val, 10) : 4000,
                      })
                    }
                    step={100}
                    min={100}
                    max={8000}
                    errorMessage={formErrors.max_tokens}
                  />
                </div>

                <div style={{ flex: 1 }}>
                  <TextField
                    label="Max Messages in Memory"
                    type="number"
                    value={String(formData.max_messages)}
                    onChange={(_: any, val: string | undefined) =>
                      setFormData({
                        ...formData,
                        max_messages: val ? parseInt(val, 10) : 20,
                      })
                    }
                    step={5}
                    min={5}
                    max={100}
                    errorMessage={formErrors.max_messages}
                  />
                </div>
              </Stack>
            </Stack>
          </div>

          {/* ===== SECTION 3: SYSTEM PROMPT ===== */}
          <div style={{
            background: '#252525',
            borderRadius: 8,
            padding: 24,
            boxShadow: '0 2px 8px rgba(0, 0, 0, 0.4)',
            border: '1px solid #3a3a3a',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 20 }}>
              <div style={{
                width: 4,
                height: 20,
                background: 'linear-gradient(135deg, #0078d4 0%, #50e6ff 100%)',
                borderRadius: 2,
              }} />
              <Text styles={{ root: { fontWeight: 600, color: '#ffffff', fontSize: 16 } }}>
                System Prompt
              </Text>
            </div>
            <PromptEditor
              value={formData.system_prompt}
              onChange={(newValue) =>
                setFormData({ ...formData, system_prompt: newValue })
              }
              error={formErrors.system_prompt}
            />
          </div>

          {/* ===== SECTION 4: TOOLS ===== */}
          <div style={{
            background: '#252525',
            borderRadius: 8,
            padding: 24,
            boxShadow: '0 2px 8px rgba(0, 0, 0, 0.4)',
            border: '1px solid #3a3a3a',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 20 }}>
              <div style={{
                width: 4,
                height: 20,
                background: 'linear-gradient(135deg, #0078d4 0%, #50e6ff 100%)',
                borderRadius: 2,
              }} />
              <Text styles={{ root: { fontWeight: 600, color: '#ffffff', fontSize: 16 } }}>
                Tools
              </Text>
            </div>
            <ToolConfigurator
              selectedTools={formData.tools}
              onChange={(newTools) => setFormData({ ...formData, tools: newTools })}
              error={formErrors.tools}
            />
          </div>

          {/* ===== CAPABILITIES ===== */}
          <div style={{
            padding: '24px',
            background: '#2a2a2a',
            borderRadius: '8px',
            border: '1px solid #3a3a3a',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: 16 }}>
              <div style={{
                width: 4,
                height: 20,
                background: 'linear-gradient(135deg, #50e6ff 0%, #0078d4 100%)',
                borderRadius: 2,
                marginRight: 12,
              }} />
              <Text styles={{ root: { fontWeight: 600, color: '#ffffff', fontSize: 16 } }}>
                Capabilities
              </Text>
            </div>
            <CapabilitiesEditor
              capabilities={formData.capabilities}
              onChange={(newCapabilities) => setFormData({ ...formData, capabilities: newCapabilities })}
              label="Agent Capabilities"
              placeholder="e.g., document_retrieval, issue_triage"
              helpText="Define capabilities to describe what this agent can do. These are used for discovery and filtering by other agents."
            />
          </div>

          {/* ===== BUTTONS ===== */}
          <Stack horizontal tokens={{ childrenGap: 12 }} styles={{ root: { paddingTop: 24, borderTop: '1px solid #3a3a3a' } }}>
            <DefaultButton
              onClick={handleSubmit}
              text="Save Changes"
              disabled={saving}
              styles={{
                root: {
                  minWidth: 120,
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
              onClick={() => navigate('/agents')}
              text="Cancel"
              disabled={saving}
              styles={{
                root: {
                  minWidth: 120,
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
            {saving && <Spinner styles={{ root: { marginLeft: 12 } }} />}
          </Stack>
        </Stack>
        </Stack>
      </div>
    </div>
  );
};
