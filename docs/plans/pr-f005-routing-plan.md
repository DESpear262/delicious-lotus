# PR-F005: Routing and Layout Implementation Plan

## Overview
Set up React Router v6 with main layout structure, navigation menu, and core page routes for the application.

**Estimated Time:** 2 hours  
**Dependencies:** PR-F001 ✅, PR-F002 ✅  
**Priority:** HIGH - Blocks PR-F006, PR-F007, PR-F011

## Goals
- Configure React Router v6 with clean route structure
- Create responsive main layout with header and footer
- Build accessible navigation menu with mobile support
- Implement 404 error handling
- Establish consistent page structure across the app

---

## Files to Create

### 1. `/home/user/delicious-lotus/frontend/src/layouts/MainLayout.tsx`
**Purpose:** Main application layout wrapper with header, navigation, and footer

**Component Structure:**
```typescript
interface MainLayoutProps {
  children?: React.ReactNode;
}

export function MainLayout({ children }: MainLayoutProps): JSX.Element {
  // Layout structure with Outlet for nested routes
}
```

**Layout Elements:**
- **Header:**
  - Logo (top-left)
  - Navigation menu
  - User status/help link (if needed for future)
  - Height: 64px
  - Sticky on scroll
  
- **Main Content:**
  - `<Outlet />` for React Router
  - Max-width container (1200px)
  - Padding for content
  - Min-height: calc(100vh - header - footer)
  
- **Footer:**
  - Status indicators (connection, etc.)
  - Copyright info
  - Help/Support links
  - Height: 48px

**Styling:**
```css
.main-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.main-layout__header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  height: 64px;
}

.main-layout__content {
  flex: 1;
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  padding: var(--spacing-xl);
}

.main-layout__footer {
  background: var(--color-surface);
  border-top: 1px solid var(--color-border);
  height: 48px;
  padding: var(--spacing-md) var(--spacing-xl);
}
```

---

### 2. `/home/user/delicious-lotus/frontend/src/components/Navigation.tsx`
**Purpose:** Primary navigation menu component

**Component Structure:**
```typescript
interface NavigationProps {
  isMobile?: boolean;
  onClose?: () => void;
}

export function Navigation({ isMobile, onClose }: NavigationProps): JSX.Element {
  const location = useLocation();
  
  const navItems = [
    { path: '/', label: 'Home', icon: 'home' },
    { path: '/history', label: 'History', icon: 'history' },
  ];
  
  return (
    <nav className="navigation" role="navigation" aria-label="Main navigation">
      <ul className="navigation__list">
        {navItems.map(item => (
          <li key={item.path}>
            <NavLink
              to={item.path}
              className={({ isActive }) => 
                `navigation__link ${isActive ? 'navigation__link--active' : ''}`
              }
              onClick={isMobile ? onClose : undefined}
            >
              {item.label}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}
```

**Features:**
- NavLink for active route highlighting
- Keyboard navigation support (Tab, Enter)
- ARIA labels for accessibility
- Mobile-friendly (hamburger menu)
- Active route styling with CSS variable `--color-primary`

**Desktop Navigation:**
- Horizontal menu in header
- Always visible
- Hover effects

**Mobile Navigation:**
- Hamburger icon button (top-right)
- Slide-in drawer from right
- Overlay backdrop
- Close on route change
- Close button (X icon)
- Breakpoint: < 768px

**Styling:**
```css
.navigation__link {
  padding: var(--spacing-sm) var(--spacing-md);
  color: var(--color-text);
  text-decoration: none;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
}

.navigation__link:hover {
  color: var(--color-primary);
}

.navigation__link--active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
  font-weight: 600;
}

/* Mobile drawer */
@media (max-width: 767px) {
  .navigation {
    position: fixed;
    top: 0;
    right: -100%;
    width: 280px;
    height: 100vh;
    background: var(--color-surface);
    box-shadow: var(--shadow-xl);
    transition: right 0.3s ease;
    z-index: 1000;
  }
  
  .navigation--open {
    right: 0;
  }
}
```

---

### 3. `/home/user/delicious-lotus/frontend/src/components/MobileMenu.tsx`
**Purpose:** Mobile hamburger menu button and drawer

**Component Structure:**
```typescript
export function MobileMenu(): JSX.Element {
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();
  
  // Close menu on route change
  useEffect(() => {
    setIsOpen(false);
  }, [location.pathname]);
  
  // Prevent body scroll when menu is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);
  
  return (
    <>
      <button
        className="mobile-menu__button"
        onClick={() => setIsOpen(true)}
        aria-label="Open menu"
        aria-expanded={isOpen}
      >
        <MenuIcon />
      </button>
      
      {isOpen && (
        <>
          <div 
            className="mobile-menu__backdrop"
            onClick={() => setIsOpen(false)}
            role="presentation"
          />
          <div className="mobile-menu__drawer">
            <button
              className="mobile-menu__close"
              onClick={() => setIsOpen(false)}
              aria-label="Close menu"
            >
              <CloseIcon />
            </button>
            <Navigation isMobile onClose={() => setIsOpen(false)} />
          </div>
        </>
      )}
    </>
  );
}
```

**Features:**
- Hamburger icon (☰)
- Slide-in animation from right
- Backdrop overlay (semi-transparent black)
- Prevent body scroll when open
- Close on backdrop click
- Close on route change
- Close button in drawer
- Trap focus in drawer when open

---

### 4. `/home/user/delicious-lotus/frontend/src/components/Breadcrumbs.tsx`
**Purpose:** Breadcrumb navigation component

**Component Structure:**
```typescript
interface BreadcrumbItem {
  label: string;
  path?: string;
}

interface BreadcrumbsProps {
  items: BreadcrumbItem[];
}

export function Breadcrumbs({ items }: BreadcrumbsProps): JSX.Element {
  return (
    <nav className="breadcrumbs" aria-label="Breadcrumb">
      <ol className="breadcrumbs__list">
        {items.map((item, index) => (
          <li key={index} className="breadcrumbs__item">
            {item.path ? (
              <Link to={item.path} className="breadcrumbs__link">
                {item.label}
              </Link>
            ) : (
              <span className="breadcrumbs__current" aria-current="page">
                {item.label}
              </span>
            )}
            {index < items.length - 1 && (
              <span className="breadcrumbs__separator" aria-hidden="true">
                /
              </span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}
```

**Usage:**
```typescript
<Breadcrumbs items={[
  { label: 'Home', path: '/' },
  { label: 'History', path: '/history' },
  { label: 'Generation Details' }
]} />
```

---

### 5. `/home/user/delicious-lotus/frontend/src/pages/Home.tsx`
**Purpose:** Home/landing page (pipeline selection placeholder)

**Component Structure:**
```typescript
export function Home(): JSX.Element {
  return (
    <div className="home-page">
      <h1>AI Video Generation Pipeline</h1>
      <p>Welcome to the AI Video Generation Platform</p>
      <p className="home-page__note">
        Pipeline selection coming in PR-F006
      </p>
    </div>
  );
}
```

**Features:**
- Simple placeholder content
- Will be replaced/enhanced by PR-F006 (Pipeline Selection)
- Centered layout
- Hero section styling

---

### 6. `/home/user/delicious-lotus/frontend/src/pages/History.tsx`
**Purpose:** Generation history page (placeholder)

**Component Structure:**
```typescript
export function History(): JSX.Element {
  return (
    <div className="history-page">
      <h1>Generation History</h1>
      <p>Your video generation history will appear here.</p>
      <p className="history-page__note">
        Full history implementation coming in PR-F011
      </p>
    </div>
  );
}
```

**Features:**
- Placeholder for PR-F011
- Basic layout structure
- Empty state message

---

### 7. `/home/user/delicious-lotus/frontend/src/pages/NotFound.tsx`
**Purpose:** 404 error page

**Component Structure:**
```typescript
export function NotFound(): JSX.Element {
  const navigate = useNavigate();
  
  return (
    <div className="not-found-page">
      <div className="not-found-page__content">
        <h1 className="not-found-page__title">404</h1>
        <h2 className="not-found-page__subtitle">Page Not Found</h2>
        <p className="not-found-page__message">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <div className="not-found-page__actions">
          <Button
            variant="primary"
            onClick={() => navigate('/')}
          >
            Go Home
          </Button>
          <Button
            variant="secondary"
            onClick={() => navigate(-1)}
          >
            Go Back
          </Button>
        </div>
      </div>
    </div>
  );
}
```

**Features:**
- Large 404 text
- Helpful error message
- "Go Home" button
- "Go Back" button
- Centered layout
- Friendly, non-technical language

**Styling:**
```css
.not-found-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  text-align: center;
}

.not-found-page__title {
  font-size: 120px;
  font-weight: 700;
  color: var(--color-primary);
  margin: 0;
  line-height: 1;
}

.not-found-page__subtitle {
  font-size: 32px;
  margin: var(--spacing-md) 0;
}

.not-found-page__message {
  color: var(--color-text-secondary);
  margin: var(--spacing-md) 0 var(--spacing-xl);
}

.not-found-page__actions {
  display: flex;
  gap: var(--spacing-md);
  justify-content: center;
}
```

---

## Files to Modify

### 1. `/home/user/delicious-lotus/frontend/src/App.tsx`
**Changes:** Add React Router configuration

**New Structure:**
```typescript
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { MainLayout } from './layouts/MainLayout';
import { Home } from './pages/Home';
import { History } from './pages/History';
import { NotFound } from './pages/NotFound';

export function App(): JSX.Element {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Home />} />
          <Route path="history" element={<History />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
```

**Key Changes:**
- Wrap in `<BrowserRouter>`
- Define route structure
- Use MainLayout as parent route
- Add catch-all route for 404

---

## Dependencies

### NPM Packages
- `react-router-dom`: ^6.20.0 (already added in PR-F001)

### Internal Dependencies
- `/frontend/src/components/ui/Button.tsx` - Design system button
- `/frontend/src/styles/variables.css` - CSS variables
- `/frontend/src/styles/base.css` - Base styles

---

## API Integration

No direct API integration in this PR. Routes are prepared for future integration in:
- PR-F006: Pipeline Selection (Home page)
- PR-F007: Generation Form (new route)
- PR-F011: History Page (History page)

---

## Implementation Details

### Step 1: Create MainLayout (30 minutes)
1. Create `layouts/MainLayout.tsx`
2. Build header, content area, footer structure
3. Add sticky header behavior
4. Style with CSS modules or inline styles
5. Make responsive (mobile, tablet, desktop)
6. Add Outlet for nested routes

### Step 2: Build Navigation (30 minutes)
1. Create `components/Navigation.tsx`
2. Use NavLink for active route detection
3. Add keyboard navigation
4. Add ARIA labels
5. Style active states
6. Create mobile version

### Step 3: Create Mobile Menu (20 minutes)
1. Create `components/MobileMenu.tsx`
2. Build hamburger button
3. Create slide-in drawer
4. Add backdrop overlay
5. Handle open/close state
6. Prevent body scroll when open
7. Add animations

### Step 4: Build Breadcrumbs (15 minutes)
1. Create `components/Breadcrumbs.tsx`
2. Render breadcrumb trail
3. Add separators
4. Style current page
5. Add ARIA attributes

### Step 5: Create Pages (25 minutes)
1. Create `pages/Home.tsx` (placeholder)
2. Create `pages/History.tsx` (placeholder)
3. Create `pages/NotFound.tsx` (full implementation)
4. Style each page
5. Add proper headings and structure

### Step 6: Update App.tsx (10 minutes)
1. Import React Router components
2. Configure route structure
3. Set up MainLayout as parent
4. Add all routes
5. Test navigation

---

## State Management Approach

### Navigation State
- Mobile menu open/close: `useState<boolean>`
- Current location: `useLocation()` from React Router
- Navigation history: `useNavigate()` for programmatic navigation

### No Global State Needed
- Layout state is local to components
- Route state managed by React Router
- No complex state management required

---

## Error Handling Strategy

### Route Errors
1. **404 Not Found:**
   - Catch-all route (`path="*"`)
   - User-friendly error page
   - Navigation options to recover

2. **Navigation Errors:**
   - React Router handles invalid navigation
   - Fallback to 404 page

### Component Errors
1. **Render Errors:**
   - Will be handled by ErrorBoundary (PR-F014)
   - For now, errors bubble to console

---

## Accessibility Features

### Keyboard Navigation
- Tab through all interactive elements
- Enter/Space to activate links/buttons
- Escape to close mobile menu
- Focus visible indicators

### ARIA Attributes
- `role="navigation"` on nav elements
- `aria-label` for navigation regions
- `aria-current="page"` for active route
- `aria-expanded` for mobile menu state
- `aria-hidden` for decorative elements

### Screen Reader Support
- Semantic HTML (`<nav>`, `<main>`, `<header>`, `<footer>`)
- Skip to main content link (optional)
- Descriptive link text
- Breadcrumb navigation

### Focus Management
- Trap focus in mobile menu when open
- Return focus to trigger button on close
- Visible focus indicators
- Logical tab order

---

## Responsive Design

### Breakpoints
- Mobile: < 768px
- Tablet: 768px - 1023px
- Desktop: ≥ 1024px

### Mobile (< 768px)
- Hamburger menu instead of horizontal nav
- Single column layout
- Reduced padding
- Stacked buttons
- Full-width content

### Tablet (768px - 1023px)
- Horizontal navigation
- Two-column layout where appropriate
- Medium padding
- Max-width container

### Desktop (≥ 1024px)
- Full horizontal navigation
- Multi-column layouts
- Maximum width 1200px
- Optimal spacing

---

## Acceptance Criteria

- [ ] React Router v6 configured with routes:
  - [ ] `/` - Home/Pipeline Selection (placeholder)
  - [ ] `/history` - Generation history (placeholder)
  - [ ] `*` - 404 page (full implementation)
- [ ] MainLayout component with:
  - [ ] Header with logo and navigation
  - [ ] Main content area with `<Outlet>`
  - [ ] Footer with status/help
  - [ ] Sticky header on scroll
- [ ] Navigation menu with:
  - [ ] "Home" and "History" links
  - [ ] Active route highlighting (CSS variable `--color-primary`)
  - [ ] Responsive mobile menu (hamburger icon)
  - [ ] Slide-in drawer animation
- [ ] Breadcrumb navigation component (reusable)
- [ ] 404 page with:
  - [ ] Large "404" heading
  - [ ] Helpful message
  - [ ] "Go Home" button
  - [ ] "Go Back" button
- [ ] Keyboard navigation support:
  - [ ] Tab through all elements
  - [ ] Enter/Space to activate
  - [ ] Escape to close mobile menu
- [ ] ARIA labels for accessibility:
  - [ ] Navigation regions labeled
  - [ ] Active route indicated
  - [ ] Mobile menu state announced
- [ ] Mobile responsive:
  - [ ] Hamburger menu < 768px
  - [ ] Backdrop overlay
  - [ ] Slide-in animation
  - [ ] Body scroll prevention

---

## Testing Approach

### Component Tests
1. **MainLayout:**
   - Renders header, content, footer
   - Outlet renders child routes
   - Header is sticky

2. **Navigation:**
   - Links render correctly
   - Active route highlighted
   - Click navigates to route
   - Mobile menu opens/closes

3. **NotFound:**
   - Renders error message
   - "Go Home" navigates to /
   - "Go Back" uses history

### Integration Tests
1. **Routing:**
   - Navigate to / renders Home
   - Navigate to /history renders History
   - Navigate to invalid route renders NotFound
   - Browser back button works

2. **Mobile Menu:**
   - Hamburger button opens drawer
   - Backdrop click closes drawer
   - Route change closes drawer
   - Body scroll prevented when open

### Accessibility Tests
1. **Keyboard Navigation:**
   - Tab order is logical
   - All interactive elements reachable
   - Enter/Space activate links
   - Escape closes mobile menu

2. **Screen Reader:**
   - Navigation landmarks announced
   - Active route indicated
   - Links have descriptive text
   - Mobile menu state announced

### Manual Testing
1. **Navigation Flow:**
   - Click all navigation links
   - Verify active state updates
   - Test browser back/forward
   - Test direct URL entry

2. **Mobile Testing:**
   - Test on mobile device/emulator
   - Verify hamburger menu works
   - Test slide-in animation
   - Verify backdrop closes menu

3. **Browser Testing:**
   - Chrome, Firefox, Safari, Edge
   - Mobile browsers (iOS, Android)
   - Different viewport sizes

---

## Styling Approach

### CSS Modules
Use CSS modules for component-specific styles:
- `MainLayout.module.css`
- `Navigation.module.css`
- `MobileMenu.module.css`
- `Breadcrumbs.module.css`
- `NotFound.module.css`

### Design System
Use CSS variables from PR-F002:
- `--color-primary` - Active link color
- `--color-text` - Default text
- `--color-surface` - Header/footer background
- `--color-border` - Borders
- `--spacing-*` - Consistent spacing
- `--shadow-*` - Shadows
- `--transition-*` - Animations

### Transitions
- Navigation link hover: 0.2s
- Mobile drawer slide: 0.3s ease
- Backdrop fade: 0.3s

---

## Performance Considerations

1. **Code Splitting:**
   - Routes loaded on-demand (React.lazy)
   - Will be added in PR-F019 (Performance)

2. **Animations:**
   - Use CSS transforms (hardware accelerated)
   - Avoid layout thrashing
   - Use will-change for animations

3. **Mobile Menu:**
   - Prevent body scroll (not display: none)
   - Use transforms for slide animation
   - Remove from DOM when closed

---

## Security Considerations

None specific to this PR. Standard React/Router security:
- No dynamic route injection
- No user-generated links
- No XSS vulnerabilities

---

## Migration Notes

None - this is new functionality.

---

## Documentation

### Code Comments
- JSDoc for all components
- Explain complex accessibility features
- Document prop types

### Usage Examples
```typescript
// Basic usage
import { MainLayout } from './layouts/MainLayout';
import { Outlet } from 'react-router-dom';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Home />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

// Breadcrumbs usage
<Breadcrumbs items={[
  { label: 'Home', path: '/' },
  { label: 'Current Page' }
]} />
```

---

## Follow-up Tasks

1. **PR-F006:** Implement Pipeline Selection on Home page
2. **PR-F007:** Add generation form route
3. **PR-F011:** Implement full History page
4. **PR-F015:** Mobile responsive enhancements
5. **Future:** Add user authentication routes

---

## Success Criteria

This PR is successful when:
1. All routes render correctly
2. Navigation works on desktop and mobile
3. Active route highlighting works
4. Mobile menu slides in/out smoothly
5. 404 page displays for invalid routes
6. Keyboard navigation works throughout
7. ARIA labels are present and correct
8. Code passes TypeScript strict mode
9. All acceptance criteria met
10. Manual testing passes on all browsers
