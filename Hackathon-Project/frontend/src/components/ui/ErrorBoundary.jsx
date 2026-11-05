import { Component } from 'react';
import { EmptyState } from './EmptyState.jsx';
import { Button } from './Button.jsx';

/** Catches render errors in a subtree. Pass `resetKey` (e.g. the route) to recover on navigation. */
export class ErrorBoundary extends Component {
  state = { error: null, showDetails: false };

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught error:', error, errorInfo);
  }

  componentDidUpdate(prev) {
    if (this.state.error && prev.resetKey !== this.props.resetKey) {
      this.setState({ error: null, showDetails: false });
    }
  }

  render() {
    if (!this.state.error) return this.props.children;
    const msg = this.state.error?.message || "An unexpected view error occurred while rendering this module.";
    return (
      <div style={{ padding: '32px 16px', display: 'flex', justifyContent: 'center' }}>
        <EmptyState
          tone="danger"
          icon="alert"
          title="This screen hit a snag"
          description={msg}
          action={
            <div className="stack" style={{ '--gap': '12px', alignItems: 'center' }}>
              <div className="row" style={{ gap: '8px' }}>
                <Button variant="secondary" icon="refresh" onClick={() => this.setState({ error: null })}>
                  Reload view
                </Button>
                <Button variant="ghost" onClick={() => window.location.reload()}>
                  Refresh page
                </Button>
                {this.state.error?.stack ? (
                  <Button
                    variant="ghost"
                    size="xs"
                    onClick={() => this.setState((s) => ({ showDetails: !s.showDetails }))}
                  >
                    {this.state.showDetails ? 'Hide technical details' : 'Show details'}
                  </Button>
                ) : null}
              </div>
              {this.state.showDetails && this.state.error?.stack ? (
                <pre className="code-block">
                  {this.state.error.stack}
                </pre>
              ) : null}
            </div>
          }
        />
      </div>
    );
  }
}
