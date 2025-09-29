import { Component } from 'react';
import { Alert, Box, Text } from '@mantine/core';

export class ErrorBoundary extends Component {
  constructor(props){ super(props); this.state = { hasError: false, error: null }; }
  static getDerivedStateFromError(error){ return { hasError: true, error }; }
  componentDidCatch(error, info){ window.__APP_ERROR__ = { error: String(error), info: String(info && info.componentStack) }; }
  render(){
    if (this.state.hasError){
      const details = window.__APP_ERROR__?.error || String(this.state.error || 'Unknown error');
      return (
        <Box p="md">
          <Alert color="red" title="Ошибка UI">
            <Text size="sm" style={{ wordBreak: 'break-all' }}>{details}</Text>
          </Alert>
        </Box>
      );
    }
    return this.props.children;
  }
}
