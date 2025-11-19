import { Outlet, Link } from 'react-router-dom';
import { ROUTES } from '../types/routes';
import { Navigation } from '../components/ad-generator/Navigation';
import { MobileMenu } from '../components/ad-generator/MobileMenu';

/**
 * MainLayout Component
 *
 * Main application layout wrapper with header, navigation, and footer.
 * Uses React Router's Outlet to render nested routes.
 */
export function AdGeneratorLayout() {
  return (
    <div className="flex flex-col h-screen overflow-hidden bg-background text-foreground">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-background/90 backdrop-blur-sm border-b border-border h-16 relative shrink-0">
        <div className="absolute bottom-0 left-0 right-0 h-[1px] bg-gradient-to-r from-blue-500/50 to-purple-500/50 opacity-50" />
        <div className="max-w-7xl w-full h-full mx-auto px-4 md:px-6 flex items-center justify-between">
          {/* Logo */}
          <Link to={ROUTES.AD_GENERATOR} className="flex items-center no-underline text-foreground hover:text-primary transition-colors group">
            <h1 className="text-xl font-bold tracking-wide group-hover:text-shadow-glow">Delicious Lotus</h1>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:block">
            <Navigation />
          </div>

          {/* Mobile Menu Button */}
          <div className="md:hidden">
            <MobileMenu />
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 w-full mx-auto overflow-y-auto scroll-smooth">
        <div className="max-w-7xl mx-auto p-4 md:p-6 relative z-10">
          <Outlet />
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-background/90 backdrop-blur-sm border-t border-border py-4 px-4 md:px-6 relative shrink-0">
        <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-blue-500/50 to-purple-500/50 opacity-50" />
        <div className="max-w-7xl w-full mx-auto flex flex-col md:flex-row gap-2 items-center justify-between text-sm text-muted-foreground">
          <div className="flex items-center">
            <span className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(67,255,201,0.6)] animate-pulse"></span>
              System Online
            </span>
          </div>
          <div className="flex items-center gap-2 flex-wrap justify-center">
            <span>&copy; 2025 Delicious Lotus</span>
            <span className="text-border">•</span>
            <a href="#help" className="text-muted-foreground hover:text-primary transition-colors">Help</a>
            <span className="text-border">•</span>
            <a href="#support" className="text-muted-foreground hover:text-primary transition-colors">Support</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
