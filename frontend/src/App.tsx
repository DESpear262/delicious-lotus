import { useState } from 'react';
import { Button, Input, Card, CardHeader, CardBody, CardFooter, Spinner } from './components/ui';

function App() {
  const [loading, setLoading] = useState(false);

  return (
    <div className="container container-lg" style={{ padding: '2rem 1rem' }}>
      <h1>AI Video Generation Pipeline - Design System</h1>
      <p style={{ color: 'var(--color-text-secondary)', marginBottom: '2rem' }}>
        Design system foundation with base UI components
      </p>

      <div className="grid grid-cols-1 tablet:grid-cols-2" style={{ gap: '2rem' }}>
        {/* Buttons */}
        <Card variant="elevated">
          <CardHeader title="Buttons" subtitle="Primary, secondary, outline, ghost, and danger variants" />
          <CardBody>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                <Button variant="primary">Primary</Button>
                <Button variant="secondary">Secondary</Button>
                <Button variant="outline">Outline</Button>
                <Button variant="ghost">Ghost</Button>
                <Button variant="danger">Danger</Button>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
                <Button size="sm">Small</Button>
                <Button size="md">Medium</Button>
                <Button size="lg">Large</Button>
              </div>
              <Button
                variant="primary"
                loading={loading}
                onClick={() => {
                  setLoading(true);
                  setTimeout(() => setLoading(false), 2000);
                }}
              >
                {loading ? 'Loading...' : 'Click to Load'}
              </Button>
            </div>
          </CardBody>
        </Card>

        {/* Inputs */}
        <Card variant="elevated">
          <CardHeader title="Inputs" subtitle="Text inputs with validation states" />
          <CardBody>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <Input label="Default Input" placeholder="Enter text..." />
              <Input
                label="With Helper Text"
                placeholder="Enter email..."
                helperText="We'll never share your email"
              />
              <Input
                label="Error State"
                placeholder="Enter password..."
                error="Password is required"
              />
              <Input
                label="Success State"
                placeholder="Username"
                success="Username is available"
              />
              <Input label="Disabled Input" placeholder="Disabled" disabled />
            </div>
          </CardBody>
        </Card>

        {/* Spinners */}
        <Card variant="elevated">
          <CardHeader title="Spinners" subtitle="Loading indicators" />
          <CardBody>
            <div style={{ display: 'flex', gap: '2rem', alignItems: 'center', flexWrap: 'wrap' }}>
              <div>
                <p style={{ fontSize: '0.875rem', marginBottom: '0.5rem' }}>Sizes:</p>
                <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                  <Spinner size="sm" />
                  <Spinner size="md" />
                  <Spinner size="lg" />
                  <Spinner size="xl" />
                </div>
              </div>
              <div>
                <p style={{ fontSize: '0.875rem', marginBottom: '0.5rem' }}>Variants:</p>
                <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                  <Spinner variant="primary" />
                  <Spinner variant="secondary" />
                </div>
              </div>
            </div>
          </CardBody>
        </Card>

        {/* Cards */}
        <Card variant="elevated">
          <CardHeader title="Cards" subtitle="Different card variants and layouts" />
          <CardBody>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <Card variant="default" padding="sm">
                <p style={{ margin: 0 }}>Default Card (small padding)</p>
              </Card>
              <Card variant="bordered" padding="md">
                <p style={{ margin: 0 }}>Bordered Card (medium padding)</p>
              </Card>
              <Card variant="elevated" padding="lg" hoverable>
                <p style={{ margin: 0 }}>Elevated Hoverable Card (large padding)</p>
              </Card>
            </div>
          </CardBody>
        </Card>
      </div>

      {/* Full Width Examples */}
      <Card variant="elevated" style={{ marginTop: '2rem' }}>
        <CardHeader
          title="Full Example Card"
          subtitle="Card with header, body, and footer"
          actions={<Button variant="ghost" size="sm">Action</Button>}
        />
        <CardBody>
          <p>
            This is an example of a complete card with all sections. The design system uses
            CSS Variables for consistent theming and CSS Modules for component-specific styles.
          </p>
          <p style={{ marginBottom: 0 }}>
            All components are built with accessibility in mind, including proper ARIA labels,
            focus states, and keyboard navigation support.
          </p>
        </CardBody>
        <CardFooter>
          <Button variant="outline">Cancel</Button>
          <Button variant="primary">Save Changes</Button>
        </CardFooter>
      </Card>
    </div>
  );
}

export default App;
