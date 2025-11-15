import { Outlet, Link } from 'react-router-dom';
import { Navigation } from '../components/Navigation';
import { MobileMenu } from '../components/MobileMenu';
import styles from './MainLayout.module.css';

/**
 * MainLayout Component
 *
 * Main application layout wrapper with header, navigation, and footer.
 * Uses React Router's Outlet to render nested routes.
 */
export function MainLayout() {
  return (
    <div className={styles.mainLayout}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerContent}>
          {/* Logo */}
          <Link to="/" className={styles.logo}>
            <h1 className={styles.logoText}>AI Video Gen</h1>
          </Link>

          {/* Desktop Navigation */}
          <div className={styles.desktopNav}>
            <Navigation />
          </div>

          {/* Mobile Menu Button */}
          <div className={styles.mobileNav}>
            <MobileMenu />
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className={styles.content}>
        <Outlet />
      </main>

      {/* Footer */}
      <footer className={styles.footer}>
        <div className={styles.footerContent}>
          <div className={styles.footerStatus}>
            <span className={styles.statusIndicator}>
              <span className={styles.statusDot}></span>
              System Online
            </span>
          </div>
          <div className={styles.footerInfo}>
            <span>&copy; 2025 AI Video Generation Platform</span>
            <span className={styles.separator}>•</span>
            <a href="#help" className={styles.footerLink}>Help</a>
            <span className={styles.separator}>•</span>
            <a href="#support" className={styles.footerLink}>Support</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
