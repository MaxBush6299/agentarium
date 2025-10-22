import React, { useState, useEffect } from 'react';
import { Dropdown, IDropdownOption, Stack, Text, Spinner, SpinnerSize } from '@fluentui/react';

interface ModelDeployment {
  deployment_name: string;
  model_id: string;
  description?: string;
  capabilities: string[];
  context_window?: number;
}

interface ModelListResponse {
  models: ModelDeployment[];
  total: number;
  endpoint: string;
  api_version: string;
}

interface ModelSelectorProps {
  value?: string;
  onChange?: (deploymentName: string) => void;
  label?: string;
  required?: boolean;
}

export const ModelSelector: React.FC<ModelSelectorProps> = ({
  value,
  onChange,
  label = 'Model',
  required = true,
}) => {
  const [models, setModels] = useState<ModelDeployment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedKey, setSelectedKey] = useState<string | undefined>(value);

  useEffect(() => {
    const fetchModels = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/models');
        
        if (!response.ok) {
          throw new Error(`Failed to fetch models: ${response.statusText}`);
        }
        
        const data: ModelListResponse = await response.json();
        setModels(data.models);
        setError(null);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to load models';
        setError(errorMessage);
        console.error('Error fetching models:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchModels();
  }, []);

  const dropdownOptions: IDropdownOption[] = models.map((model) => ({
    key: model.deployment_name,
    text: `${model.deployment_name} (${model.model_id})`,
    data: model,
    title: model.description || `${model.model_id} deployment`,
  }));

  const handleChange = (
    _event: React.FormEvent<HTMLDivElement>,
    option?: IDropdownOption
  ) => {
    if (option) {
      setSelectedKey(option.key as string);
      onChange?.(option.key as string);
    }
  };

  if (error) {
    return (
      <Stack tokens={{ childrenGap: 8 }}>
        <Text variant="medium" styles={{ root: { color: '#d0d0d0' } }}>
          {label}{required && ' *'}
        </Text>
        <Text variant="small" styles={{ root: { color: '#ff6b6b' } }}>
          ⚠️ {error}
        </Text>
      </Stack>
    );
  }

  if (loading) {
    return (
      <Stack tokens={{ childrenGap: 8 }}>
        <Text variant="medium" styles={{ root: { color: '#d0d0d0' } }}>
          {label}{required && ' *'}
        </Text>
        <Spinner size={SpinnerSize.small} label="Loading models..." />
      </Stack>
    );
  }

  return (
    <Stack tokens={{ childrenGap: 8 }}>
      <Dropdown
        label={`${label}${required ? ' *' : ''}`}
        selectedKey={selectedKey}
        onChange={handleChange}
        options={dropdownOptions}
        styles={{
          root: {
            width: '100%',
          },
          label: {
            color: '#d0d0d0',
            fontWeight: 600,
          },
          dropdown: {
            backgroundColor: '#2d2d2d',
            borderColor: '#3d3d3d',
            color: '#d0d0d0',
          },
          dropdownItem: {
            backgroundColor: '#2d2d2d',
            color: '#d0d0d0',
            selectors: {
              '&:hover': {
                backgroundColor: '#3d3d3d',
              },
            },
          },
          dropdownItemSelected: {
            backgroundColor: '#0078d4',
            color: '#ffffff',
          },
          callout: {
            backgroundColor: '#2d2d2d',
            borderColor: '#3d3d3d',
          },
          title: {
            color: '#d0d0d0',
            backgroundColor: '#2d2d2d',
          },
        }}
        placeholder={models.length === 0 ? 'No models available' : 'Select a model'}
      />
      {selectedKey && models.length > 0 && (
        <Text
          variant="small"
          styles={{
            root: {
              color: '#a0a0a0',
              fontSize: '12px',
              marginTop: '-8px',
            },
          }}
        >
          {models.find((m) => m.deployment_name === selectedKey)?.description}
        </Text>
      )}
    </Stack>
  );
};

export default ModelSelector;
