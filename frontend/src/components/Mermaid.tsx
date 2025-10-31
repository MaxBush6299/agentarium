import React, { useEffect, useRef } from 'react';
import mermaid from 'mermaid';
import { makeStyles } from '@fluentui/react-components';

const useStyles = makeStyles({
  mermaidContainer: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: '24px',
    marginBottom: '24px',
    overflow: 'auto',
    backgroundColor: '#f5f5f5',
    padding: '24px',
    borderRadius: '8px',
  },
});

interface MermaidProps {
  chart: string;
}

// Initialize mermaid once
mermaid.initialize({
  startOnLoad: false,
  theme: 'default',
  securityLevel: 'loose',
  fontFamily: 'Segoe UI, sans-serif',
});

export const Mermaid: React.FC<MermaidProps> = ({ chart }) => {
  const styles = useStyles();
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const renderChart = async () => {
      if (containerRef.current) {
        try {
          const { svg } = await mermaid.render(`mermaid-${Date.now()}`, chart);
          containerRef.current.innerHTML = svg;
        } catch (error) {
          console.error('Mermaid rendering error:', error);
          containerRef.current.innerHTML = `<pre>${chart}</pre>`;
        }
      }
    };

    renderChart();
  }, [chart]);

  return (
    <div 
      ref={containerRef} 
      className={styles.mermaidContainer}
    />
  );
};
